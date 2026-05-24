# Codex Implementation Notes

This repository is positioned as `wealth-research-agent`: a weekly asset-management product research and benchmarking workbench.

## Hard Constraints

1. All pages, APIs and reports must be framed as research assistance, risk summary, product benchmarking, market/channel percentile analysis or report generation.
2. Do not output trade-direction language, configuration instructions or promised-return language.
3. Do not commit credentials, private data, real customer data, model weights or internal company files.
4. Default data must come from `data/` synthetic/mock files. Real connectors must be configured through environment variables.
5. Report conclusions must be traceable through `tool_call_id` or `evidence_id`.

## Backend Architecture

Weekly report path:

```text
weekly_report parsers
  -> scale/return/percentile/benchmark metrics
  -> weekly_report_generator / benchmark_report_generator
  -> weekly_report_verifier
  -> guardrail / human review when needed
  -> audit trace
```

Agent path remains ReAct/MCP-capable with deterministic fallback.

## Frontend Architecture

Top-level pages:

```text
frontend/src/pages/
  WeeklyReportDashboard.jsx
  ProductBenchmarkWorkbench.jsx
  AgentTraceView.jsx
```

Human review is implemented as a drawer, not a top-level page.

## Verification

```bash
python scripts/generate_weekly_report_universe.py
python -m compileall backend scripts eval
pytest
python eval/run_eval.py
python eval/run_route_optimization.py
python eval/run_contextual_bandit.py
python -m backend.app.dpo.eval_dpo_report_style
cd frontend
npm run build
```
