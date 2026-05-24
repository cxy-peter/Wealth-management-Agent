from __future__ import annotations

import re
from typing import Any


REGISTRY_CODE_PATTERN = re.compile(r"^[A-Z0-9]{6,24}$")


def validate_registry_code(registry_code: str) -> dict[str, Any]:
    code = str(registry_code or "").strip().upper()
    format_valid = bool(REGISTRY_CODE_PATTERN.match(code))
    return {
        "registry_code": code,
        "format_valid": format_valid,
        "registry_status": "unknown",
        "verified": False,
        "reason": "No real registry API is configured; the demo only validates code format.",
    }

