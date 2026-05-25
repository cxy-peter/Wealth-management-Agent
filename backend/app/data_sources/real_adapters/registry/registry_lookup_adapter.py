from __future__ import annotations

import re

from backend.app.data_sources.base import AdapterResult
from backend.app.data_sources.real_adapters.common import metadata_record, sample_result


PARSER_VERSION = "registry_lookup_adapter.v1"


def lookup_registry_code(registry_code: str = "", product_code: str = "") -> AdapterResult:
    code = registry_code or product_code or "AF245408"
    basic_format_ok = bool(re.match(r"^[A-Z0-9]{6,24}$", code))
    status = "manual_check_required" if basic_format_ok else "unknown"
    row = {
        "registry_code": code,
        "product_code": product_code or code,
        "registry_status": status,
        "verified": False,
        "verification_note": "No official registry API configured; never marking verified=true in sample mode.",
    }
    record = metadata_record(
        row,
        source_type="registry_lookup_sample",
        source_name="Registry lookup sample",
        source_url_or_file="manual_check_required:financial_product_registry",
        evidence_id=f"ev_registry_{code}",
        as_of_date="2025-04-04",
        confidence_level="medium",
        parser_version=PARSER_VERSION,
    )
    return sample_result("registry_lookup_adapter", [record], "registry lookup requires manual check or configured adapter")
