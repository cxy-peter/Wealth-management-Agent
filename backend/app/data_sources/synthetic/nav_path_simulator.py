from __future__ import annotations

import random


def simulate_weekly_nav(latest_nav: float, risk_level: str, rng: random.Random) -> float:
    risk_num = int(str(risk_level).replace("R", "") or 2)
    drift = 0.0005 + risk_num * 0.0002
    vol = 0.0015 + risk_num * 0.0014
    return round(max(0.55, float(latest_nav) * (1 + rng.gauss(drift, vol))), 6)

