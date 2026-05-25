from __future__ import annotations

import json
import urllib.request
from typing import Any

from backend.app.data_sources.base import AdapterResult
from backend.app.data_sources.real_adapters.common import adapters_enabled, failed_result, metadata_record, sample_result


ADAPTER_NAME = "boc_nav_adapter"
PARSER_VERSION = "boc_nav_adapter.v1"
SOURCE_URL = "https://www.bocwm.cn/"


def _sample_records() -> list[Any]:
    rows = [
        {
            "product_code": "AF245408",
            "product_name": "中银理财公开净值样本AF245408",
            "latest_nav": 1.0132,
            "cumulative_nav": 1.0188,
            "nav_date": "2025-04-04",
        }
    ]
    return [
        metadata_record(
            row,
            source_type="official_public_nav",
            source_name="BOC Wealth public NAV sample",
            source_url_or_file=SOURCE_URL,
            evidence_id=f"ev_official_nav_{row['product_code']}_{row['nav_date'].replace('-', '')}",
            as_of_date=row["nav_date"],
            confidence_level="high",
            parser_version=PARSER_VERSION,
        )
        for row in rows
    ]


def fetch_public_nav(product_code: str = "AF245408", url: str | None = None, timeout: int = 8) -> AdapterResult:
    """Fetch/parse a public NAV sample.

    The real network path is intentionally opt-in through ENABLE_REAL_DATA_ADAPTERS.
    The fallback sample keeps demos deterministic and never claims full-market
    coverage.
    """

    records = _sample_records()
    if not adapters_enabled():
        return sample_result(ADAPTER_NAME, records)
    try:
        target = url or SOURCE_URL
        with urllib.request.urlopen(target, timeout=timeout) as response:  # noqa: S310 - opt-in public adapter
            raw = response.read(2_000_000).decode("utf-8", errors="ignore")
        # First version supports JSON fixtures or public pages containing sample fields.
        try:
            payload = json.loads(raw)
            rows = payload if isinstance(payload, list) else payload.get("records", [])
            parsed = [row for row in rows if str(row.get("product_code")) == str(product_code)]
            if parsed:
                return AdapterResult(ADAPTER_NAME, "success", [
                    metadata_record(
                        row,
                        source_type="official_public_nav",
                        source_name="BOC Wealth public NAV",
                        source_url_or_file=target,
                        evidence_id=f"ev_official_nav_{row.get('product_code')}_{str(row.get('nav_date', 'unknown')).replace('-', '')}",
                        as_of_date=str(row.get("nav_date") or row.get("as_of_date") or ""),
                        confidence_level="high",
                        parser_version=PARSER_VERSION,
                    )
                    for row in parsed
                ])
        except Exception:
            pass
        return AdapterResult(ADAPTER_NAME, "success_sample", records, message="Public page fetched, structured NAV fields not found; using sample fallback.")
    except Exception as exc:  # pragma: no cover - depends on network
        return failed_result(ADAPTER_NAME, exc, records)
