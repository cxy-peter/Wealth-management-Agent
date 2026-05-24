# Model extension plan

## Current demo

新闻风险与情绪默认使用 deterministic rule-based fallback。这样可以在无 GPU、无外部接口、无模型文件的机器上稳定运行。

## Qwen LoRA adapter

`backend/app/models/qwen_risk_adapter.py` 提供可选 wrapper：

```python
classifier = QwenRiskClassifier(
    base_model_path="path configured outside the repo",
    adapter_path="path configured outside the repo",
)
classifier.predict(news_text, symbol="600519")
```

输出 schema：

```json
{
  "sentiment_score": 3,
  "risk_score": 2,
  "raw_output": "...",
  "model_mode": "qwen-lora",
  "fallback_required": false
}
```

## Training script requirements

后续如果补训练脚本，应满足：

- 模型路径、数据路径、输出路径全部来自 CLI 参数；
- 不提交模型权重、adapter 权重、私有语料或密钥；
- 保存 adapter metadata：base model、LoRA rank、target modules、训练样本数、验证集指标；
- 推理输出必须经过严格整数解析，解析失败走规则兜底；
- 评测继续写入 `eval/results.json`。
