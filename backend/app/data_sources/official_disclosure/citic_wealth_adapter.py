from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.data_sources.base import AdapterResult, DataSourceRecord, attach_source_metadata

ROOT = Path(__file__).resolve().parents[4]
SAMPLE_PATH = ROOT / "data" / "public" / "official_disclosure" / "citic_wealth_disclosures.json"


class CiticWealthDisclosureAdapter:
    source_type = "official_disclosure_sample"
    source_name = "CITIC wealth disclosure sample"
    parser_version = "citic_wealth_adapter.v1"

    def fetch(self) -> dict[str, Any]:
        if not SAMPLE_PATH.exists():
            return {"adapter_status": "failed", "reason": "local disclosure sample is missing", "records": []}
        return {"adapter_status": "available", "records": json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))}

    def parse(self, raw: dict[str, Any]) -> list[dict[str, Any]]:
        return list(raw.get("records", []))

    def normalize(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for row in rows:
            normalized.append(
                {
                    "title": row.get("title", ""),
                    "notice_type": row.get("notice_type", "公告"),
                    "published_at": row.get("published_at", ""),
                    "product_keyword": row.get("product_keyword", ""),
                    "source_url_or_file": row.get("source_url_or_file", str(SAMPLE_PATH)),
                    "evidence_id": row.get("evidence_id", ""),
                }
            )
        return normalized

    def validate(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        missing = [row.get("evidence_id", "") for row in rows if not row.get("source_url_or_file")]
        return {"valid": not missing, "missing_source_url_or_file": missing}

    def to_records(self, rows: list[dict[str, Any]]) -> list[DataSourceRecord]:
        return [
            attach_source_metadata(
                row,
                source_type=self.source_type,
                source_name=self.source_name,
                source_url_or_file=row.get("source_url_or_file") or str(SAMPLE_PATH),
                evidence_id=row.get("evidence_id") or f"ev_citic_disclosure_{index:03d}",
                as_of_date=str(row.get("published_at", ""))[:10],
                confidence_level="medium",
                parser_version=self.parser_version,
            )
            for index, row in enumerate(rows, 1)
        ]

    def run(self) -> AdapterResult:
        raw = self.fetch()
        if raw.get("adapter_status") != "available":
            return AdapterResult(self.source_name, "failed", [], "SampleMissing", raw.get("reason", ""))
        rows = self.normalize(self.parse(raw))
        validation = self.validate(rows)
        return AdapterResult(
            self.source_name,
            "available" if validation["valid"] else "partial",
            self.to_records(rows),
            message=json.dumps(validation, ensure_ascii=False),
        )

