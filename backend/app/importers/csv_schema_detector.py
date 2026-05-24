from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class SchemaDetectionResult:
    schema_name: str
    columns: list[str]
    confidence: float
    missing_required_fields: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "columns": self.columns,
            "confidence": self.confidence,
            "missing_required_fields": self.missing_required_fields,
        }


REQUIRED_FIELDS = {
    "product_weekly_snapshot": {"report_date", "product_code", "product_name"},
    "product_nav_weekly": {"product_code", "nav_date", "nav"},
    "peer_product_metrics": {"peer_product_code", "report_date", "return_3m"},
    "market_issuance_weekly": {"report_date"},
    "channel_peer_universe": {"channel"},
}


def detect_schema_from_columns(columns: list[str]) -> SchemaDetectionResult:
    lowered = {str(column).lower(): str(column) for column in columns}
    joined = " ".join(lowered)
    if "nav_date" in lowered or ("nav" in lowered and "latest_nav" not in lowered):
        schema = "product_nav_weekly"
    elif "peer_product_code" in lowered:
        schema = "peer_product_metrics"
    elif "new_product" in joined or "issuance" in joined:
        schema = "market_issuance_weekly"
    elif "channel" in lowered and "product_code" not in lowered:
        schema = "channel_peer_universe"
    else:
        schema = "product_weekly_snapshot"
    required = REQUIRED_FIELDS[schema]
    missing = sorted(field for field in required if field not in lowered)
    confidence = round(1 - len(missing) / max(len(required), 1), 3)
    return SchemaDetectionResult(schema, list(columns), confidence, missing)


def detect_csv_schema(path: str) -> dict[str, Any]:
    frame = pd.read_csv(path, nrows=20)
    return detect_schema_from_columns(frame.columns.astype(str).tolist()).to_dict()
