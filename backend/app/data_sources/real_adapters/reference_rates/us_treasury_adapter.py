from __future__ import annotations

from datetime import date, datetime
from html import unescape
from html.parser import HTMLParser
import re
import urllib.request

from backend.app.data_sources.base import AdapterResult
from backend.app.data_sources.real_adapters.common import adapters_enabled, failed_result, metadata_record, sample_result


ADAPTER_NAME = "us_treasury_adapter"
PARSER_VERSION = "us_treasury_adapter.v2"
TREASURY_YIELD_CURVE_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "TextView?type=daily_treasury_yield_curve"
)

TENOR_COLUMNS = {
    "1 Mo": ("1M", 30),
    "3 Mo": ("3M", 90),
    "6 Mo": ("6M", 180),
    "1 Yr": ("1Y", 365),
    "2 Yr": ("2Y", 730),
    "5 Yr": ("5Y", 1825),
    "10 Yr": ("10Y", 3650),
    "30 Yr": ("30Y", 10950),
}


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._in_row = False
        self._in_cell = False
        self._current_row: list[str] = []
        self._current_cell: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._in_row = True
            self._current_row = []
        elif self._in_row and tag in {"td", "th"}:
            self._in_cell = True
            self._current_cell = []

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._in_cell:
            text = unescape(" ".join(self._current_cell))
            text = re.sub(r"\s+", " ", text).strip()
            self._current_row.append(text)
            self._in_cell = False
        elif tag == "tr" and self._in_row:
            if self._current_row:
                self.rows.append(self._current_row)
            self._in_row = False


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
            source_name="US Treasury Daily Treasury Rates sample",
            source_url_or_file=TREASURY_YIELD_CURVE_URL,
            evidence_id=f"ev_us_treasury_{label}_20250404",
            as_of_date="2025-04-04",
            confidence_level="high",
            parser_version=PARSER_VERSION,
        )
        for label, days, value in tenors
    ]


def _parse_date(value: str) -> str | None:
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _parse_rate(value: str) -> float | None:
    cleaned = value.strip().replace("%", "")
    if cleaned in {"", "N/A", "NA", "-"}:
        return None
    try:
        raw = float(cleaned)
    except ValueError:
        return None
    return raw / 100 if raw > 1 else raw


def _parse_treasury_html(raw_html: str) -> list[dict[str, float | int | str]]:
    parser = _TableParser()
    parser.feed(raw_html)
    rows = parser.rows
    header_index = None
    header: list[str] = []
    for idx, row in enumerate(rows):
        if "Date" in row and any(column in row for column in TENOR_COLUMNS):
            header_index = idx
            header = row
            break
    if header_index is None:
        return []

    records_by_date: list[dict[str, str]] = []
    for row in rows[header_index + 1 :]:
        if len(row) < len(header):
            continue
        mapped = dict(zip(header, row))
        if _parse_date(mapped.get("Date", "")):
            records_by_date.append(mapped)
    if not records_by_date:
        return []

    latest = max(records_by_date, key=lambda item: _parse_date(item.get("Date", "")) or "")
    as_of_date = _parse_date(latest.get("Date", "")) or date.today().isoformat()
    parsed: list[dict[str, float | int | str]] = []
    for column, (label, days) in TENOR_COLUMNS.items():
        annual_yield = _parse_rate(latest.get(column, ""))
        if annual_yield is None:
            continue
        parsed.append(
            {
                "rate_id": f"USD_TREASURY_{label}",
                "as_of_date": as_of_date,
                "currency": "USD",
                "rate_type": "us_treasury",
                "tenor_days": days,
                "tenor_label": label,
                "annual_yield": annual_yield,
            }
        )
    return parsed


def _to_records(parsed_rates: list[dict[str, float | int | str]]):
    records = []
    for row in parsed_rates:
        label = str(row["tenor_label"])
        as_of_date = str(row["as_of_date"])
        records.append(
            metadata_record(
                dict(row),
                source_type="public_reference_rate_api",
                source_name="US Treasury Daily Treasury Rates",
                source_url_or_file=TREASURY_YIELD_CURVE_URL,
                evidence_id=f"ev_us_treasury_{label}_{as_of_date.replace('-', '')}",
                as_of_date=as_of_date,
                confidence_level="high",
                parser_version=PARSER_VERSION,
            )
        )
    return records


def fetch_us_treasury_rates(timeout: int = 8) -> AdapterResult:
    sample_records = _sample_records()
    if not adapters_enabled():
        return sample_result(ADAPTER_NAME, sample_records)
    try:
        request = urllib.request.Request(
            TREASURY_YIELD_CURVE_URL,
            headers={"User-Agent": "wealth-research-agent-demo/1.0 (+public-reference-rate-adapter)"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - opt-in public adapter
            raw = response.read(3_000_000).decode("utf-8", errors="ignore")
        parsed_rates = _parse_treasury_html(raw)
        if not parsed_rates:
            raise ValueError("US Treasury yield curve table was reachable but no tenor rows were parsed")
        return AdapterResult(
            ADAPTER_NAME,
            "success",
            _to_records(parsed_rates),
            message="Parsed public US Treasury Daily Treasury Rates table.",
        )
    except Exception as exc:  # pragma: no cover - depends on public network
        return failed_result(ADAPTER_NAME, exc, sample_records)
