# 资管投研辅助 Agent 报告：贵州茅台（600519）

## 0. 合规说明

本报告仅用于投研辅助、模型流程展示和教育研究，不构成投资建议、交易指令或收益承诺。所有样例数据均为脱敏/模拟数据。 [tool_call_id=tc_risk_guardrail_b9c529ba96; evidence_id=ev_metrics_600519]

## 1. Planner、数据与工具调用摘要

- Planner task_type：standard_research；analysis_depth：standard。[evidence_id=ev_planner_plan]
- 行情/净值样本：25 条观测，起始值 1500.000，结束值 1536.000。[tool_call_id=tc_calculate_metrics_c154679dac; evidence_id=ev_metrics_600519]
- 新闻样本：4 条，平均情绪分 3.5，平均风险分 3.0。[tool_call_id=tc_classify_news_risk_e5f4934e23; evidence_id=ev_news_risk_600519_4]
- 同业产品样本：5 款，覆盖风险等级：R1, R2, R3, R4。[tool_call_id=tc_product_benchmark_b05c8fe18a; evidence_id=ev_product_benchmark_5]
- 数据模式：sample/mock；Qwen 风险适配器：rule-based-fallback。[tool_call_id=tc_classify_news_risk_e5f4934e23; evidence_id=ev_news_risk_600519_4]

| Tool call | Tool | 状态 | 耗时 | Evidence |
|---|---|---:|---:|---|
| tc_load_fundamental_snapshot_fafeb3ecf2 | load_fundamental_snapshot | pass | 8.81 ms | ev_fundamental_600519 |
| tc_load_price_series_dd3046b99d | load_price_series | pass | 2.61 ms | ev_sample_nav_600519_25 |
| tc_calculate_metrics_c154679dac | calculate_metrics | pass | 3.51 ms | ev_metrics_600519 |
| tc_load_valuation_snapshot_919debe840 | load_valuation_snapshot | pass | 2.14 ms | ev_valuation_600519 |
| tc_load_news_42d784078c | load_news | pass | 2.84 ms | ev_sample_news_600519_4 |
| tc_classify_news_risk_e5f4934e23 | classify_news_risk | pass | 0.74 ms | ev_news_risk_600519_4 |
| tc_product_benchmark_b05c8fe18a | product_benchmark | pass | 7.11 ms | ev_product_benchmark_5 |
| tc_risk_guardrail_b9c529ba96 | risk_guardrail_check | pass | 0.02 ms | ev_metrics_600519, ev_news_risk_600519_4, ev_valuation_600519, ev_product_benchmark_5 |

## 2. 核心量化指标

| 指标 | 数值 | 追溯 |
|---|---:|---|
| 区间收益 | 2.40% | [tool_call_id=tc_calculate_metrics_c154679dac; evidence_id=ev_metrics_600519] |
| 年化收益 | 28.28% | [tool_call_id=tc_calculate_metrics_c154679dac; evidence_id=ev_metrics_600519] |
| 年化波动率 | 6.87% | [tool_call_id=tc_calculate_metrics_c154679dac; evidence_id=ev_metrics_600519] |
| 最大回撤 | -0.79% | [tool_call_id=tc_calculate_metrics_c154679dac; evidence_id=ev_metrics_600519] |
| Sharpe Ratio | 3.824 | [tool_call_id=tc_calculate_metrics_c154679dac; evidence_id=ev_metrics_600519] |

## 3. 基本面与估值摘要

基本面标签：盈利质量样例较强 [tool_call_id=tc_load_fundamental_snapshot_fafeb3ecf2; evidence_id=ev_fundamental_600519]

- 营收增速样例值为 8.3%。[tool_call_id=tc_load_fundamental_snapshot_fafeb3ecf2]
- ROE 样例值为 28.6%，净利率样例值为 47.2%。[tool_call_id=tc_load_fundamental_snapshot_fafeb3ecf2]
- 资产负债率样例值为 19.8%。[evidence_id=ev_fundamental_600519]

估值区间：相对同业中位数偏高 [tool_call_id=tc_load_valuation_snapshot_919debe840; evidence_id=ev_valuation_600519]

- PE(TTM) 为 28.4，同业样例中位数为 24.8。 [tool_call_id=tc_load_valuation_snapshot_919debe840]
- PB 为 8.6，同业样例中位数为 6.9。 [tool_call_id=tc_load_valuation_snapshot_919debe840]
- 估值结论只用于横向描述，不输出交易方向或收益承诺。 [tool_call_id=tc_load_valuation_snapshot_919debe840]

## 4. 技术面风险观察

- 趋势标签：样本内短期趋势偏强 [tool_call_id=tc_calculate_metrics_c154679dac; evidence_id=ev_metrics_600519]
- 波动状态：低波动观察 [tool_call_id=tc_calculate_metrics_c154679dac; evidence_id=ev_metrics_600519]
- MA5 / MA20：1531.200 / 1520.450 [tool_call_id=tc_calculate_metrics_c154679dac; evidence_id=ev_metrics_600519]
- 5 日动量 / 20 日动量：0.39% / 1.79% [tool_call_id=tc_calculate_metrics_c154679dac; evidence_id=ev_metrics_600519]

