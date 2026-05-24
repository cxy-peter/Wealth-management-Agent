from __future__ import annotations

from typing import Any

import pandas as pd


def import_weekly_snapshot(frame: pd.DataFrame, upload_id: str = "manual") -> dict[str, Any]:
    records = frame.copy()
    if "report_date" in records:
        records["report_date"] = pd.to_datetime(records["report_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    records["source_type"] = "manual_upload"
    records["evidence_id"] = [f"ev_upload_{upload_id}_weekly_{idx + 1}" for idx in range(len(records))]
    return {"schema": "product_weekly_snapshot", "row_count": int(len(records)), "records": records.to_dict(orient="records")}
