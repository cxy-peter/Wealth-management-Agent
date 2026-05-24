from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.evaluation import run_evaluation  # noqa: E402


def main() -> None:
    payload = run_evaluation()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload["metrics"]["forbidden_wording_fail_rate"] > 0:
        raise SystemExit(1)
    if not all(item["passed"] for item in payload["cases"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
