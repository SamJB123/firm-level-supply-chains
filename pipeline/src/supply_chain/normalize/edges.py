from __future__ import annotations

import hashlib
from collections import defaultdict

from supply_chain.models import (
    CandidateLink,
    ConfidenceBand,
    NormalizedEdge,
    ParsedEvidence,
    RelationType,
)
from supply_chain.normalize.entities import normalize_name


def build_edges(
    evidence_items: list[ParsedEvidence],
    entity_lookup: dict[str, str],
) -> tuple[list[NormalizedEdge], list[CandidateLink]]:
    explicit_edges: dict[str, NormalizedEdge] = {}
    candidates: list[CandidateLink] = []
    named_relationships = _index_named_relationships(evidence_items)
    role_candidates = _index_role_candidates(evidence_items)

    for item in evidence_items:
        reporter_id = entity_lookup[normalize_name(item.reporter_name)]
        counterparty_id = entity_lookup[normalize_name(item.counterparty_name)]

        if item.named_counterparty:
            source_id, target_id = _directed_pair(item, reporter_id, counterparty_id)
            edge_id = _edge_id(source_id, target_id, item.relation_type)
            existing = explicit_edges.get(edge_id)
            if existing is None:
                explicit_edges[edge_id] = NormalizedEdge(
                    edge_id=edge_id,
                    source_entity_id=source_id,
                    target_entity_id=target_id,
                    relation_type=item.relation_type,
                    confidence=item.confidence,
                    evidence_ids=[item.evidence_id],
                    countries=[item.country],
                    source_systems=[item.source_system],
                    explicit=True,
                )
            else:
                existing.evidence_ids.append(item.evidence_id)
                if item.source_system not in existing.source_systems:
                    existing.source_systems.append(item.source_system)
                if item.country not in existing.countries:
                    existing.countries.append(item.country)
            continue

        relation_type = item.relation_type
        source_id, target_id = _directed_pair(item, reporter_id, counterparty_id)
        placeholder_edge_id = _edge_id(source_id, target_id, relation_type)
        existing = explicit_edges.get(placeholder_edge_id)
        if existing is None:
            explicit_edges[placeholder_edge_id] = NormalizedEdge(
                edge_id=placeholder_edge_id,
                source_entity_id=source_id,
                target_entity_id=target_id,
                relation_type=relation_type,
                confidence=item.confidence,
                evidence_ids=[item.evidence_id],
                countries=[item.country],
                source_systems=[item.source_system],
                explicit=False,
            )
        else:
            existing.evidence_ids.append(item.evidence_id)
            if item.source_system not in existing.source_systems:
                existing.source_systems.append(item.source_system)
            if item.country not in existing.countries:
                existing.countries.append(item.country)

        candidates.extend(
            _infer_candidates(
                item=item,
                placeholder_entity_id=counterparty_id,
                named_relationships=named_relationships,
                entity_lookup=entity_lookup,
                role_candidates=role_candidates,
            )
        )

    deduped_candidates: dict[str, CandidateLink] = {}
    for candidate in candidates:
        deduped_candidates[candidate.candidate_link_id] = candidate
    return list(explicit_edges.values()), list(deduped_candidates.values())


def _index_named_relationships(evidence_items: list[ParsedEvidence]) -> dict[str, list[ParsedEvidence]]:
    indexed: dict[str, list[ParsedEvidence]] = defaultdict(list)
    for item in evidence_items:
        if item.named_counterparty:
            indexed[normalize_name(item.reporter_name)].append(item)
            indexed[normalize_name(item.counterparty_name)].append(item)
    return indexed


def _index_role_candidates(evidence_items: list[ParsedEvidence]) -> dict[str, dict[str, list[str]]]:
    indexed: dict[str, dict[str, list[str]]] = {
        "supplier": defaultdict(list),
        "customer": defaultdict(list),
    }
    for item in evidence_items:
        if not item.named_counterparty:
            continue
        if item.relation_type == RelationType.SUPPLIER:
            indexed["supplier"][item.counterparty_name].append(item.evidence_id)
            indexed["customer"][item.reporter_name].append(item.evidence_id)
        elif item.relation_type == RelationType.CUSTOMER:
            indexed["customer"][item.counterparty_name].append(item.evidence_id)
            indexed["supplier"][item.reporter_name].append(item.evidence_id)
    return indexed


