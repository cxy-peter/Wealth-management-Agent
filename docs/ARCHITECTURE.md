# Architecture

## Runtime Flow

```mermaid
flowchart LR
  API["FastAPI"] --> Planner["planner_agent"]
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
  Verify --> Audit["SQLite audit store"]
  Audit --> Trace["TraceView"]
```

## Product Benchmark Flow

```mermaid
flowchart LR
  Catalog["sample_product_catalog.csv"] --> Tool["product_benchmark"]
  Nav["sample_product_nav.csv"] --> Tool
  Events["sample_product_risk_events.csv"] --> API["Product detail APIs"]
  Tool --> Metrics["return / volatility / drawdown / Sharpe / Calmar / excess"]
  Metrics --> Report["Report with evidence_id"]
```

## Key Contracts

- Planner outputs task type, analysis depth, required tools, skipped tools, risk level, and human-review hint.
- Tool registry returns `tool_call_id`, `tool_name`, `input_args`, `output`, `evidence_ids`, `latency_ms`, `success`, and `error_type`.
- Product benchmark rows include metric evidence and source tool-call references.
- Verifier checks metrics, evidence, report structure, product benchmark sourcing, and guardrail wording.
- SQLite records runs, agent events, tool calls, report snapshots, eval results, and human reviews.

## Fallback Strategy

- No API key: ReAct-capable agents use the deterministic tool pipeline.
- No GPU or local model file: Qwen adapter uses rule-based fallback.
- No external data connector: default reads `data/` sample/mock CSV files.
- No blocking LangGraph interrupt: human review uses `pending_review` plus review APIs.
