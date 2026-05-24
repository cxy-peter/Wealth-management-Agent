"""Generate synthetic weekly-report datasets for the wealth research workspace.

The generator intentionally creates mock data only. Field names and business
logic mirror common weekly product reporting workflows, but no real product,
client, or internal company data is copied into the repository.
"""
from __future__ import annotations

import csv
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
WEEKLY = DATA / "weekly"
BENCHMARK = DATA / "benchmark"
DPO = DATA / "dpo"

SEED = 20260709
PRODUCT_COUNT = 96
PEER_COUNT = 360
REPORT_DATES = [date(2025, 1, 31) + timedelta(days=7 * i) for i in range(10)]

PRODUCT_TYPES = ["纯固收", "固收增强", "多资产", "混合类", "QDII", "现金管理", "封闭式", "最短持有期型", "日开型"]
SERIES = ["稳健添利", "悦享固收", "多元配置", "现金优选", "全球配置", "封闭精选", "持有期增强"]
CHANNELS = ["个金", "私银", "对公", "直销", "百信", "交行", "厦门银行", "邮惠万家"]
RISK_LEVELS = ["R1", "R2", "R3", "R4", "R5"]
OPEN_TYPES = ["日开", "7天", "14天", "21天", "30天", "60天", "90天", "120天", "180天", "270天", "360天", "1年封闭"]
INVESTMENT_NATURE = ["固定收益类", "混合类", "权益类", "商品及金融衍生品类", "QDII"]
BENCHMARK_STATUS = ["above_upper", "in_range", "below_lower"]

TYPE_CONFIG = {
    "现金管理": {"risk": ["R1"], "return": 0.018, "vol": 0.004, "dd": 0.002},
    "日开型": {"risk": ["R1", "R2"], "return": 0.022, "vol": 0.006, "dd": 0.004},
    "纯固收": {"risk": ["R2"], "return": 0.031, "vol": 0.018, "dd": 0.014},
    "固收增强": {"risk": ["R2", "R3"], "return": 0.042, "vol": 0.038, "dd": 0.032},
    "最短持有期型": {"risk": ["R2", "R3"], "return": 0.036, "vol": 0.026, "dd": 0.022},
    "多资产": {"risk": ["R3", "R4"], "return": 0.052, "vol": 0.070, "dd": 0.060},
    "混合类": {"risk": ["R3", "R4"], "return": 0.055, "vol": 0.090, "dd": 0.080},
    "QDII": {"risk": ["R3", "R4", "R5"], "return": 0.058, "vol": 0.120, "dd": 0.105},
    "封闭式": {"risk": ["R2", "R3", "R4"], "return": 0.040, "vol": 0.044, "dd": 0.035},
}


def _holding_days(open_type: str) -> int:
    mapping = {
        "日开": 1,
        "7天": 7,
        "14天": 14,
        "21天": 21,
        "30天": 30,
        "60天": 60,
        "90天": 90,
        "120天": 120,
        "180天": 180,
        "270天": 270,
        "360天": 360,
        "1年封闭": 365,
    }
    return mapping[open_type]


def _benchmark_bounds(product_type: str, rng: random.Random) -> tuple[float, float]:
    base = TYPE_CONFIG[product_type]["return"]
    width = rng.uniform(0.006, 0.018)
    lower = max(0.0, base - width)
    upper = base + width
    return round(lower, 4), round(upper, 4)


def _status(annual_return: float, lower: float, upper: float) -> str:
    if annual_return < lower:
        return "below_lower"
    if annual_return > upper:
        return "above_upper"
    return "in_range"


def _percentile(values: list[float], value: float, higher_is_better: bool = True) -> float:
    if not values:
        return 0.5
    if higher_is_better:
        return sum(1 for item in values if item <= value) / len(values)
    return sum(1 for item in values if item >= value) / len(values)


