from __future__ import annotations

from supply_chain.models import ConfidenceBand, ParsedEvidence


def rescore_evidence(evidence_items: list[ParsedEvidence]) -> list[ParsedEvidence]:
    rescored: list[ParsedEvidence] = []
    for item in evidence_items:
        updated = item.model_copy()
        if updated.named_counterparty and updated.confidence == ConfidenceBand.LOW:
            updated.confidence = ConfidenceBand.MEDIUM
        if not updated.named_counterparty and updated.confidence == ConfidenceBand.HIGH:
            updated.confidence = ConfidenceBand.MEDIUM
        rescored.append(updated)
    return rescored
