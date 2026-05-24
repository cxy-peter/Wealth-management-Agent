"""Generate a synthetic-but-realistic product universe for local demos.

The generated data is entirely synthetic. It is intended for product research,
benchmarking, routing, and audit demos without relying on internal products,
client data, credentials, or live market feeds.
"""
from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

SEED = 20260524
PRODUCT_COUNT = 108

ASSET_CLASSES = [
    "现金管理",
    "纯债固收",
    "固收+",
    "多资产",
    "权益增强",
    "量化对冲",
    "商品/黄金",
    "QDII/全球配置",
    "养老目标/FOF",
]
CHANNELS = ["银行渠道", "线上渠道", "机构渠道", "券商渠道", "私行渠道"]
ISSUER_TYPES = ["银行理财子", "公募基金", "券商资管", "信托资管", "保险资管"]
PRODUCT_TYPES = ["开放式净值型", "定开净值型", "封闭净值型"]
LIQUIDITY_TYPES = ["每日开放", "每周开放", "每月开放", "每季开放", "持有期"]
DURATION_BUCKETS = ["0-3M", "3-6M", "6-12M", "1-3Y", "3Y+"]
CREDIT_FOCUS = ["高等级信用债", "利率债为主", "中高等级信用债", "可转债/信用混合", "非信用主导"]
STATUS = ["存续", "募集期", "观察期"]
RISK_LEVELS = ["R1", "R2", "R3", "R4", "R5"]
RISK_EVENT_TYPES = [
    "信用利差走阔",
    "权益回撤",
    "久期风险",
    "流动性风险",
    "汇率波动",
    "商品价格波动",
    "监管/合规提示",
    "估值波动",
]

ASSET_CONFIG = {
    "现金管理": {"risk": ["R1", "R2"], "strategy": ["现金管理", "流动性管理"], "mean": 0.018, "vol": 0.006},
    "纯债固收": {"risk": ["R2", "R3"], "strategy": ["利率债", "信用债", "短债"], "mean": 0.030, "vol": 0.018},
    "固收+": {"risk": ["R2", "R3", "R4"], "strategy": ["债券增强", "可转债增强", "股债平衡"], "mean": 0.042, "vol": 0.040},
    "多资产": {"risk": ["R3", "R4"], "strategy": ["股债商多资产", "风险平价", "目标波动"], "mean": 0.055, "vol": 0.075},
    "权益增强": {"risk": ["R4", "R5"], "strategy": ["指数增强", "主动权益", "红利增强"], "mean": 0.070, "vol": 0.145},
    "量化对冲": {"risk": ["R3", "R4"], "strategy": ["市场中性", "CTA", "多策略对冲"], "mean": 0.046, "vol": 0.065},
    "商品/黄金": {"risk": ["R3", "R4"], "strategy": ["黄金ETF联接", "商品趋势", "贵金属配置"], "mean": 0.040, "vol": 0.110},
    "QDII/全球配置": {"risk": ["R3", "R4", "R5"], "strategy": ["全球债券", "全球权益", "全球多资产"], "mean": 0.052, "vol": 0.125},
    "养老目标/FOF": {"risk": ["R2", "R3", "R4"], "strategy": ["目标日期", "目标风险", "FOF稳健"], "mean": 0.043, "vol": 0.060},
}

RISK_VOL_MULTIPLIER = {"R1": 0.55, "R2": 0.80, "R3": 1.00, "R4": 1.35, "R5": 1.80}
RISK_MEAN_SHIFT = {"R1": -0.008, "R2": -0.003, "R3": 0.000, "R4": 0.006, "R5": 0.010}