def _make_products(rng: random.Random) -> list[dict[str, object]]:
    products = []
    for idx in range(PRODUCT_COUNT):
        product_type = PRODUCT_TYPES[idx % len(PRODUCT_TYPES)]
        cfg = TYPE_CONFIG[product_type]
        open_type = OPEN_TYPES[idx % len(OPEN_TYPES)]
        inception = date(2022, 1, 7) + timedelta(days=7 * rng.randint(0, 120))
        code = f"WP{idx + 1:04d}"
        products.append(
            {
                "product_code": code,
                "product_name": f"{rng.choice(SERIES)}{product_type}样例{idx + 1:03d}",
                "product_series": rng.choice(SERIES),
                "product_type": product_type,
                "channel": CHANNELS[idx % len(CHANNELS)],
                "risk_level": rng.choice(cfg["risk"]),
                "open_type": open_type,
                "holding_period_days": _holding_days(open_type),
                "inception_date": inception,
                "base_return": cfg["return"] + rng.uniform(-0.01, 0.012),
                "base_vol": cfg["vol"] * rng.uniform(0.75, 1.35),
                "base_dd": cfg["dd"] * rng.uniform(0.70, 1.50),
                "base_scale": rng.uniform(0.6, 22.0) * (1.6 if product_type in {"现金管理", "纯固收"} else 1.0),
            }
        )
    return products


def _scale_history(products: list[dict[str, object]], rng: random.Random) -> list[dict[str, object]]:
    rows = []
    for product in products:
        scale = float(product["base_scale"])
        for report_date in REPORT_DATES:
            drift = rng.gauss(0.015, 0.12)
            scale = max(0.05, scale + drift)
            rows.append(
                {
                    "report_date": report_date.isoformat(),
                    "product_code": product["product_code"],
                    "product_scale_bn": round(scale, 4),
                    "scale_evidence_id": f"ev_scale_{product['product_code']}_{report_date:%Y%m%d}",
                }
            )
    return rows


def _nav_history(products: list[dict[str, object]], rng: random.Random) -> list[dict[str, object]]:
    rows = []
    start = REPORT_DATES[0] - timedelta(days=7 * 48)
    weeks = 58
    for product in products:
        nav = 1.0 + rng.uniform(-0.005, 0.005)
        bench = 1.0
        weekly_mean = float(product["base_return"]) / 52
        weekly_vol = float(product["base_vol"]) / math.sqrt(52)
        for week in range(weeks):
            dt = start + timedelta(days=7 * week)
            if week > 0:
                shock = -abs(rng.gauss(float(product["base_dd"]) / 4, float(product["base_dd"]) / 8)) if rng.random() < 0.03 else 0.0
                nav = max(0.72, nav * (1 + rng.gauss(weekly_mean, weekly_vol) + shock))
                bench = max(0.78, bench * (1 + rng.gauss(weekly_mean * 0.85, weekly_vol * 0.65) + shock * 0.4))
            rows.append(
                {
                    "product_code": product["product_code"],
                    "nav_date": dt.isoformat(),
                    "nav": round(nav, 6),
                    "benchmark_nav": round(bench, 6),
                    "nav_evidence_id": f"ev_weekly_nav_{product['product_code']}_{dt:%Y%m%d}",
                }
            )
    return rows


def _nav_metrics(nav_rows: list[dict[str, object]], product_code: str, report_date: date) -> dict[str, float]:
    rows = [row for row in nav_rows if row["product_code"] == product_code and date.fromisoformat(str(row["nav_date"])) <= report_date]
    rows = rows[-53:]
    values = [float(row["nav"]) for row in rows]
    if len(values) < 2:
        return {"return_1m": 0, "return_3m": 0, "return_6m": 0, "return_1y": 0, "return_ytd": 0, "max_drawdown": 0, "volatility": 0, "sharpe": 0, "latest_nav": values[-1] if values else 1.0, "daily_nav_change_bp": 0}
    returns = [(values[i] / values[i - 1] - 1) for i in range(1, len(values))]
    running_max = []
    current = values[0]
    for value in values:
        current = max(current, value)
        running_max.append(current)
    max_dd = min(value / high - 1 for value, high in zip(values, running_max))
    vol = (sum((r - sum(returns) / len(returns)) ** 2 for r in returns) / max(len(returns) - 1, 1)) ** 0.5 * math.sqrt(52)
    ann = (values[-1] / values[0]) ** (52 / max(len(values) - 1, 1)) - 1
    sharpe = (ann - 0.02) / vol if vol else 0

    def trailing(weeks: int) -> float:
        if len(values) <= weeks:
            return values[-1] / values[0] - 1
        return values[-1] / values[-weeks - 1] - 1

    return {
        "latest_nav": values[-1],
        "daily_nav_change_bp": returns[-1] * 10000 / 5,
        "since_inception_annual_return": ann,
        "return_1m": trailing(4),
        "return_3m": trailing(13),
        "return_6m": trailing(26),
        "return_1y": trailing(52),
        "return_ytd": values[-1] / values[max(0, len(values) - min(len(values), 8))] - 1,
        "max_drawdown": max_dd,
        "volatility": vol,
        "sharpe": sharpe,
    }


