# 资管投研辅助 Agent 报告：贵州茅台（600519）

## 0. 合规说明

本报告仅用于投研辅助、模型流程展示和教育研究，不构成交易指令或收益承诺。所有样例数据均为脱敏/模拟数据。 [tool_call_id=tc_risk_guardrail_2a31b45873; evidence_id=ev_metrics_600519]

## 1. Planner、数据与工具调用摘要

- Planner task_type：standard_research；analysis_depth：standard。[evidence_id=ev_planner_plan]
- 行情/净值样本：25 条观测，起始值 1500.000，结束值 1536.000。[tool_call_id=tc_calculate_metrics_158da672fa; evidence_id=ev_metrics_600519]
- 新闻样本：4 条，平均情绪分 3.5，平均风险分 3.0。[tool_call_id=tc_classify_news_risk_c6f8f95e0b; evidence_id=ev_news_risk_600519_4]
- 同业产品样本：12 款，覆盖风险等级：R1, R2。[tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_benchmark_12]
- 产品池规模：108 款 synthetic sample 产品。[tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_benchmark_12]
- 数据模式：sample/mock；Qwen 风险适配器：rule-based-fallback。[tool_call_id=tc_classify_news_risk_c6f8f95e0b; evidence_id=ev_news_risk_600519_4]

| Tool call | Tool | 状态 | 耗时 | Evidence |
|---|---|---:|---:|---|
| tc_load_fundamental_snapshot_9c7de46f47 | load_fundamental_snapshot | pass | 7.26 ms | ev_fundamental_600519 |
| tc_load_price_series_c1484977fb | load_price_series | pass | 2.83 ms | ev_sample_nav_600519_25 |
| tc_calculate_metrics_158da672fa | calculate_metrics | pass | 2.97 ms | ev_metrics_600519 |
| tc_load_valuation_snapshot_54550775f9 | load_valuation_snapshot | pass | 2.68 ms | ev_valuation_600519 |
| tc_load_news_019fa2cba9 | load_news | pass | 3.42 ms | ev_sample_news_600519_4 |
| tc_classify_news_risk_c6f8f95e0b | classify_news_risk | pass | 0.68 ms | ev_news_risk_600519_4 |
| tc_product_benchmark_16f4e4e304 | product_benchmark | pass | 73.15 ms | ev_product_benchmark_12 |
| tc_risk_guardrail_2a31b45873 | risk_guardrail_check | pass | 0.25 ms | ev_metrics_600519, ev_news_risk_600519_4, ev_valuation_600519, ev_product_benchmark_12 |

## 2. 核心量化指标

| 指标 | 数值 | 追溯 |
|---|---:|---|
| 区间收益 | 2.40% | [tool_call_id=tc_calculate_metrics_158da672fa; evidence_id=ev_metrics_600519] |
| 年化收益 | 28.28% | [tool_call_id=tc_calculate_metrics_158da672fa; evidence_id=ev_metrics_600519] |
| 年化波动率 | 6.87% | [tool_call_id=tc_calculate_metrics_158da672fa; evidence_id=ev_metrics_600519] |
| 最大回撤 | -0.79% | [tool_call_id=tc_calculate_metrics_158da672fa; evidence_id=ev_metrics_600519] |
| Sharpe Ratio | 3.824 | [tool_call_id=tc_calculate_metrics_158da672fa; evidence_id=ev_metrics_600519] |

## 3. 基本面与估值摘要

基本面标签：盈利质量样例较强 [tool_call_id=tc_load_fundamental_snapshot_9c7de46f47; evidence_id=ev_fundamental_600519]

- 营收增速样例值为 8.3%。[tool_call_id=tc_load_fundamental_snapshot_9c7de46f47]
- ROE 样例值为 28.6%，净利率样例值为 47.2%。[tool_call_id=tc_load_fundamental_snapshot_9c7de46f47]
- 资产负债率样例值为 19.8%。[evidence_id=ev_fundamental_600519]

估值区间：相对同业中位数偏高 [tool_call_id=tc_load_valuation_snapshot_54550775f9; evidence_id=ev_valuation_600519]

- PE(TTM) 为 28.4，同业样例中位数为 24.8。 [tool_call_id=tc_load_valuation_snapshot_54550775f9]
- PB 为 8.6，同业样例中位数为 6.9。 [tool_call_id=tc_load_valuation_snapshot_54550775f9]
- 估值结论只用于横向描述，不输出交易方向或收益承诺。 [tool_call_id=tc_load_valuation_snapshot_54550775f9]

## 4. 技术面风险观察

- 趋势标签：样本内短期趋势偏强 [tool_call_id=tc_calculate_metrics_158da672fa; evidence_id=ev_metrics_600519]
- 波动状态：低波动观察 [tool_call_id=tc_calculate_metrics_158da672fa; evidence_id=ev_metrics_600519]
- MA5 / MA20：1531.200 / 1520.450 [tool_call_id=tc_calculate_metrics_158da672fa; evidence_id=ev_metrics_600519]
- 5 日动量 / 20 日动量：0.39% / 1.79% [tool_call_id=tc_calculate_metrics_158da672fa; evidence_id=ev_metrics_600519]

- 最新样例收盘值 1536.000，MA5 为 1531.200，MA20 为 1520.450。[tool_call_id=tc_calculate_metrics_158da672fa]
- 5 日动量 0.39%，20 日动量 1.79%。[evidence_id=ev_metrics_600519]

## 5. 同业产品对标样例

