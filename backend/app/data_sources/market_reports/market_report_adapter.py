from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators

disable_optional_pandas_accelerators()

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
REPORT_DIR = ROOT / "data" / "public" / "market_reports"


def load_market_report_samples() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    if not REPORT_DIR.exists():
        return {"adapter_status": "sample_missing", "records": records}
    for path in sorted(REPORT_DIR.glob("*")):
        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            rows = payload if isinstance(payload, list) else payload.get("records") or payload.get("reports") or [payload]
            records.extend(rows)
        elif path.suffix.lower() == ".csv":
            records.extend(pd.read_csv(path).to_dict(orient="records"))
    return {"adapter_status": "available" if records else "sample_missing", "records": records}

