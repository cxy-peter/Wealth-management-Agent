from __future__ import annotations

import random


def lifecycle_status(current_status: str, rng: random.Random) -> str:
    if current_status == "到期":
        return "到期"
    return "到期" if rng.random() < 0.015 else current_status or "存续"

