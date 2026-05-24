from __future__ import annotations

from typing import Any

import pandas as pd


def import_peer_benchmark(frame: pd.DataFrame, upload_id: str = "manual") -> dict[str, Any]:
    records = frame.copy()
    records["source_type"] = "manual_upload"
    records["evidence_id"] = [f"ev_upload_{upload_id}_peer_{idx + 1}" for idx in range(len(records))]
    return {"schema": "peer_product_metrics", "row_count": int(len(records)), "records": records.to_dict(orient="records")}
