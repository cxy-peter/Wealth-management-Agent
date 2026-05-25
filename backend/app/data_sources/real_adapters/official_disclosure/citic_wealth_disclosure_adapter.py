from __future__ import annotations

import urllib.request

from backend.app.data_sources.base import AdapterResult
from backend.app.data_sources.real_adapters.common import adapters_enabled, failed_result, metadata_record, sample_result


ADAPTER_NAME = "citic_wealth_disclosure_adapter"
PARSER_VERSION = "citic_wealth_disclosure_adapter.v1"
SOURCE_URL = "https://www.citicwealth.com/"


def _sample_records():
    row = {
        "announcement_title": "信银理财产品信息披露公告样本",
        "announcement_date": "2025-04-03",
        "product_name": "公开披露产品样本",
        "product_code": "AF245408",
        "disclosure_type": "nav_announcement",
    }
    return [
        metadata_record(
            row,
            source_type="official_disclosure_sample",
            source_name="CITIC Wealth disclosure sample",
            source_url_or_file=SOURCE_URL,
            evidence_id="ev_citic_disclosure_AF245408_20250403",
            as_of_date=row["announcement_date"],
            confidence_level="high",
            parser_version=PARSER_VERSION,
        )
    ]


def fetch_disclosures(product_keyword: str = "AF245408", url: str | None = None, timeout: int = 8) -> AdapterResult:
    records = _sample_records()
    if not adapters_enabled():
        return sample_result(ADAPTER_NAME, records)
    try:
        target = url or SOURCE_URL
        with urllib.request.urlopen(target, timeout=timeout) as response:  # noqa: S310 - opt-in public adapter
            html = response.read(2_000_000).decode("utf-8", errors="ignore")
        if product_keyword and product_keyword in html:
            return AdapterResult(ADAPTER_NAME, "success_sample", records, message="Public page fetched and keyword observed; structured parser uses sample record in v1.")
        return AdapterResult(ADAPTER_NAME, "success_sample", records, message="Public page fetched; keyword not found; using sample fallback.")
    except Exception as exc:  # pragma: no cover - depends on network
        return failed_result(ADAPTER_NAME, exc, records)
