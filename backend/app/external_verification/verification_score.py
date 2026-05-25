from __future__ import annotations


def external_verification_score(
    *,
    official_nav_coverage: float = 0.0,
    disclosure_coverage: float = 0.0,
    reference_rate_coverage: float = 0.0,
    registry_check_coverage: float = 0.0,
    source_freshness_score: float = 0.0,
    conflict_penalty: float = 0.0,
) -> float:
    score = (
        0.30 * official_nav_coverage
        + 0.20 * disclosure_coverage
        + 0.20 * reference_rate_coverage
        + 0.15 * registry_check_coverage
        + 0.15 * source_freshness_score
        - 0.30 * conflict_penalty
    )
    return round(max(0.0, min(1.0, score)), 4)
