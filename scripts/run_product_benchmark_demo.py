from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.weekly_report.generators.benchmark_report_generator import peer_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the product benchmark demo.")
    parser.add_argument("--product-code", default="WP0001")
    parser.add_argument("--report-date", default=None)
    args = parser.parse_args()
    print(json.dumps(peer_benchmark(args.product_code, args.report_date), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
