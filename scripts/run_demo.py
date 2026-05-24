from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.agents.workflow import ResearchRequest, run_workflow  # noqa: E402
from backend.app.weekly_report.generators.weekly_report_generator import generate_weekly_report  # noqa: E402
from backend.app.weekly_report.weekly_report_verifier import verify_weekly_report  # noqa: E402


def run_weekly_demo(report_date: str | None, output: str) -> None:
    result = generate_weekly_report(report_date)
    result["verification_result"] = verify_weekly_report(result)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result["report_markdown"], encoding="utf-8")
    print(f"Weekly report generated: {path}")
    print(f"report_date: {result['report_date']}")
    print(f"product_count: {result['product_count']}")
    print(f"verification_pass: {result['verification_result']['pass']}")


def run_legacy_demo(symbol: str, company: str, output: str) -> None:
    result = run_workflow(ResearchRequest(symbol=symbol, company=company, output_path=output))
    print(f"Legacy report generated: {result['report_path']}")
    print("Key metrics:")
    for key in ["total_return", "annualized_return", "annualized_volatility", "max_drawdown", "sharpe_ratio"]:
        print(f"  {key}: {result['metrics'][key]:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the weekly wealth product research demo")
    parser.add_argument("--report-date", default=None)
    parser.add_argument("--output", default=str(Path("reports") / "demo_report.md"))
    parser.add_argument("--legacy", action="store_true", help="Run the legacy generic research workflow.")
    parser.add_argument("--symbol", default="600519")
    parser.add_argument("--company", default="贵州茅台")
    args = parser.parse_args()

    if args.legacy:
        run_legacy_demo(args.symbol, args.company, args.output)
    else:
        run_weekly_demo(args.report_date, args.output)


if __name__ == "__main__":
    main()
