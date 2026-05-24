from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.dpo.dpo_dataset_validator import validate_dpo_dataset

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_REPORT_DATA = ROOT / "data" / "dpo" / "report_preference_pairs.jsonl"
DEFAULT_PLANNER_DATA = ROOT / "data" / "dpo" / "planner_preference_pairs.jsonl"


def _dry_run_payload(args: argparse.Namespace, report_validation: dict[str, Any], planner_pairs: int) -> dict[str, Any]:
    return {
        "training_status": "not_trained",
        "mode": "dry_run",
        "training_enabled": False,
        "base_model": args.base_model,
        "adapter_type": "LoRA" if not args.qlora else "QLoRA",
        "lora_rank": args.lora_rank,
        "target_modules": args.target_modules.split(","),
        "train_pairs": report_validation["pair_count"] + planner_pairs,
        "eval_pairs": 0,
        "beta": args.beta,
        "learning_rate": args.learning_rate,
        "train_loss": None,
        "eval_loss": None,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "note": "Set ENABLE_DPO_TRAINING=true and provide model/data/output paths to run TRL DPOTrainer outside the demo.",
        "report_dataset_validation": report_validation,
        "planner_pair_count": planner_pairs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run or train Qwen DPO adapters for weekly-report alignment.")
    parser.add_argument("--report-dataset", default=os.getenv("DPO_REPORT_DATASET", str(DEFAULT_REPORT_DATA)))
    parser.add_argument("--planner-dataset", default=os.getenv("DPO_PLANNER_DATASET", str(DEFAULT_PLANNER_DATA)))
    parser.add_argument("--base-model", default=os.getenv("QWEN_DPO_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct"))
    parser.add_argument("--adapter-output", default=os.getenv("QWEN_DPO_ADAPTER_OUTPUT", ""))
    parser.add_argument("--lora-rank", type=int, default=int(os.getenv("QWEN_DPO_LORA_RANK", "8")))
    parser.add_argument("--target-modules", default=os.getenv("QWEN_DPO_TARGET_MODULES", "q_proj,v_proj"))
    parser.add_argument("--beta", type=float, default=float(os.getenv("QWEN_DPO_BETA", "0.1")))
    parser.add_argument("--learning-rate", type=float, default=float(os.getenv("QWEN_DPO_LR", "0.00005")))
    parser.add_argument("--qlora", action="store_true")
    parser.add_argument("--enable-training", default=os.getenv("ENABLE_DPO_TRAINING", "false"))
    args = parser.parse_args()

    report_validation = validate_dpo_dataset(args.report_dataset)
    planner_pairs = 0
    planner_path = Path(args.planner_dataset)
    if planner_path.exists():
        planner_pairs = sum(1 for line in planner_path.read_text(encoding="utf-8").splitlines() if line.strip())

    if str(args.enable_training).lower() != "true":
        print(json.dumps(_dry_run_payload(args, report_validation, planner_pairs), ensure_ascii=False, indent=2))
        return

    payload = _dry_run_payload(args, report_validation, planner_pairs)
    payload["training_enabled"] = True
    payload["mode"] = "training_requested"
    if not report_validation["valid"]:
        payload["training_status"] = "blocked_by_dataset_validation"
    elif not args.adapter_output:
        payload["training_status"] = "blocked_by_missing_adapter_output"
    else:
        payload["training_status"] = "blocked_in_demo_environment"
        payload["note"] = "TRL/PEFT imports are intentionally deferred; install them and run this script in a model-training environment."
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

