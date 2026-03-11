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


def _infer_candidates(
    item: ParsedEvidence,
    placeholder_entity_id: str,
    named_relationships: dict[str, list[ParsedEvidence]],
    entity_lookup: dict[str, str],
) -> list[CandidateLink]:
    reporter_key = normalize_name(item.reporter_name)
    reporter_related = named_relationships.get(reporter_key, [])
    possibilities: list[tuple[str, str]] = []

    for related in reporter_related:
        if related.evidence_id == item.evidence_id:
            continue
        if item.relation_type == RelationType.UNDISCLOSED_CUSTOMER and related.relation_type == RelationType.SUPPLIER:
            possibilities.append((related.reporter_name, related.evidence_id))
        elif item.relation_type == RelationType.UNDISCLOSED_SUPPLIER and related.relation_type == RelationType.CUSTOMER:
            possibilities.append((related.reporter_name, related.evidence_id))
        elif related.counterparty_name == item.reporter_name:
            possibilities.append((related.reporter_name, related.evidence_id))

    deduped_names: dict[str, list[str]] = defaultdict(list)
    for candidate_name, evidence_id in possibilities:
        deduped_names[candidate_name].append(evidence_id)

    ranked: list[CandidateLink] = []
    for rank, (candidate_name, evidence_ids) in enumerate(sorted(deduped_names.items(), key=lambda item: (-len(item[1]), item[0]))[:5], start=1):
        candidate_key = normalize_name(candidate_name)
        candidate_entity_id = entity_lookup.get(candidate_key)
        if not candidate_entity_id:
            continue
        ranked.append(
            CandidateLink(
                candidate_link_id=_candidate_id(placeholder_entity_id, candidate_entity_id),
                undisclosed_entity_id=placeholder_entity_id,
                candidate_entity_id=candidate_entity_id,
                rank=rank,
                confidence=ConfidenceBand.LOW if len(evidence_ids) == 1 else ConfidenceBand.MEDIUM,
                rationale=f"{candidate_name} appears in other downloaded-source evidence connected to {item.reporter_name}.",
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