def _snapshot(products: list[dict[str, object]], scale_rows: list[dict[str, object]], nav_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    scale_map = {(row["product_code"], row["report_date"]): float(row["product_scale_bn"]) for row in scale_rows}
    rows = []
    for report_date in REPORT_DATES:
        for product in products:
            code = str(product["product_code"])
            scale = scale_map[(code, report_date.isoformat())]
            prev_week = scale_map.get((code, (report_date - timedelta(days=7)).isoformat()), scale)
            prev_month = scale_map.get((code, (report_date - timedelta(days=28)).isoformat()), scale)
            metrics = _nav_metrics(nav_rows, code, report_date)
            lower, upper = _benchmark_bounds(str(product["product_type"]), random.Random(hash((code, report_date.isoformat())) & 0xFFFF))
            status = _status(metrics["since_inception_annual_return"], lower, upper)
            running_days = max(1, (report_date - product["inception_date"]).days)
            rows.append(
                {
                    "report_date": report_date.isoformat(),
                    "product_code": code,
                    "product_name": product["product_name"],
                    "product_series": product["product_series"],
                    "product_type": product["product_type"],
                    "channel": product["channel"],
                    "risk_level": product["risk_level"],
                    "open_type": product["open_type"],
                    "holding_period_days": product["holding_period_days"],
                    "inception_date": product["inception_date"].isoformat(),
                    "running_days": running_days,
                    "product_scale_bn": round(scale, 4),
                    "scale_wow_bn": round(scale - prev_week, 4),
                    "scale_mom_bn": round(scale - prev_month, 4),
                    "latest_nav": round(metrics["latest_nav"], 6),
                    "daily_nav_change_bp": round(metrics["daily_nav_change_bp"], 2),
                    "since_inception_annual_return": round(metrics["since_inception_annual_return"], 6),
                    "return_1m": round(metrics["return_1m"], 6),
                    "return_3m": round(metrics["return_3m"], 6),
                    "return_6m": round(metrics["return_6m"], 6),
                    "return_1y": round(metrics["return_1y"], 6),
                    "return_ytd": round(metrics["return_ytd"], 6),
                    "max_drawdown": round(metrics["max_drawdown"], 6),
                    "volatility": round(metrics["volatility"], 6),
                    "sharpe": round(metrics["sharpe"], 6),
                    "benchmark_lower": lower,
                    "benchmark_upper": upper,
                    "benchmark_status": status,
                    "evidence_id": f"ev_snapshot_{code}_{report_date:%Y%m%d}",
                }
            )
    return rows


def _benchmark_status(snapshot_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "report_date": row["report_date"],
            "product_code": row["product_code"],
            "benchmark_lower": row["benchmark_lower"],
            "benchmark_upper": row["benchmark_upper"],
            "actual_return": row["since_inception_annual_return"],
            "benchmark_status": row["benchmark_status"],
            "evidence_id": f"ev_benchmark_status_{row['product_code']}_{str(row['report_date']).replace('-', '')}",
        }
        for row in snapshot_rows
    ]


