from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators

disable_optional_pandas_accelerators()

import pandas as pd


def preview_excel(source: bytes | str | Path, sample_rows: int = 5) -> dict[str, Any]:
    try:
        excel_source = BytesIO(source) if isinstance(source, bytes) else source
        workbook = pd.ExcelFile(excel_source)
        sheets = []
        for sheet in workbook.sheet_names[:8]:
            frame = pd.read_excel(workbook, sheet_name=sheet, nrows=sample_rows)
            sheets.append(
                {
                    "sheet_name": sheet,
                    "columns": [str(column) for column in frame.columns],
                    "sample_rows": frame.fillna("").to_dict(orient="records"),
                }
            )
        return {"parser_status": "parsed", "file_type": "excel", "sheets": sheets}
    except Exception as exc:
        return {"parser_status": "failed", "file_type": "excel", "error_type": exc.__class__.__name__, "sheets": []}

