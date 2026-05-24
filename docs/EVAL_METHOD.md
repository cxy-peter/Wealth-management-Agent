# Evaluation Method

## Report Eval

Run:

```bash
python eval/run_eval.py
```

Output:

```text
eval/results.json
```

Metrics:

- `tool_call_success`
- `report_format_pass`
- `metric_consistency`
- `risk_warning_coverage`
- `evidence_coverage`
- `forbidden_wording_fail_rate`
- `avg_latency_ms`

## Route Optimization Eval

Run:

```bash
python eval/run_route_optimization.py
```

Output:

```text
eval/route_optimization_results.json
```

Reward:

```text
0.25 * tool_call_success
+ 0.25 * metric_consistency
+ 0.20 * risk_warning_coverage
+ 0.15 * evidence_coverage
+ 0.10 * report_format_pass
- 0.10 * latency_penalty
- 1.00 * forbidden_wording_hit
```

Policy:

- `fast_snapshot`
- `standard_research`
- `deep_review`
- `product_compare`
- `risk_only`

Current implementation uses epsilon-greedy routing with deterministic sample cases.
