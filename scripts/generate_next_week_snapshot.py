from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.data_sources.synthetic.next_week_generator import generate_next_week_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate demo-only synthetic next-week product research data.")
    parser.add_argument("--as-of-date", default=None)
    parser.add_argument("--base-date", default=None)
    parser.add_argument("--seed", type=int, default=20260709)
    parser.add_argument("--n-products", type=int, default=96)
    args = parser.parse_args()
    result = generate_next_week_snapshot(
        as_of_date=args.as_of_date,
        base_date=args.base_date,
        seed=args.seed,
        n_products=args.n_products,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
