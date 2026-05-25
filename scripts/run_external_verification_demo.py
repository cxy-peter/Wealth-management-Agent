from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.external_verification.external_verification_agent import run_external_verification


def main() -> None:
    parser = argparse.ArgumentParser(description="Run external verification sample demo.")
    parser.add_argument("--product-code", default="AF245408")
    parser.add_argument("--registry-code", default="")
    parser.add_argument("--uploaded-nav", type=float, default=None)
    args = parser.parse_args()
    result = run_external_verification(args.product_code, registry_code=args.registry_code or None, uploaded_nav=args.uploaded_nav)
    print(json.dumps(result["external_verification_result"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