def _weights(asset_class: str, rng: random.Random) -> dict[str, float]:
    if asset_class == "现金管理":
        base = (0.10, 0.00, 0.88, 0.02)
    elif asset_class == "纯债固收":
        base = (0.86, 0.00, 0.12, 0.02)
    elif asset_class == "固收+":
        base = (0.72, 0.14, 0.08, 0.06)
    elif asset_class == "多资产":
        base = (0.44, 0.28, 0.12, 0.16)
    elif asset_class == "权益增强":
        base = (0.10, 0.78, 0.04, 0.08)
    elif asset_class == "量化对冲":
        base = (0.34, 0.34, 0.12, 0.20)
    elif asset_class == "商品/黄金":
        base = (0.18, 0.10, 0.08, 0.64)
    elif asset_class == "QDII/全球配置":
        base = (0.22, 0.42, 0.08, 0.28)
    else:
        base = (0.48, 0.26, 0.10, 0.16)
    noisy = [max(0.0, item + rng.uniform(-0.035, 0.035)) for item in base]
    total = sum(noisy) or 1.0
    return {
        "bond_weight": round(noisy[0] / total, 4),
        "equity_weight": round(noisy[1] / total, 4),
        "cash_weight": round(noisy[2] / total, 4),
        "alternative_weight": round(noisy[3] / total, 4),
    }


def _duration_days(bucket: str, rng: random.Random) -> int:
    ranges = {
        "0-3M": (30, 90),
        "3-6M": (91, 180),
        "6-12M": (181, 365),
        "1-3Y": (366, 1095),
        "3Y+": (1096, 1825),
    }
    low, high = ranges[bucket]
    return rng.randint(low, high)


def _benchmark(asset_class: str) -> str:
    mapping = {
        "现金管理": "7日年化现金管理样例基准",
        "纯债固收": "中债综合财富样例基准",
        "固收+": "固收增强复合样例基准",
        "多资产": "股债商多资产样例基准",
        "权益增强": "宽基权益增强样例基准",
        "量化对冲": "市场中性策略样例基准",
        "商品/黄金": "黄金商品篮子样例基准",
        "QDII/全球配置": "全球配置样例基准",
        "养老目标/FOF": "养老FOF复合样例基准",
    }
    return mapping[asset_class]


def _make_catalog(rng: random.Random) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx in range(PRODUCT_COUNT):
        asset_class = ASSET_CLASSES[idx % len(ASSET_CLASSES)]
        cfg = ASSET_CONFIG[asset_class]
        risk_level = rng.choice(cfg["risk"])
        duration_bucket = rng.choice(DURATION_BUCKETS)
        liquidity_type = rng.choice(LIQUIDITY_TYPES)
        strategy = rng.choice(cfg["strategy"])
        product_id = f"SP{idx + 1:04d}"
        product_name = f"{asset_class}{strategy}样例{idx + 1:03d}"
        rows.append(
            {
                "product_id": product_id,
                "product_name": product_name,
                "issuer_type": rng.choice(ISSUER_TYPES),
                "asset_class": asset_class,
                "strategy_type": strategy,
                "channel": rng.choice(CHANNELS),
                "risk_level": risk_level,
                "product_type": rng.choice(PRODUCT_TYPES),
                "liquidity_type": liquidity_type,
                "duration_days": _duration_days(duration_bucket, rng),
                "benchmark": _benchmark(asset_class),
                "fee_rate": round(rng.uniform(0.001, 0.018) * (1.0 + 0.08 * RISK_LEVELS.index(risk_level)), 4),
                "min_holding_amount": rng.choice([1, 1000, 10000, 50000, 100000, 300000, 1000000]),
                **_weights(asset_class, rng),
                "credit_rating_focus": rng.choice(CREDIT_FOCUS),
                "duration_bucket": duration_bucket,
                "open_date": (date(2023, 1, 6) + timedelta(days=7 * rng.randint(0, 70))).isoformat(),
                "status": rng.choice(STATUS),
            }
        )
    return rows


