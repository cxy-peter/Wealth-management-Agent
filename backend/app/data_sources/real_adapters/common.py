from __future__ import annotations

import os
from typing import Any

from backend.app.data_sources.base import AdapterResult, DataSourceRecord, attach_source_metadata


def adapters_enabled() -> bool:
    return os.getenv("ENABLE_REAL_DATA_ADAPTERS", "false").lower() == "true"


def sample_result(adapter_name: str, records: list[DataSourceRecord], message: str = "adapter disabled; using sample fallback") -> AdapterResult:
    return AdapterResult(adapter_name=adapter_name, adapter_status="disabled_sample", records=records, message=message)


def failed_result(adapter_name: str, exc: Exception | str, records: list[DataSourceRecord] | None = None) -> AdapterResult:
    error_type = exc.__class__.__name__ if isinstance(exc, Exception) else "AdapterError"
    message = str(exc)
    return AdapterResult(adapter_name=adapter_name, adapter_status="failed", records=records or [], error_type=error_type, message=message)


def metadata_record(
    payload: dict[str, Any],
    *,
    source_type: str,
    source_name: str,
    source_url_or_file: str,
    evidence_id: str,
    as_of_date: str,
    confidence_level: str = "high",
    parser_version: str,
) -> DataSourceRecord:
    return attach_source_metadata(
        payload,
        source_type=source_type,
        source_name=source_name,
        source_url_or_file=source_url_or_file,
        evidence_id=evidence_id,
        as_of_date=as_of_date,
        confidence_level=confidence_level,
        parser_version=parser_version,
    )
