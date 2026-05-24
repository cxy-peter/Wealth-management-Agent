# Frontend Information Architecture

The frontend is intentionally limited to three top-level workspaces:

- `WeeklyReportDashboard`: weekly filters, KPI cards, scale-change rank, benchmark-failed table, low-percentile products, market issuance modules and risk-summary tab.
- `ProductBenchmarkWorkbench`: peer benchmark, market percentile, channel benchmark, top peer products and product detail drawer with NAV/benchmark curves and evidence trace.
- `AgentTraceView`: run id, weekly report date, planner plan, tool calls, evidence ids, verifier result, guardrail result, DPO chosen/rejected examples and advanced eval.

Human review is rendered as a drawer/modal only when a run enters `pending_review`.

Scenario replay remains an advanced/internal concept and is not exposed as top-level navigation.
