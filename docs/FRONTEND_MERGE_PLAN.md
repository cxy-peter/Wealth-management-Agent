# Frontend Consolidation

The frontend is intentionally limited to three top-level workspaces:

- `ResearchDashboard`: analysis form, metrics, report preview, and a merged News Risk tab.
- `ProductBenchmark`: filter sidebar, product table, scatter plot, product detail drawer, NAV/benchmark curves, risk events, and metric trace.
- `TraceView`: planner/tool/event trace, verifier, guardrail, advanced eval, route optimization, contextual bandit results, and ScenarioReplay preview.

Human review is a drawer that opens when `human_review.status === "pending_review"`; it is not a top-level navigation item.

The app keeps sample/mock fallback data in `frontend/src/data/mockData.js`, so the UI remains usable when the backend is unavailable.
