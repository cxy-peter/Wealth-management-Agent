from __future__ import annotations

from backend.app.data_sources.base import AdapterResult
from backend.app.data_sources.real_adapters.common import metadata_record, sample_result


def fetch_deposit_rates() -> AdapterResult:
    rows = [
        ("RMB_DEPOSIT_3M", 90, "3M", 0.011),
        ("RMB_DEPOSIT_6M", 180, "6M", 0.013),
        ("RMB_DEPOSIT_1Y", 365, "1Y", 0.015),
        ("RMB_DEPOSIT_360D", 360, "360D", 0.0148),
    ]
    records = [
        metadata_record(
            {
                "rate_id": rate_id,
                "as_of_date": "2025-04-04",
                "currency": "CNY",
                "rate_type": "deposit",
                "tenor_days": days,
                "tenor_label": label,
                "annual_yield": value,
            },
            source_type="public_reference_rate_api",
            source_name="Deposit rate sample",
            source_url_or_file="data/public/reference_rates/deposit_rate_sample.csv",
            evidence_id=f"ev_deposit_{rate_id}_20250404",
            as_of_date="2025-04-04",
            confidence_level="medium",
            parser_version="deposit_rate_adapter.v1",
        )
        for rate_id, days, label, value in rows
    ]
    return sample_result("deposit_rate_adapter", records)
