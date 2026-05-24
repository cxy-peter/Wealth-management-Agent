from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.agents.workflow import ResearchRequest, run_workflow  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Wealth Research Agent MVP demo")
    parser.add_argument("--symbol", default="600519")
    parser.add_argument("--company", default="贵州茅台")
    parser.add_argument("--output", default=str(Path("reports") / "demo_report.md"))
    args = parser.parse_args()

    result = run_workflow(ResearchRequest(symbol=args.symbol, company=args.company, output_path=args.output))
    print(f"Report generated: {result['report_path']}")
    print("Key metrics:")
    for key in ["total_return", "annualized_return", "annualized_volatility", "max_drawdown", "sharpe_ratio"]:
        print(f"  {key}: {result['metrics'][key]:.4f}")


if __name__ == "__main__":
    main()