def _market_issuance(rng: random.Random) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    weekly = []
    details = []
    for report_date in REPORT_DATES:
        total = rng.randint(45, 96)
        by_nature = {nature: rng.randint(3, 25) for nature in INVESTMENT_NATURE}
        by_term = {term: rng.randint(1, 14) for term in OPEN_TYPES}
        weekly.append(
            {
                "report_date": report_date.isoformat(),
                "new_product_count": total,
                "by_investment_nature_json": json.dumps(by_nature, ensure_ascii=False),
                "by_duration_json": json.dumps(by_term, ensure_ascii=False),
                "benchmark_lower_avg": round(rng.uniform(0.018, 0.032), 4),
                "benchmark_upper_avg": round(rng.uniform(0.032, 0.058), 4),
                "evidence_id": f"ev_market_issuance_{report_date:%Y%m%d}",
            }
        )
        for idx in range(min(total, 28)):
            product_type = rng.choice(PRODUCT_TYPES)
            lower, upper = _benchmark_bounds(product_type, rng)
            details.append(
                {
                    "report_date": report_date.isoformat(),
                    "new_product_code": f"MN{report_date:%m%d}{idx + 1:03d}",
                    "new_product_name": f"{product_type}新发样例{idx + 1:03d}",
                    "issuer_type": rng.choice(["银行理财子", "公募基金", "券商资管", "保险资管"]),
                    "investment_nature": rng.choice(INVESTMENT_NATURE),
                    "duration_bucket": rng.choice(OPEN_TYPES),
                    "risk_level": rng.choice(RISK_LEVELS),
                    "benchmark_lower": lower,
                    "benchmark_upper": upper,
                    "evidence_id": f"ev_market_new_{report_date:%Y%m%d}_{idx + 1:03d}",
                }
            )
    return weekly, details


def _peer_universe(snapshot_rows: list[dict[str, object]], rng: random.Random) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    latest = [row for row in snapshot_rows if row["report_date"] == REPORT_DATES[-1].isoformat()]
    peers = []
    metrics = []
    channels = []
    top = []
    for idx in range(PEER_COUNT):
        anchor = latest[idx % len(latest)]
        ptype = str(anchor["product_type"])
        channel = CHANNELS[idx % len(CHANNELS)]
        ret = float(anchor["return_3m"]) + rng.gauss(0, 0.012)
        dd = float(anchor["max_drawdown"]) - abs(rng.gauss(0, 0.008))
        vol = max(0.001, float(anchor["volatility"]) * rng.uniform(0.7, 1.5))
        sharpe = (ret * 4 - 0.02) / vol if vol else 0
        peer_code = f"PR{idx + 1:04d}"
        peers.append(
            {
                "peer_product_code": peer_code,
                "peer_product_name": f"{ptype}同业样例{idx + 1:03d}",
                "product_type": ptype,
                "channel": channel,
                "risk_level": anchor["risk_level"],
                "open_type": anchor["open_type"],
                "holding_period_days": anchor["holding_period_days"],
                "evidence_id": f"ev_peer_universe_{peer_code}",
            }
        )
        metrics.append(
            {
                "peer_product_code": peer_code,
                "report_date": REPORT_DATES[-1].isoformat(),
                "return_1m": round(ret / 3, 6),
                "return_3m": round(ret, 6),
                "return_6m": round(ret * 1.8, 6),
                "max_drawdown": round(dd, 6),
                "volatility": round(vol, 6),
                "sharpe": round(sharpe, 6),
                "return_percentile": 0.0,
                "drawdown_percentile": 0.0,
                "evidence_id": f"ev_peer_metric_{peer_code}",
            }
        )
        channels.append(
            {
                "channel": channel,
                "product_type": ptype,
                "peer_product_code": peer_code,
                "return_3m": round(ret, 6),
                "scale_bn": round(rng.uniform(0.2, 30), 4),
                "evidence_id": f"ev_channel_peer_{peer_code}",
            }
        )

    by_type: dict[str, list[dict[str, object]]] = {}
    for row in metrics:
        ptype = next(peer["product_type"] for peer in peers if peer["peer_product_code"] == row["peer_product_code"])
        by_type.setdefault(ptype, []).append(row)
    for ptype, rows in by_type.items():
        returns = [float(row["return_3m"]) for row in rows]
        dds = [float(row["max_drawdown"]) for row in rows]
        for row in rows:
            row["return_percentile"] = round(_percentile(returns, float(row["return_3m"]), True), 4)
            row["drawdown_percentile"] = round(_percentile(dds, float(row["max_drawdown"]), True), 4)
        leaders = sorted(rows, key=lambda item: (float(item["return_percentile"]), float(item["sharpe"])), reverse=True)[:8]
        for rank, item in enumerate(leaders, 1):
            peer = next(peer for peer in peers if peer["peer_product_code"] == item["peer_product_code"])
            top.append(
                {
                    "report_date": REPORT_DATES[-1].isoformat(),
                    "rank": rank,
                    "peer_product_code": item["peer_product_code"],
                    "peer_product_name": peer["peer_product_name"],
                    "product_type": ptype,
                    "return_3m": item["return_3m"],
                    "return_percentile": item["return_percentile"],
                    "max_drawdown": item["max_drawdown"],
                    "sharpe": item["sharpe"],
                    "tracking_reason": "同类收益分位和风险调整指标靠前，用于周报跟踪样例。",
                    "evidence_id": f"ev_top_peer_{item['peer_product_code']}",
                }
            )
    return peers, metrics, channels, top