| 产品 | 资产类别 | 风险等级 | 期限 | 年化收益 | 年化波动 | 最大回撤 | Sharpe | Calmar | Benchmark excess | 收益排名 | 风险调整排名 | 追溯 |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 现金管理现金管理样例082 | 现金管理 | R2 | 0-3M | 3.27% | 0.69% | -0.18% | 1.839 | 18.251 | 4.24% | 1 | 1 | [tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_metric_SP0082] |
| 现金管理现金管理样例046 | 现金管理 | R1 | 3Y+ | 2.47% | 0.38% | -0.10% | 1.244 | 24.469 | 0.47% | 2 | 2 | [tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_metric_SP0046] |
| 现金管理流动性管理样例028 | 现金管理 | R1 | 3Y+ | 2.20% | 0.28% | -0.03% | 0.718 | 81.361 | 0.90% | 3 | 3 | [tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_metric_SP0028] |
| 现金管理现金管理样例055 | 现金管理 | R2 | 6-12M | 2.13% | 0.56% | -0.24% | 0.230 | 8.903 | 4.42% | 4 | 4 | [tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_metric_SP0055] |
| 现金管理现金管理样例100 | 现金管理 | R1 | 6-12M | 1.97% | 0.30% | -0.08% | -0.110 | 25.685 | -0.96% | 5 | 5 | [tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_metric_SP0100] |
| 现金管理流动性管理样例010 | 现金管理 | R1 | 3Y+ | 1.31% | 0.55% | -0.33% | -1.259 | 4.004 | 3.17% | 6 | 6 | [tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_metric_SP0010] |
| 现金管理现金管理样例001 | 现金管理 | R1 | 6-12M | 1.08% | 0.29% | -0.12% | -3.134 | 8.970 | 1.33% | 7 | 11 | [tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_metric_SP0001] |
| 现金管理流动性管理样例073 | 现金管理 | R1 | 0-3M | 1.08% | 0.40% | -0.13% | -2.312 | 8.080 | 0.10% | 8 | 8 | [tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_metric_SP0073] |
| 现金管理流动性管理样例019 | 现金管理 | R1 | 3Y+ | 0.65% | 0.44% | -0.25% | -3.061 | 2.628 | -2.70% | 9 | 9 | [tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_metric_SP0019] |
| 现金管理现金管理样例091 | 现金管理 | R1 | 0-3M | 0.52% | 0.18% | -0.04% | -8.294 | 13.640 | 0.50% | 10 | 12 | [tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_metric_SP0091] |
| 现金管理现金管理样例037 | 现金管理 | R2 | 1-3Y | -0.16% | 0.70% | -0.48% | -3.081 | -0.345 | -5.36% | 11 | 10 | [tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_metric_SP0037] |
| 现金管理流动性管理样例064 | 现金管理 | R2 | 3-6M | -0.72% | 2.04% | -1.56% | -1.332 | -0.464 | -0.37% | 12 | 7 | [tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_metric_SP0064] |

方法说明：基于 synthetic sample 产品周度 NAV 与 benchmark_nav 计算收益、波动、回撤、Sharpe、Calmar、benchmark excess、胜率和回撤修复天数；排序仅用于投研材料整理。 [tool_call_id=tc_product_benchmark_16f4e4e304; evidence_id=ev_product_benchmark_12]

## 6. 新闻情绪与风险信号

| 日期 | 标题 | 情绪分 | 风险分 | 模型模式 | 证据 | 追溯 |
|---|---|---:|---:|---|---|---|
| 2025-01-08 | 春节消费预期回暖 | 5 | 3 | rule-based-fallback | positive_hits=2; negative_hits=1; high_risk_hits=1; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_c6f8f95e0b; evidence_id=ev_news_risk_600519_4] |
| 2025-01-14 | 监管关注酒类价格秩序 | 2 | 4 | rule-based-fallback | positive_hits=0; negative_hits=1; high_risk_hits=2; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_c6f8f95e0b; evidence_id=ev_news_risk_600519_4] |
| 2025-01-21 | 公司推进分红规划 | 5 | 2 | rule-based-fallback | positive_hits=3; negative_hits=0; high_risk_hits=0; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_c6f8f95e0b; evidence_id=ev_news_risk_600519_4] |
| 2025-02-07 | 消费数据分化 | 2 | 3 | rule-based-fallback | positive_hits=0; negative_hits=1; high_risk_hits=1; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_c6f8f95e0b; evidence_id=ev_news_risk_600519_4] |

重点风险标题：监管关注酒类价格秩序; 春节消费预期回暖; 消费数据分化。[tool_call_id=tc_classify_news_risk_c6f8f95e0b; evidence_id=ev_news_risk_600519_4]

## 7. 风险提示与可追溯结论

- 新闻风险分处于中等及以上，应核查监管、渠道、价格、库存或违约相关事件。 [tool_call_id=tc_risk_guardrail_2a31b45873; evidence_id=ev_metrics_600519]
- 相对估值样例高于同业中位数，需要拆分质量溢价、成长预期和估值回撤风险。 [tool_call_id=tc_risk_guardrail_2a31b45873; evidence_id=ev_metrics_600519]
- 输出仅用于投研辅助、风险摘要、产品对标和研究报告生成，正式使用前保留人工复核与合规校验。 [tool_call_id=tc_risk_guardrail_2a31b45873; evidence_id=ev_metrics_600519]

系统结论：当前输出适合作为投研初稿、风险摘要、产品对标和材料整理的辅助结果。正式决策前，应结合真实数据源、产品说明书、投委会口径、合规审查与人工复核。[tool_call_id=tc_risk_guardrail_2a31b45873; evidence_id=ev_metrics_600519]