def _weekly_nav(row: dict[str, object], rng: random.Random) -> list[dict[str, object]]:
    asset_class = str(row["asset_class"])
    risk_level = str(row["risk_level"])
    cfg = ASSET_CONFIG[asset_class]
    weeks = rng.randint(26, 52)
    start = date(2025, 1, 3) - timedelta(days=7 * (weeks - 1))
    nav = 1.0 + rng.uniform(-0.006, 0.006)
    benchmark_nav = 1.0
    annual_mean = cfg["mean"] + RISK_MEAN_SHIFT[risk_level] + rng.uniform(-0.015, 0.015)
    annual_vol = cfg["vol"] * RISK_VOL_MULTIPLIER[risk_level] * rng.uniform(0.80, 1.25)
    weekly_mean = annual_mean / 52.0
    weekly_vol = annual_vol / math.sqrt(52.0)
    benchmark_mean = (cfg["mean"] - 0.004) / 52.0
    benchmark_vol = max(0.003, weekly_vol * 0.75)
    shock_prob = {"R1": 0.01, "R2": 0.02, "R3": 0.035, "R4": 0.055, "R5": 0.075}[risk_level]
    shock_scale = {"R1": 0.004, "R2": 0.010, "R3": 0.022, "R4": 0.040, "R5": 0.070}[risk_level]
    records = []
    for week in range(weeks):
        if week > 0:
            shock = -abs(rng.gauss(shock_scale, shock_scale * 0.35)) if rng.random() < shock_prob else 0.0
            weekly_return = rng.gauss(weekly_mean, weekly_vol) + shock
            benchmark_return = rng.gauss(benchmark_mean, benchmark_vol) + shock * 0.55
            nav = max(0.65, nav * (1.0 + weekly_return))
            benchmark_nav = max(0.70, benchmark_nav * (1.0 + benchmark_return))
        records.append(
            {
                "product_id": row["product_id"],
                "date": (start + timedelta(days=7 * week)).isoformat(),
                "nav": round(nav, 6),
                "benchmark_nav": round(benchmark_nav, 6),
                "evidence_id": f"ev_product_nav_{row['product_id']}_{week + 1:02d}",
            }
        )
    return records


def _risk_events(row: dict[str, object], nav_rows: list[dict[str, object]], rng: random.Random) -> list[dict[str, object]]:
    risk_level = str(row["risk_level"])
    count = rng.randint(0, 1) if risk_level in {"R1", "R2"} else rng.randint(1, 3)
    if risk_level == "R5":
        count = rng.randint(2, 4)
    event_types = {
        "现金管理": ["流动性风险", "监管/合规提示", "估值波动"],
        "纯债固收": ["信用利差走阔", "久期风险", "估值波动"],
        "固收+": ["信用利差走阔", "权益回撤", "久期风险", "估值波动"],
        "多资产": ["权益回撤", "商品价格波动", "估值波动"],
        "权益增强": ["权益回撤", "估值波动", "监管/合规提示"],
        "量化对冲": ["流动性风险", "权益回撤", "估值波动"],
        "商品/黄金": ["商品价格波动", "汇率波动", "估值波动"],
        "QDII/全球配置": ["汇率波动", "权益回撤", "流动性风险"],
        "养老目标/FOF": ["权益回撤", "估值波动", "久期风险"],
    }.get(str(row["asset_class"]), RISK_EVENT_TYPES)
    rows = []
    for idx in range(count):
        nav_point = rng.choice(nav_rows)
        event_type = rng.choice(event_types)
        severity = min(5, max(1, RISK_LEVELS.index(risk_level) + 1 + rng.choice([-1, 0, 0, 1])))
        rows.append(
            {
                "product_id": row["product_id"],
                "event_date": nav_point["date"],
                "event_type": event_type,
                "severity": severity,
                "event_summary": f"{event_type}样例事件，供投研风险摘要和证据追溯使用。",
                "evidence_id": f"ev_product_event_{row['product_id']}_{idx + 1:02d}",
            }
        )
    return rows


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
    catalog = _make_catalog(rng)
    nav_rows: list[dict[str, object]] = []
    event_rows: list[dict[str, object]] = []
    for row in catalog:
        product_nav = _weekly_nav(row, rng)
        nav_rows.extend(product_nav)
        event_rows.extend(_risk_events(row, product_nav, rng))

    _write_csv(DATA_DIR / "sample_product_catalog.csv", catalog)
    _write_csv(DATA_DIR / "sample_product_nav.csv", nav_rows)
    _write_csv(DATA_DIR / "sample_product_risk_events.csv", event_rows)
    print(
        f"generated {len(catalog)} products, {len(nav_rows)} nav rows, "
        f"{len(event_rows)} risk events under {DATA_DIR}"
    )


if __name__ == "__main__":
    main()
