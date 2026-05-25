from __future__ import annotations

from backend.app.data_sources.real_adapters.reference_rates.chinabond_curve_adapter import fetch_chinabond_curve


def fetch_chinamoney_curve():
    result = fetch_chinabond_curve()
    return type(result)(
        adapter_name="chinamoney_curve_adapter",
        adapter_status=result.adapter_status,
        records=result.records,
        error_type=result.error_type,
        message="online fetch disabled; fallback_to_sample",
    )
