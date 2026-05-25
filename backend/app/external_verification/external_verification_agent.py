from __future__ import annotations

from typing import Any

from backend.app.external_verification.external_source_registry import run_external_sources
from backend.app.external_verification.source_boundary_guardrail import check_source_boundary
from backend.app.external_verification.verification_score import external_verification_score


def _payloads(adapter_payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = adapter_payload.get("records") or []
    return [record.get("payload", {}) for record in records if isinstance(record, dict)]


def run_external_verification(
    product_code: str,
    *,
    registry_code: str | None = None,
    uploaded_nav: float | None = None,
    report_text: str = "",
) -> dict[str, Any]:
    sources = run_external_sources(product_code, registry_code)
    nav_rows = _payloads(sources["official_public_nav"])
    disclosure_rows = _payloads(sources["official_disclosure_sample"])
    registry_rows = _payloads(sources["registry_lookup_sample"])
    rate_rows = _payloads(sources["public_reference_rate_api"]) + _payloads(sources["deposit_rate_sample"])

    verified_fields: list[str] = []
    unverified_fields: list[str] = []
    conflicting_fields: list[dict[str, Any]] = []

    official_nav = next((row for row in nav_rows if str(row.get("product_code")) == str(product_code)), None)
    if official_nav:
        verified_fields.extend(["product_code", "latest_nav", "nav_date"])
        if uploaded_nav is not None:
            diff = abs(float(uploaded_nav) - float(official_nav.get("latest_nav") or 0))
            if diff > 0.0005:
                conflicting_fields.append(
                    {
                        "field": "latest_nav",
                        "uploaded_value": uploaded_nav,
                        "official_value": official_nav.get("latest_nav"),
                        "evidence_id": next((r.get("evidence_id") for r in sources["official_public_nav"].get("records", [])), ""),
                    }
                )
    else:
        unverified_fields.extend(["latest_nav", "nav_date"])

    registry_status = registry_rows[0].get("registry_status") if registry_rows else "unknown"
    if registry_status in {"manual_check_required", "unknown"}:
        unverified_fields.append("registry_code")

    score = external_verification_score(
        official_nav_coverage=1.0 if official_nav else 0.0,
        disclosure_coverage=1.0 if disclosure_rows else 0.0,
        reference_rate_coverage=1.0 if rate_rows else 0.0,
        registry_check_coverage=0.5 if registry_status == "manual_check_required" else 0.0,
        source_freshness_score=0.8,
        conflict_penalty=1.0 if conflicting_fields else 0.0,
    )

    boundary = check_source_boundary(
        report_text,
        {
            "source_types": ["official_public_nav", "official_disclosure_sample", "registry_lookup_sample", "public_reference_rate_api", "synthetic_weekly_snapshot"],
            "synthetic_peer_universe": True,
            "percentile_from_synthetic": True,
            "nav_conflict": bool(conflicting_fields),
            "official_adapter_status": sources["official_public_nav"].get("adapter_status"),
        },
    )

    result = {
        "verified_fields": verified_fields,
        "unverified_fields": unverified_fields,
        "conflicting_fields": conflicting_fields,
        "official_sources_used": [
            record for key in ["official_public_nav", "official_disclosure_sample", "public_reference_rate_api"] for record in sources[key].get("records", [])
        ],
        "synthetic_fields_used": ["peer_percentile", "weekly_snapshot"],
        "verification_score": score,
        "warnings": [
            *(boundary.get("warnings") or []),
            *([] if not conflicting_fields else ["官方净值与上传净值存在差异，需要人工复核。"]),
        ],
        "source_boundary": boundary,
    }
    return {
        "product_code": product_code,
        "external_sources": sources,
        "external_verification_result": result,
        "source_coverage": {
            "official_public_nav": len(nav_rows),
            "official_disclosure_sample": len(disclosure_rows),
            "registry_lookup_sample": len(registry_rows),
            "public_reference_rate_api": len(rate_rows),
            "manual_upload": 1 if uploaded_nav is not None else 0,
            "synthetic_weekly_snapshot": 2,
        },
    }
