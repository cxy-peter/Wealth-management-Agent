"""LinUCB contextual bandit policy for workflow routing."""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.app.optimization.context_features import FEATURE_NAMES, vectorize_context
from backend.app.optimization.router_policy import ACTIONS

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators

disable_optional_pandas_accelerators()

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STATE_PATH = ROOT / "data" / "router_policy_state.json"


@dataclass
class LinUCBPolicy:
    alpha: float = 0.7
    ridge_lambda: float = 1.0
    seed: int = 42
    actions: list[str] = field(default_factory=lambda: list(ACTIONS))
    feature_names: list[str] = field(default_factory=lambda: list(FEATURE_NAMES))
    A: dict[str, np.ndarray] = field(init=False)
    b: dict[str, np.ndarray] = field(init=False)

    def __post_init__(self) -> None:
        random.seed(self.seed)
        dim = len(self.feature_names)
        self.A = {action: np.eye(dim) * self.ridge_lambda for action in self.actions}
        self.b = {action: np.zeros(dim) for action in self.actions}

    def _x(self, context: dict[str, float]) -> np.ndarray:
        return np.asarray(vectorize_context(context), dtype=float)

    def action_scores(self, context: dict[str, float]) -> dict[str, float]:
        x = self._x(context)
        scores: dict[str, float] = {}
        for action in self.actions:
            inv_a = np.linalg.inv(self.A[action])
            theta = inv_a @ self.b[action]
            exploration = self.alpha * np.sqrt(float(x.T @ inv_a @ x))
            scores[action] = float(theta.T @ x + exploration)
        return scores

    def select_action(self, context: dict[str, float]) -> tuple[str, dict[str, float]]:
        scores = self.action_scores(context)
        best = max(self.actions, key=lambda action: (scores[action], -self.actions.index(action)))
        return best, scores

    def update(self, action: str, context: dict[str, float], reward: float) -> None:
        if action not in self.actions:
            raise ValueError(f"unknown action: {action}")
        x = self._x(context)
        self.A[action] = self.A[action] + np.outer(x, x)
        self.b[action] = self.b[action] + float(reward) * x

    def snapshot(self) -> dict[str, Any]:
        return {
            "policy": "linucb_contextual_bandit",
            "alpha": self.alpha,
            "ridge_lambda": self.ridge_lambda,
            "seed": self.seed,
            "actions": self.actions,
            "feature_names": self.feature_names,
            "A": {action: matrix.tolist() for action, matrix in self.A.items()},
            "b": {action: vector.tolist() for action, vector in self.b.items()},
        }

    def save(self, path: str | Path = DEFAULT_STATE_PATH) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.snapshot(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: str | Path = DEFAULT_STATE_PATH) -> "LinUCBPolicy":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        policy = cls(
            alpha=float(payload.get("alpha", 0.7)),
            ridge_lambda=float(payload.get("ridge_lambda", 1.0)),
            seed=int(payload.get("seed", 42)),
            actions=list(payload.get("actions", ACTIONS)),
            feature_names=list(payload.get("feature_names", FEATURE_NAMES)),
        )
        policy.A = {action: np.asarray(matrix, dtype=float) for action, matrix in payload.get("A", {}).items()}
        policy.b = {action: np.asarray(vector, dtype=float) for action, vector in payload.get("b", {}).items()}
        return policy
