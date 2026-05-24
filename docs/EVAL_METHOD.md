# Evaluation Method

## Report Eval

```bash
python eval/run_eval.py
```

Output: `eval/results.json`

Metrics:

- `tool_call_success`
- `report_format_pass`
- `metric_consistency`
- `risk_warning_coverage`
- `evidence_coverage`
- `forbidden_wording_fail_rate`
- `avg_latency_ms`

This eval keeps the legacy synchronous workflow healthy while the main product direction moves to weekly product research.

## Weekly DPO Style Eval

```bash
python -m backend.app.dpo.eval_dpo_report_style
```

Output: `eval/dpo_style_eval_results.json`

Checks:

- chosen output has `evidence_id`
- chosen output is grounded to tool output
- chosen output avoids configuration-oriented or return-promise wording
- chosen/rejected are materially different

## Route Optimization Eval

```bash
python eval/run_route_optimization.py
```

Output: `eval/route_optimization_results.json`

Actions:

- `fast_weekly_snapshot`
- `standard_weekly_report`
- `deep_product_review`
- `benchmark_only`
- `market_update_only`

## Contextual Bandit Eval

```bash
python eval/run_contextual_bandit.py
```

Output: `eval/contextual_bandit_results.json`

Cases:

- `eval/contextual_bandit_cases.json`: 96 weekly routing cases.
- Coverage includes weekly report, product benchmark, market update, high-risk review, low latency, missing NAV, scale pressure and benchmark-failed scenarios.

Context features:

- `is_weekly_report`
- `is_product_benchmark`
- `is_market_update`
- `is_high_risk_product`
- `benchmark_failed_count`
- `scale_drop_count`
- `product_pool_size`
- `avg_return_percentile`
- `avg_drawdown_percentile`
- `missing_nav_ratio`
- `market_new_issue_count`
- `latency_budget_ms`
- `human_review_required`

Compared strategies:

- `fixed_standard_research`
- `epsilon_greedy`
- `linucb_contextual_bandit`

Output fields:

- `average_reward`
- `average_latency_ms`
- `action_distribution`
- `regret_vs_oracle`
- `verifier_pass_rate`
- `forbidden_wording_fail_rate`
- `per_case_results`
