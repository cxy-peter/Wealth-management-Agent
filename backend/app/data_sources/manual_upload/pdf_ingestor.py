from __future__ import annotations

from typing import Any


def preview_pdf(_: bytes | str, sample_pages: int = 2) -> dict[str, Any]:
    return {
        "parser_status": "unsupported_or_optional",
        "file_type": "pdf",
        "sample_pages": sample_pages,
        "message": "PDF text extraction is kept as an optional adapter in the demo.",
    }

