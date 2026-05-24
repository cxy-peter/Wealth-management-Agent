# Codex Implementation Notes

This repository is positioned as `wealth-research-agent`: a runnable asset-management research assistant demo for portfolio research, wealth-product comparison, risk summary, and report generation.

## Hard Constraints

1. All pages, APIs, and reports must be framed as research assistance, risk summary, product benchmarking, or report generation.
2. Do not output trade-direction language or promised return language.
3. Do not commit credentials, private data, real customer data, model weights, or internal company files.
4. Default data must come from `data/` sample/mock files. Real connectors must be configured through environment variables.
5. Report conclusions must be traceable to sample data, metric tools, news evidence, product metrics, or guardrail output through `tool_call_id` or `evidence_id`.

## Backend Architecture

Current workflow:

```text
planner_agent
  -> conditional LangGraph route
  -> ReAct/MCP-capable tool agents with deterministic fallback
  -> risk_guardrail_agent
  -> report_agent
  -> verifier_agent
  -> human_review_agent when needed
```

Product benchmark uses:

```text
sample_product_catalog.csv
sample_product_nav.csv
sample_product_risk_events.csv
```

## Frontend Architecture

Top-level pages:

```text
frontend/src/pages/
  ResearchDashboard.jsx
  ProductBenchmark.jsx
  TraceView.jsx
```

Human review is implemented as a drawer, not a top-level page. News risk is a tab in `ResearchDashboard`. Eval, route optimization, contextual bandit, and ScenarioReplay are in `TraceView` advanced tabs.

## Verification

```bash
python scripts/generate_sample_product_universe.py
python scripts/run_demo.py --symbol 600519 --company 贵州茅台
python eval/run_eval.py
python eval/run_route_optimization.py
python eval/run_contextual_bandit.py
pytest
cd frontend
npm run build
```
