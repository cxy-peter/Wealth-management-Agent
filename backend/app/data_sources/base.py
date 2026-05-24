from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from typing import Any, Protocol


REQUIRED_SOURCE_FIELDS = [
    "source_type",
    "source_name",
    "source_url_or_file",
    "fetched_at",
    "as_of_date",
    "staleness_days",
    "confidence_level",
    "evidence_id",
    "parser_version",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value)[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def staleness_days(as_of_date: Any, today: date | None = None) -> int:
    parsed = parse_date(as_of_date)
    if parsed is None:
        return 9999
    anchor = today or date.today()
    return max(0, (anchor - parsed).days)


@dataclass(frozen=True)
class DataSourceRecord:
    source_type: str
    source_name: str
    source_url_or_file: str
    fetched_at: str
    as_of_date: str
    staleness_days: int
    confidence_level: str
    evidence_id: str
    parser_version: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdapterResult:
    adapter_name: str
    adapter_status: str
    records: list[DataSourceRecord]
    error_type: str | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter_name": self.adapter_name,
            "adapter_status": self.adapter_status,
            "records": [record.to_dict() for record in self.records],
            "error_type": self.error_type,
            "message": self.message,
        }


class DataSourceAdapter(Protocol):
    source_type: str
    source_name: str
    parser_version: str

    def fetch(self) -> Any:
        ...

    def parse(self, raw: Any) -> list[dict[str, Any]]:
        ...

    def normalize(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ...

    def validate(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        ...

    def to_records(self, rows: list[dict[str, Any]]) -> list[DataSourceRecord]:
        ...


def attach_source_metadata(
    payload: dict[str, Any],
    *,
    source_type: str,
    source_name: str,
    source_url_or_file: str,
    evidence_id: str,
    as_of_date: str,
    confidence_level: str = "medium",
    parser_version: str = "v1",
    fetched_at: str | None = None,
) -> DataSourceRecord:
    return DataSourceRecord(
        source_type=source_type,
        source_name=source_name,
        source_url_or_file=source_url_or_file,
        fetched_at=fetched_at or utc_now_iso(),
        as_of_date=as_of_date,
        staleness_days=staleness_days(as_of_date),
        confidence_level=confidence_level,
        evidence_id=evidence_id,
        parser_version=parser_version,
        payload=payload,
    )

