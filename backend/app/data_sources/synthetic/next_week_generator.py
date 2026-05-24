from __future__ import annotations

import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from backend.app.data_sources.base import staleness_days
from backend.app.data_sources.synthetic.nav_path_simulator import simulate_weekly_nav
from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators
from backend.app.weekly_report.parsers.weekly_snapshot_parser import list_report_dates, load_weekly_snapshot

disable_optional_pandas_accelerators()

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
LIVE_DIR = ROOT / "data" / "live"


def _default_as_of(base_date: str | None = None) -> str:
    if base_date:
        return (date.fromisoformat(base_date) + timedelta(days=7)).isoformat()
    dates = list_report_dates()
    return (date.fromisoformat(dates[-1]) + timedelta(days=7)).isoformat()


def _source_columns(row: dict[str, Any], as_of_date: str, source_name: str, evidence_id: str, fetched_at: str) -> dict[str, Any]:
    return {
        **row,
        "source_type": "synthetic_weekly_snapshot",
        "source_name": source_name,
        "source_url_or_file": "scripts/generate_next_week_snapshot.py",
        "fetched_at": fetched_at,
        "as_of_date": as_of_date,
        "staleness_days": staleness_days(as_of_date),
        "confidence_level": "medium",
        "evidence_id": evidence_id,
        "parser_version": "next_week_generator.v1",
    }


def generate_next_week_snapshot(
    *,
    as_of_date: str | None = None,
    base_date: str | None = None,
    seed: int = 20260709,
    n_products: int = 96,
    output_dir: str | Path = LIVE_DIR,
) -> dict[str, Any]:
    rng = random.Random(seed)
    selected_as_of = as_of_date or _default_as_of(base_date)
    selected_base = base_date or list_report_dates()[-1]
    base = load_weekly_snapshot(selected_base).head(n_products).copy()
    if base.empty:
        raise FileNotFoundError(f"no base weekly snapshot for {selected_base}")

    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    weekly_rows: list[dict[str, Any]] = []
    peer_rows: list[dict[str, Any]] = []
    for _, source in base.iterrows():
        row = source.to_dict()
        code = str(row["product_code"])
        risk_level = str(row.get("risk_level", "R2"))
        risk_num = int(risk_level.replace("R", "") or 2)
        scale_shock = rng.gauss(0.02 - risk_num * 0.005, 0.12 + risk_num * 0.025)
        new_scale = max(0.03, float(row["product_scale_bn"]) + scale_shock)
        new_nav = simulate_weekly_nav(float(row["latest_nav"]), risk_level, rng)
        ret_3m = float(row["return_3m"]) + rng.gauss(0, 0.002 + risk_num * 0.001)
        drawdown = min(0.0, float(row["max_drawdown"]) - abs(rng.gauss(0, 0.0015 * risk_num)))
        vol = max(0.001, float(row["volatility"]) * rng.uniform(0.92, 1.12))
        annual = float(row["since_inception_annual_return"]) + rng.gauss(0, 0.002)
        lower = float(row["benchmark_lower"])
        upper = float(row["benchmark_upper"])
        status = "below_lower" if annual < lower else "above_upper" if annual > upper else "in_range"
        evidence = f"ev_live_snapshot_{code}_{selected_as_of.replace('-', '')}"
        weekly_rows.append(
            _source_columns(
                {
                    **{key: (value.isoformat() if hasattr(value, "isoformat") else value) for key, value in row.items() if key not in {"source_type", "source_name", "source_url_or_file", "fetched_at", "as_of_date", "staleness_days", "confidence_level", "parser_version"}},
                    "report_date": selected_as_of,
                    "product_scale_bn": round(new_scale, 4),
                    "scale_wow_bn": round(new_scale - float(row["product_scale_bn"]), 4),
                    "scale_mom_bn": round(float(row.get("scale_mom_bn", 0)) + scale_shock, 4),
                    "latest_nav": new_nav,
                    "daily_nav_change_bp": round((new_nav / float(row["latest_nav"]) - 1) * 10000 / 5, 2),
                    "since_inception_annual_return": round(annual, 6),
                    "return_3m": round(ret_3m, 6),
                    "max_drawdown": round(drawdown, 6),
                    "volatility": round(vol, 6),
                    "sharpe": round((annual - 0.02) / vol if vol else 0, 6),
                    "benchmark_status": status,
                },
                selected_as_of,
                "Synthetic next-week product snapshot",
                evidence,
                fetched_at,
            )
        )
        for peer_idx in range(2):
            peer_code = f"LPR{code[-4:]}{peer_idx + 1}"
            peer_rows.append(
                _source_columns(
                    {
                        "peer_product_code": peer_code,
                        "report_date": selected_as_of,
                        "return_3m": round(ret_3m + rng.gauss(0, 0.004), 6),
                        "max_drawdown": round(drawdown - abs(rng.gauss(0, 0.004)), 6),
                        "volatility": round(vol * rng.uniform(0.85, 1.2), 6),
                        "sharpe": round(float(row["sharpe"]) + rng.gauss(0, 0.2), 6),
                        "return_percentile": round(rng.uniform(0.05, 0.95), 4),
                        "drawdown_percentile": round(rng.uniform(0.05, 0.95), 4),
                    },
                    selected_as_of,
                    "Synthetic next-week peer metrics",
                    f"ev_live_peer_metric_{peer_code}_{selected_as_of.replace('-', '')}",
                    fetched_at,
                )
            )

    market = [
        _source_columns(
            {
                "report_date": selected_as_of,
                "new_product_count": rng.randint(45, 95),
                "by_investment_nature_json": json.dumps({"固定收益类": rng.randint(20, 45), "混合类": rng.randint(8, 18), "QDII": rng.randint(4, 12)}, ensure_ascii=False),
                "by_duration_json": json.dumps({"日开": rng.randint(4, 12), "90天": rng.randint(8, 18), "180天": rng.randint(8, 20), "1年封闭": rng.randint(6, 16)}, ensure_ascii=False),
                "benchmark_lower_avg": round(rng.uniform(0.018, 0.03), 4),
                "benchmark_upper_avg": round(rng.uniform(0.034, 0.055), 4),
            },
            selected_as_of,
            "Synthetic next-week market issuance",
            f"ev_live_market_issuance_{selected_as_of.replace('-', '')}",
            fetched_at,
        )
    ]

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    weekly_path = output_path / f"weekly_snapshot_{selected_as_of}.csv"
    peer_path = output_path / f"peer_metrics_{selected_as_of}.csv"
    market_path = output_path / f"market_issuance_{selected_as_of}.csv"
    freshness_path = output_path / f"data_freshness_{selected_as_of}.json"

    pd.DataFrame(weekly_rows).to_csv(weekly_path, index=False)
    pd.DataFrame(peer_rows).to_csv(peer_path, index=False)
    pd.DataFrame(market).to_csv(market_path, index=False)
    freshness = {
        "as_of_date": selected_as_of,
        "base_date": selected_base,
        "source_type": "synthetic_weekly_snapshot",
        "record_counts": {"weekly_snapshot": len(weekly_rows), "peer_metrics": len(peer_rows), "market_issuance": len(market)},
        "files": [str(weekly_path), str(peer_path), str(market_path)],
        "generated_at": fetched_at,
        "disclaimer": "Synthetic demo data only; not a real full-market ranking.",
    }
    freshness_path.write_text(json.dumps(freshness, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "generated", **freshness, "freshness_file": str(freshness_path)}
