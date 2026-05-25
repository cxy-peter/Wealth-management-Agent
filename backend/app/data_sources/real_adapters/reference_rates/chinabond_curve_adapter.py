from __future__ import annotations

from backend.app.data_sources.base import AdapterResult
from backend.app.data_sources.real_adapters.common import metadata_record, sample_result


def fetch_chinabond_curve() -> AdapterResult:
    rows = [
        ("CGB_3M", 90, "3M", 0.0155),
        ("CGB_6M", 180, "6M", 0.0165),
        ("CGB_1Y", 365, "1Y", 0.0178),
        ("CGB_5Y", 1825, "5Y", 0.021),
    ]
    records = [
        metadata_record(
            {
                "rate_id": rate_id,
                "as_of_date": "2025-04-04",
                "currency": "CNY",
                "rate_type": "gov_bond",
                "tenor_days": days,
                "tenor_label": label,
                "annual_yield": value,
            },
            source_type="public_reference_rate_api",
            source_name="ChinaBond curve sample",
            source_url_or_file="data/public/reference_rates/chinabond_curve_sample.csv",
            evidence_id=f"ev_chinabond_{rate_id}_20250404",
            as_of_date="2025-04-04",
            confidence_level="medium",
            parser_version="chinabond_curve_adapter.v1",
        )
        for rate_id, days, label, value in rows
    ]
    return sample_result("chinabond_curve_adapter", records, "online fetch disabled; fallback_to_sample")
