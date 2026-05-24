from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.weekly_report.generators.weekly_report_generator import generate_weekly_report
from backend.app.weekly_report.weekly_report_verifier import verify_weekly_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the weekly product report demo.")
    parser.add_argument("--report-date", default=None)
    parser.add_argument("--output", default="reports/demo_report.md")
    args = parser.parse_args()
    result = generate_weekly_report(args.report_date)
    result["verification_result"] = verify_weekly_report(result)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result["report_markdown"], encoding="utf-8")
    print(json.dumps({"report_date": result["report_date"], "output": str(output), "verification": result["verification_result"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
