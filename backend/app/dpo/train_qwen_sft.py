from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT_DATA = ROOT / "data" / "dpo" / "report_preference_pairs.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run SFT hook for DPO-aligned weekly-report adapters.")
    parser.add_argument("--dataset", default=os.getenv("SFT_REPORT_DATASET", str(DEFAULT_REPORT_DATA)))
    parser.add_argument("--base-model", default=os.getenv("QWEN_SFT_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct"))
    parser.add_argument("--adapter-output", default=os.getenv("QWEN_SFT_ADAPTER_OUTPUT", ""))
    parser.add_argument("--enable-training", default=os.getenv("ENABLE_SFT_TRAINING", "false"))
    args = parser.parse_args()
    path = Path(args.dataset)
    pair_count = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()) if path.exists() else 0
    enabled = str(args.enable_training).lower() == "true"
    print(
        json.dumps(
            {
                "training_status": "not_trained" if not enabled else "blocked_in_demo_environment",
                "mode": "dry_run" if not enabled else "training_requested",
                "base_model": args.base_model,
                "adapter_output_configured": bool(args.adapter_output),
                "train_pairs": pair_count,
                "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                "note": "SFT is optional baseline only; no weights or private data are shipped.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