def _infer_candidates(
    item: ParsedEvidence,
    placeholder_entity_id: str,
    named_relationships: dict[str, list[ParsedEvidence]],
    entity_lookup: dict[str, str],
    role_candidates: dict[str, dict[str, list[str]]],
) -> list[CandidateLink]:
    reporter_key = normalize_name(item.reporter_name)
    reporter_related = named_relationships.get(reporter_key, [])
    possibilities: dict[str, dict[str, object]] = {}

    for related in reporter_related:
        if related.evidence_id == item.evidence_id:
            continue
        if item.relation_type == RelationType.UNDISCLOSED_CUSTOMER and related.relation_type == RelationType.SUPPLIER:
            _record_candidate(
                possibilities,
                candidate_name=related.reporter_name,
                evidence_ids=[related.evidence_id],
                rationale=f"{related.reporter_name} is explicitly connected to {item.reporter_name} in another downloaded filing.",
                reciprocal=True,
            )
        elif item.relation_type == RelationType.UNDISCLOSED_SUPPLIER and related.relation_type == RelationType.CUSTOMER:
            _record_candidate(
                possibilities,
                candidate_name=related.reporter_name,
                evidence_ids=[related.evidence_id],
                rationale=f"{related.reporter_name} is explicitly connected to {item.reporter_name} in another downloaded filing.",
                reciprocal=True,
            )
        elif related.counterparty_name == item.reporter_name:
            _record_candidate(
                possibilities,
                candidate_name=related.reporter_name,
                evidence_ids=[related.evidence_id],
                rationale=f"{related.reporter_name} names {item.reporter_name} as a counterparty in another downloaded filing.",
                reciprocal=True,
            )

    fallback_role = "customer" if item.relation_type == RelationType.UNDISCLOSED_CUSTOMER else "supplier"
    for candidate_name, evidence_ids in role_candidates[fallback_role].items():
        if normalize_name(candidate_name) == reporter_key:
            continue
        _record_candidate(
            possibilities,
            candidate_name=candidate_name,
            evidence_ids=evidence_ids,
            rationale=f"{candidate_name} repeatedly appears as an explicit {fallback_role} in the downloaded-source corpus.",
            reciprocal=False,
        )

    ranked: list[CandidateLink] = []
    scored_candidates = sorted(
        possibilities.items(),
        key=lambda item: (
            -int(bool(item[1]["reciprocal"])),
            -len(item[1]["evidence_ids"]),
            item[0],
        ),
    )
    for rank, (candidate_name, candidate_meta) in enumerate(scored_candidates[:5], start=1):
        candidate_key = normalize_name(candidate_name)
        candidate_entity_id = entity_lookup.get(candidate_key)
        if not candidate_entity_id:
            continue
        evidence_ids = sorted(candidate_meta["evidence_ids"])
        reciprocal = bool(candidate_meta["reciprocal"])
        rationale = str(candidate_meta["rationale"])
        ranked.append(
            CandidateLink(
                candidate_link_id=_candidate_id(placeholder_entity_id, candidate_entity_id),
                undisclosed_entity_id=placeholder_entity_id,
                candidate_entity_id=candidate_entity_id,
                rank=rank,
                confidence=ConfidenceBand.MEDIUM if reciprocal or len(evidence_ids) > 2 else ConfidenceBand.LOW,
                rationale=rationale,
                supporting_evidence_ids=evidence_ids,
            )
        )
    return ranked


def _directed_pair(item: ParsedEvidence, reporter_id: str, counterparty_id: str) -> tuple[str, str]:
    if item.relation_type in {RelationType.SUPPLIER, RelationType.UNDISCLOSED_SUPPLIER}:
        return counterparty_id, reporter_id
    return reporter_id, counterparty_id


def _edge_id(source_id: str, target_id: str, relation_type: RelationType) -> str:
    return f"edge-{hashlib.md5(f'{source_id}:{target_id}:{relation_type.value}'.encode('utf-8')).hexdigest()[:12]}"


def _candidate_id(placeholder_entity_id: str, candidate_entity_id: str) -> str:
    return f"cand-{hashlib.md5(f'{placeholder_entity_id}:{candidate_entity_id}'.encode('utf-8')).hexdigest()[:12]}"


def _record_candidate(
    possibilities: dict[str, dict[str, object]],
    *,
    candidate_name: str,
    evidence_ids: list[str],
    rationale: str,
    reciprocal: bool,
) -> None:
    if candidate_name.startswith("Undisclosed "):
        return
    existing = possibilities.setdefault(
        candidate_name,
        {
            "evidence_ids": set(),
            "rationale": rationale,
            "reciprocal": reciprocal,
        },
    )
    existing["evidence_ids"].update(evidence_ids)
    if reciprocal:
        existing["reciprocal"] = True
        existing["rationale"] = rationale