- 最新样例收盘值 1536.000，MA5 为 1531.200，MA20 为 1520.450。[tool_call_id=tc_calculate_metrics_c154679dac]
- 5 日动量 0.39%，20 日动量 1.79%。[evidence_id=ev_metrics_600519]

## 5. 同业产品对比样例

| 产品 | 资产类别 | 渠道 | 风险等级 | 年化收益 | 年化波动 | 最大回撤 | Sharpe | 收益排名 | 追溯 |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 权益精选模拟 | 权益 | 券商渠道 | R4 | 8.80% | 16.00% | -7.20% | 0.425 | 1 | [tool_call_id=tc_product_benchmark_b05c8fe18a; evidence_id=ev_product_benchmark_5] |
| 多资产平衡二号 | 多资产 | 银行渠道 | R3 | 5.20% | 7.50% | -3.38% | 0.427 | 2 | [tool_call_id=tc_product_benchmark_b05c8fe18a; evidence_id=ev_product_benchmark_5] |
| 量化对冲模拟 | 量化 | 机构渠道 | R3 | 4.10% | 7.50% | -3.38% | 0.280 | 3 | [tool_call_id=tc_product_benchmark_b05c8fe18a; evidence_id=ev_product_benchmark_5] |
| 固收+稳健一号 | 固收+ | 银行渠道 | R2 | 3.60% | 3.50% | -1.58% | 0.457 | 4 | [tool_call_id=tc_product_benchmark_b05c8fe18a; evidence_id=ev_product_benchmark_5] |
| 现金管理增强 | 现金管理 | 线上渠道 | R1 | 1.20% | 1.50% | -0.68% | -0.533 | 5 | [tool_call_id=tc_product_benchmark_b05c8fe18a; evidence_id=ev_product_benchmark_5] |

方法说明：基于样例净值、期限、风险等级和渠道字段做横向对标；排序仅用于投研材料整理。 [tool_call_id=tc_product_benchmark_b05c8fe18a; evidence_id=ev_product_benchmark_5]

## 6. 新闻情绪与风险信号

| 日期 | 标题 | 情绪分 | 风险分 | 模型模式 | 证据 | 追溯 |
|---|---|---:|---:|---|---|---|
| 2025-01-08 | 春节消费预期回暖 | 5 | 3 | rule-based-fallback | positive_hits=2; negative_hits=1; high_risk_hits=1; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_e5f4934e23; evidence_id=ev_news_risk_600519_4] |
| 2025-01-14 | 监管关注酒类价格秩序 | 2 | 4 | rule-based-fallback | positive_hits=0; negative_hits=1; high_risk_hits=2; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_e5f4934e23; evidence_id=ev_news_risk_600519_4] |
| 2025-01-21 | 公司推进分红规划 | 5 | 2 | rule-based-fallback | positive_hits=3; negative_hits=0; high_risk_hits=0; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_e5f4934e23; evidence_id=ev_news_risk_600519_4] |
| 2025-02-07 | 消费数据分化 | 2 | 3 | rule-based-fallback | positive_hits=0; negative_hits=1; high_risk_hits=1; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_e5f4934e23; evidence_id=ev_news_risk_600519_4] |

重点风险标题：监管关注酒类价格秩序; 春节消费预期回暖; 消费数据分化。[tool_call_id=tc_classify_news_risk_e5f4934e23; evidence_id=ev_news_risk_600519_4]

## 7. 风险提示与可追溯结论

- 新闻风险分处于中等及以上，应核查监管、渠道、价格、库存或违约相关事件。 [tool_call_id=tc_risk_guardrail_b9c529ba96; evidence_id=ev_metrics_600519]
- 相对估值样例高于同业中位数，需要拆分质量溢价、成长预期和估值回撤风险。 [tool_call_id=tc_risk_guardrail_b9c529ba96; evidence_id=ev_metrics_600519]
- 产品池包含较高风险等级样例，展示收益指标时必须同步展示波动、回撤和风险等级。 [tool_call_id=tc_risk_guardrail_b9c529ba96; evidence_id=ev_metrics_600519]
- 输出仅用于投研辅助、风险摘要、产品对标和研究报告生成，正式使用前保留人工复核与合规校验。 [tool_call_id=tc_risk_guardrail_b9c529ba96; evidence_id=ev_metrics_600519]

系统结论：当前输出适合作为投研初筛、风险摘要、产品对标和材料整理的辅助结果。正式决策前，应结合真实数据源、基金/理财产品说明书、投委会口径、合规审查与人工复核。[tool_call_id=tc_risk_guardrail_b9c529ba96; evidence_id=ev_metrics_600519]
