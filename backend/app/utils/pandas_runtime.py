"""Runtime guard for pandas optional acceleration modules.

Some local Anaconda environments keep old binary builds of optional pandas
accelerators. The demo does not need them, so we disable them before pandas is
imported to avoid noisy import traces while preserving normal pandas behavior.
"""
from __future__ import annotations

import os
import sys


def disable_optional_pandas_accelerators() -> None:
    os.environ.setdefault("PANDAS_USE_NUMEXPR", "0")
    for module_name in ("numexpr", "bottleneck"):
        if module_name not in sys.modules:
            sys.modules[module_name] = None
