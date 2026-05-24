from __future__ import annotations

from typing import Any

import pandas as pd

from backend.app.importers.csv_schema_detector import detect_schema_from_columns


def detect_excel_schemas(path: str) -> dict[str, Any]:
    workbook = pd.ExcelFile(path)
    sheets = []
    for sheet_name in workbook.sheet_names:
        frame = pd.read_excel(workbook, sheet_name=sheet_name, nrows=20)
        detection = detect_schema_from_columns(frame.columns.astype(str).tolist()).to_dict()
        sheets.append({"sheet_name": sheet_name, **detection, "preview": frame.head(5).to_dict(orient="records")})
    return {"file_name": path, "sheets": sheets}
