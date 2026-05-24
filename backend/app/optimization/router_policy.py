"""Simple epsilon-greedy routing policy."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

ACTIONS = ["fast_snapshot", "standard_research", "deep_review", "product_compare", "risk_only"]

ACTION_TO_REQUEST = {
    "fast_snapshot": {"analysis_type": "fast", "risk_preference": "balanced"},
    "standard_research": {"analysis_type": "full", "risk_preference": "balanced"},
    "deep_review": {"analysis_type": "deep", "risk_preference": "strict"},
    "product_compare": {"analysis_type": "product", "risk_preference": "balanced"},
    "risk_only": {"analysis_type": "risk", "risk_preference": "conservative"},
}


@dataclass
class EpsilonGreedyRouter:
    epsilon: float = 0.2
    seed: int = 42
    values: dict[str, float] = field(default_factory=lambda: {action: 0.0 for action in ACTIONS})
    counts: dict[str, int] = field(default_factory=lambda: {action: 0 for action in ACTIONS})

    def __post_init__(self) -> None:
        self._random = random.Random(self.seed)

    def select_action(self) -> str:
        untried = [action for action, count in self.counts.items() if count == 0]
        if untried:
            return untried[0]
        if self._random.random() < self.epsilon:
            return self._random.choice(ACTIONS)
        return max(ACTIONS, key=lambda action: self.values[action])

    def update(self, action: str, reward: float) -> None:
        self.counts[action] += 1
        count = self.counts[action]
        old = self.values[action]
        self.values[action] = old + (reward - old) / count

    def snapshot(self) -> dict:
        return {"epsilon": self.epsilon, "values": self.values, "counts": self.counts}
