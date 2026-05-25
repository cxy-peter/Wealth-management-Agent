from __future__ import annotations

from backend.app.data_sources.base import AdapterResult
from backend.app.data_sources.real_adapters.common import sample_result
from backend.app.data_sources.real_adapters.official_disclosure.citic_wealth_disclosure_adapter import _sample_records


def fetch_disclosures(product_keyword: str = "", url: str | None = None, timeout: int = 8) -> AdapterResult:
    records = _sample_records()
    return sample_result("icbc_disclosure_adapter", records, "adapter disabled; ICBC disclosure parser keeps sample fallback in v1")