def _dpo_pairs(snapshot_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    latest = [row for row in snapshot_rows if row["report_date"] == REPORT_DATES[-1].isoformat()]
    pairs = []
    for idx, row in enumerate(latest[:24], 1):
        evidence = row["evidence_id"]
        pairs.append(
            {
                "id": f"dpo_weekly_{idx:03d}",
                "prompt": {
                    "task": "根据 tool outputs 生成资管产品周报摘要。",
                    "tool_output": {
                        "product_code": row["product_code"],
                        "product_name": row["product_name"],
                        "scale_wow_bn": row["scale_wow_bn"],
                        "return_3m": row["return_3m"],
                        "benchmark_status": row["benchmark_status"],
                        "max_drawdown": row["max_drawdown"],
                        "evidence_id": evidence,
                    },
                },
                "chosen": (
                    f"{row['product_name']} 本周规模变化 {row['scale_wow_bn']} 亿元，"
                    f"近3个月收益 {float(row['return_3m']) * 100:.2f}%，基准状态为 {row['benchmark_status']}；"
                    f"最大回撤 {float(row['max_drawdown']) * 100:.2f}%，需结合渠道和同类分位继续观察。"
                    f"[evidence_id={evidence}]"
                ),
                "rejected": (
                    f"{row['product_name']} 本周表现较好，但缺少数字来源、风险提示和 evidence_id，"
                    "并把阶段性表现外推为未来表现。"
                ),
                "reject_reason": "缺少 evidence_id、风险提示不足，且存在未来表现外推。",
            }
        )
    return pairs


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"no rows for {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rng = random.Random(SEED)
    products = _make_products(rng)
    scale_rows = _scale_history(products, rng)
    nav_rows = _nav_history(products, rng)
    snapshot_rows = _snapshot(products, scale_rows, nav_rows)
    benchmark_rows = _benchmark_status(snapshot_rows)
    market_weekly, market_details = _market_issuance(rng)
    peers, peer_metrics, channel_peers, top_peers = _peer_universe(snapshot_rows, rng)
    dpo_pairs = _dpo_pairs(snapshot_rows)

    _write_csv(WEEKLY / "product_weekly_snapshot.csv", snapshot_rows)
    _write_csv(WEEKLY / "product_scale_history.csv", scale_rows)
    _write_csv(WEEKLY / "product_nav_weekly.csv", nav_rows)
    _write_csv(WEEKLY / "product_benchmark_status.csv", benchmark_rows)
    _write_csv(WEEKLY / "market_issuance_weekly.csv", market_weekly)
    _write_csv(WEEKLY / "market_new_product_detail.csv", market_details)
    _write_csv(BENCHMARK / "peer_product_universe.csv", peers)
    _write_csv(BENCHMARK / "peer_product_metrics.csv", peer_metrics)
    _write_csv(BENCHMARK / "channel_peer_universe.csv", channel_peers)
    _write_csv(BENCHMARK / "top_peer_products.csv", top_peers)

    DPO.mkdir(parents=True, exist_ok=True)
    with (DPO / "weekly_report_preference_pairs.jsonl").open("w", encoding="utf-8") as handle:
        for pair in dpo_pairs:
            handle.write(json.dumps(pair, ensure_ascii=False) + "\n")

    print(
        f"generated weekly snapshots={len(snapshot_rows)}, nav={len(nav_rows)}, "
        f"peer_metrics={len(peer_metrics)}, dpo_pairs={len(dpo_pairs)}"
    )


if __name__ == "__main__":
    main()
