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

Current coverage:

- `eval/eval_cases.json`: 20 cases.
- Scenarios include normal research, product comparison, risk summary, high-risk news, missing data, empty product pool, wording injection, and extreme-volatility labels.

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
0.20 * tool_call_success
+ 0.20 * metric_consistency
+ 0.15 * risk_warning_coverage
+ 0.15 * evidence_coverage
+ 0.10 * report_format_pass
+ 0.10 * route_match_score
- 0.10 * latency_penalty
- 0.15 * unnecessary_tool_penalty
- 1.00 * forbidden_wording_hit
```

## Contextual Bandit Eval

Run:

```bash
python eval/run_contextual_bandit.py
```

Output:

```text
eval/contextual_bandit_results.json
```

Cases:

- `eval/contextual_bandit_cases.json`: 90 cases.
- Symbols are diversified across equity-like symbols, product ids, index-like symbols, global allocation and commodity examples.
- Context features include asset/product flags, risk preference, missing-data flags, news count/risk, volatility, drawdown, product pool size, product risk level, latency budget, and human-review requirement.

Compared strategies:

- `fixed_standard_research`
- `epsilon_greedy`
- `linucb_contextual_bandit`

Output fields:

- `average_reward`
- `average_latency_ms`
- `forbidden_wording_fail_rate`
- `action_distribution`
- `regret_vs_oracle`
- `per_case_results`
