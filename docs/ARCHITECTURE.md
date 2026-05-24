# Architecture

## Runtime Flow

```mermaid
flowchart LR
  API["FastAPI /api/analyze"] --> Planner["planner_agent"]
  Planner --> Graph["LangGraph conditional routing"]
  Graph --> F["fundamental_react_agent"]
  Graph --> T["technical_react_agent"]
  Graph --> V["valuation_react_agent"]
  Graph --> N["news_react_agent"]
  Graph --> P["product_benchmark_agent"]
  F --> G["risk_guardrail_agent"]
  T --> G
  V --> G
  N --> G
  P --> G
  G --> R["report_agent"]
  R --> Verify["verifier_agent"]
  Verify --> H["human_review_agent"]
  Verify --> Done["completed"]
```

## Key Contracts

- Planner 输出 task type、depth、required tools、skipped tools、risk level、human review hint。
- Tool registry 为所有工具返回统一 trace：`tool_call_id`、`tool_name`、`input_args`、`output`、`evidence_ids`、`latency_ms`、`success`、`error_type`。
- Verifier 复核数值、证据、报告结构和 guardrail。
- SQLite 记录 run、agent events、tool calls、report snapshots、eval results、human reviews。

## Fallback Strategy

- 无 API key：ReAct agent 自动走 deterministic tool pipeline。
- 无 GPU 或无模型文件：Qwen adapter 自动走 rule-based fallback。
- 无外部数据接口：默认使用 `data/` sample/mock CSV。
- 无 blocking interrupt：使用 pending-review 状态和审核 API。
