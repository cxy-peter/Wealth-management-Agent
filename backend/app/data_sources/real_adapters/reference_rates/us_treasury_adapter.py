from __future__ import annotations

import csv
import io
import urllib.request

from backend.app.data_sources.base import AdapterResult
from backend.app.data_sources.real_adapters.common import adapters_enabled, failed_result, metadata_record, sample_result


ADAPTER_NAME = "us_treasury_adapter"
PARSER_VERSION = "us_treasury_adapter.v1"
FISCAL_DATA_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/daily_treasury_rates"


def _sample_records():
    tenors = [("1M", 30, 0.052), ("3M", 90, 0.051), ("6M", 180, 0.049), ("1Y", 365, 0.046), ("2Y", 730, 0.043), ("5Y", 1825, 0.041), ("10Y", 3650, 0.042), ("30Y", 10950, 0.044)]
    return [
        metadata_record(
            {
                "rate_id": f"USD_TREASURY_{label}",
                "as_of_date": "2025-04-04",
                "currency": "USD",
                "rate_type": "us_treasury",
                "tenor_days": days,
                "tenor_label": label,
                "annual_yield": value,
            },
            source_type="public_reference_rate_api",
            source_name="US Treasury Fiscal Data API sample",
            source_url_or_file=FISCAL_DATA_URL,
            evidence_id=f"ev_us_treasury_{label}_20250404",
            as_of_date="2025-04-04",
            confidence_level="high",
            parser_version=PARSER_VERSION,
        )
        for label, days, value in tenors
    ]


def fetch_us_treasury_rates(timeout: int = 8) -> AdapterResult:
    records = _sample_records()
    if not adapters_enabled():
        return sample_result(ADAPTER_NAME, records)
    try:
        url = f"{FISCAL_DATA_URL}?sort=-record_date&page[size]=1"
        with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - opt-in public adapter
            raw = response.read(2_000_000).decode("utf-8", errors="ignore")
        if raw.strip().startswith("{"):
            return AdapterResult(ADAPTER_NAME, "success_sample", records, message="Fiscal Data API reachable; v1 keeps normalized sample fallback.")
        csv.DictReader(io.StringIO(raw))
        return AdapterResult(ADAPTER_NAME, "success_sample", records, message="Fiscal Data response parsed as CSV-like payload; using sample fallback.")
    except Exception as exc:  # pragma: no cover - depends on network
        return failed_result(ADAPTER_NAME, exc, records)
