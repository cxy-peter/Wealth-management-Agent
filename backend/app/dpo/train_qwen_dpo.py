from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from backend.app.dpo.dpo_dataset_validator import DEFAULT_DATASET, validate_dpo_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate or train Qwen DPO adapter for weekly-report style.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--model-path", default=os.getenv("QWEN_MODEL_PATH", ""))
    parser.add_argument("--adapter-output", default=os.getenv("QWEN_DPO_ADAPTER_OUTPUT", ""))
    parser.add_argument("--enable-training", default=os.getenv("ENABLE_DPO_TRAINING", "false"))
    args = parser.parse_args()

    validation = validate_dpo_dataset(args.dataset)
    enable_training = str(args.enable_training).lower() == "true"
    payload = {
        "mode": "validation_only" if not enable_training else "training_requested",
        "training_enabled": enable_training,
        "validation": validation,
        "model_path_configured": bool(args.model_path),
        "adapter_output_configured": bool(args.adapter_output),
    }
    if enable_training:
        if not validation["valid"]:
            payload["training_status"] = "blocked_by_dataset_validation"
        elif not args.model_path or not args.adapter_output:
            payload["training_status"] = "blocked_by_missing_cli_or_env_paths"
        else:
            Path(args.adapter_output).parent.mkdir(parents=True, exist_ok=True)
            payload["training_status"] = "not_executed_in_demo_environment"
            payload["note"] = "LoRA/QLoRA training hook is configured, but model weights are not shipped."
    else:
        payload["training_status"] = "skipped_by_default"
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
