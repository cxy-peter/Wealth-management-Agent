# 资管投研辅助 Agent 报告：贵州茅台（600519）

## 0. 合规说明

本报告仅用于投研辅助、模型流程展示和教育研究，不构成交易指令或收益承诺。所有样例数据均为脱敏/模拟数据。 [tool_call_id=tc_risk_guardrail_48155e6f2d; evidence_id=ev_metrics_600519]

## 1. Planner、数据与工具调用摘要

- Planner task_type：deep_review；analysis_depth：deep。[evidence_id=ev_planner_plan]
- 行情/净值样本：25 条观测，起始值 1500.000，结束值 1536.000。[tool_call_id=tc_calculate_metrics_cdb7fbb83b; evidence_id=ev_metrics_600519]
- 新闻样本：4 条，平均情绪分 3.5，平均风险分 3.0。[tool_call_id=tc_classify_news_risk_b4716cc85b; evidence_id=ev_news_risk_600519_4]
- 同业产品样本：22 款，覆盖风险等级：R1, R2, R3, R4, R5。[tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_benchmark_22]
- 产品池规模：108 款 synthetic sample 产品。[tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_benchmark_22]
- 数据模式：sample/mock；Qwen 风险适配器：rule-based-fallback。[tool_call_id=tc_classify_news_risk_b4716cc85b; evidence_id=ev_news_risk_600519_4]

| Tool call | Tool | 状态 | 耗时 | Evidence |
|---|---|---:|---:|---|
| tc_load_fundamental_snapshot_ea30de5612 | load_fundamental_snapshot | pass | 8.83 ms | ev_fundamental_600519 |
| tc_load_price_series_8b2461c6ce | load_price_series | pass | 4.1 ms | ev_sample_nav_600519_25 |
| tc_calculate_metrics_cdb7fbb83b | calculate_metrics | pass | 4.63 ms | ev_metrics_600519 |
| tc_load_valuation_snapshot_9257a75b1b | load_valuation_snapshot | pass | 5.22 ms | ev_valuation_600519 |
| tc_load_news_c9749a435d | load_news | pass | 2.79 ms | ev_sample_news_600519_4 |
| tc_classify_news_risk_b4716cc85b | classify_news_risk | pass | 0.65 ms | ev_news_risk_600519_4 |
| tc_product_benchmark_8d4b7f6d33 | product_benchmark | pass | 174.37 ms | ev_product_benchmark_22 |
| tc_risk_guardrail_48155e6f2d | risk_guardrail_check | pass | 0.58 ms | ev_metrics_600519, ev_news_risk_600519_4, ev_valuation_600519, ev_product_benchmark_22 |

## 2. 核心量化指标

| 指标 | 数值 | 追溯 |
|---|---:|---|
| 区间收益 | 2.40% | [tool_call_id=tc_calculate_metrics_cdb7fbb83b; evidence_id=ev_metrics_600519] |
| 年化收益 | 28.28% | [tool_call_id=tc_calculate_metrics_cdb7fbb83b; evidence_id=ev_metrics_600519] |
| 年化波动率 | 6.87% | [tool_call_id=tc_calculate_metrics_cdb7fbb83b; evidence_id=ev_metrics_600519] |
| 最大回撤 | -0.79% | [tool_call_id=tc_calculate_metrics_cdb7fbb83b; evidence_id=ev_metrics_600519] |
| Sharpe Ratio | 3.824 | [tool_call_id=tc_calculate_metrics_cdb7fbb83b; evidence_id=ev_metrics_600519] |

## 3. 基本面与估值摘要

基本面标签：盈利质量样例较强 [tool_call_id=tc_load_fundamental_snapshot_ea30de5612; evidence_id=ev_fundamental_600519]

- 营收增速样例值为 8.3%。[tool_call_id=tc_load_fundamental_snapshot_ea30de5612]
- ROE 样例值为 28.6%，净利率样例值为 47.2%。[tool_call_id=tc_load_fundamental_snapshot_ea30de5612]
- 资产负债率样例值为 19.8%。[evidence_id=ev_fundamental_600519]

估值区间：相对同业中位数偏高 [tool_call_id=tc_load_valuation_snapshot_9257a75b1b; evidence_id=ev_valuation_600519]

- PE(TTM) 为 28.4，同业样例中位数为 24.8。 [tool_call_id=tc_load_valuation_snapshot_9257a75b1b]
- PB 为 8.6，同业样例中位数为 6.9。 [tool_call_id=tc_load_valuation_snapshot_9257a75b1b]
- 估值结论只用于横向描述，不输出交易方向或收益承诺。 [tool_call_id=tc_load_valuation_snapshot_9257a75b1b]

## 4. 技术面风险观察

- 趋势标签：样本内短期趋势偏强 [tool_call_id=tc_calculate_metrics_cdb7fbb83b; evidence_id=ev_metrics_600519]
- 波动状态：低波动观察 [tool_call_id=tc_calculate_metrics_cdb7fbb83b; evidence_id=ev_metrics_600519]
- MA5 / MA20：1531.200 / 1520.450 [tool_call_id=tc_calculate_metrics_cdb7fbb83b; evidence_id=ev_metrics_600519]
- 5 日动量 / 20 日动量：0.39% / 1.79% [tool_call_id=tc_calculate_metrics_cdb7fbb83b; evidence_id=ev_metrics_600519]

- 最新样例收盘值 1536.000，MA5 为 1531.200，MA20 为 1520.450。[tool_call_id=tc_calculate_metrics_cdb7fbb83b]
- 5 日动量 0.39%，20 日动量 1.79%。[evidence_id=ev_metrics_600519]

## 5. 同业产品对标样例

| 产品 | 资产类别 | 风险等级 | 期限 | 年化收益 | 年化波动 | 最大回撤 | Sharpe | Calmar | Benchmark excess | 收益排名 | 风险调整排名 | 追溯 |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 权益增强主动权益样例068 | 权益增强 | R5 | 6-12M | 21.54% | 31.54% | -21.65% | 0.620 | 0.995 | 5.63% | 1 | 3 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0068] |
| 多资产目标波动样例067 | 多资产 | R4 | 6-12M | 9.97% | 10.77% | -4.49% | 0.740 | 2.222 | 3.49% | 2 | 2 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0067] |
| 养老目标/FOF目标风险样例018 | 养老目标/FOF | R2 | 6-12M | 6.37% | 3.55% | -1.41% | 1.233 | 4.513 | 3.63% | 3 | 1 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0018] |
| 商品/黄金商品趋势样例034 | 商品/黄金 | R4 | 6-12M | 4.41% | 18.29% | -18.60% | 0.132 | 0.237 | 8.74% | 4 | 8 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0034] |
| 多资产目标波动样例094 | 多资产 | R3 | 6-12M | 3.80% | 8.64% | -6.77% | 0.209 | 0.561 | 4.26% | 5 | 6 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0094] |
| 量化对冲市场中性样例078 | 量化对冲 | R4 | 6-12M | 3.79% | 12.35% | -6.40% | 0.145 | 0.593 | 5.18% | 6 | 7 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0078] |
| 纯债固收短债样例083 | 纯债固收 | R3 | 6-12M | 2.85% | 1.75% | -1.53% | 0.486 | 1.861 | -2.76% | 7 | 4 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0083] |
| 现金管理现金管理样例055 | 现金管理 | R2 | 6-12M | 2.13% | 0.56% | -0.24% | 0.230 | 8.903 | 4.42% | 8 | 5 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0055] |
| 现金管理现金管理样例100 | 现金管理 | R1 | 6-12M | 1.97% | 0.30% | -0.08% | -0.110 | 25.685 | -0.96% | 9 | 11 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0100] |
| 多资产风险平价样例004 | 多资产 | R4 | 6-12M | 1.31% | 13.69% | -7.42% | -0.051 | 0.176 | -2.75% | 10 | 9 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0004] |
| 现金管理现金管理样例001 | 现金管理 | R1 | 6-12M | 1.08% | 0.29% | -0.12% | -3.134 | 8.970 | 1.33% | 11 | 22 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0001] |
| 纯债固收利率债样例056 | 纯债固收 | R3 | 6-12M | 0.65% | 3.02% | -2.46% | -0.448 | 0.262 | 2.30% | 12 | 13 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0056] |
| 权益增强主动权益样例095 | 权益增强 | R5 | 6-12M | -0.63% | 29.95% | -29.52% | -0.088 | -0.021 | -13.36% | 13 | 10 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0095] |
| 养老目标/FOFFOF稳健样例009 | 养老目标/FOF | R3 | 6-12M | -3.53% | 9.46% | -9.56% | -0.584 | -0.369 | -10.94% | 14 | 14 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0009] |
| 固收+可转债增强样例075 | 固收+ | R4 | 6-12M | -3.94% | 9.53% | -9.02% | -0.624 | -0.437 | -6.94% | 15 | 16 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0075] |
| 权益增强红利增强样例032 | 权益增强 | R4 | 6-12M | -4.13% | 23.40% | -16.04% | -0.262 | -0.258 | 2.61% | 16 | 12 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0032] |
| 量化对冲市场中性样例051 | 量化对冲 | R3 | 6-12M | -4.88% | 7.13% | -7.44% | -0.965 | -0.656 | -2.65% | 17 | 17 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0051] |
| 商品/黄金黄金ETF联接样例007 | 商品/黄金 | R4 | 6-12M | -6.24% | 13.68% | -11.12% | -0.602 | -0.561 | -1.09% | 18 | 15 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0007] |
| 养老目标/FOF目标风险样例081 | 养老目标/FOF | R3 | 6-12M | -8.91% | 7.03% | -9.07% | -1.553 | -0.982 | -7.17% | 19 | 19 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0081] |
| 商品/黄金黄金ETF联接样例052 | 商品/黄金 | R3 | 6-12M | -12.73% | 10.46% | -15.18% | -1.408 | -0.839 | -8.06% | 20 | 18 | [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_metric_SP0052] |

方法说明：基于 synthetic sample 产品周度 NAV 与 benchmark_nav 计算收益、波动、回撤、Sharpe、Calmar、benchmark excess、胜率和回撤修复天数；排序仅用于投研材料整理。 [tool_call_id=tc_product_benchmark_8d4b7f6d33; evidence_id=ev_product_benchmark_22]

## 6. 新闻情绪与风险信号

| 日期 | 标题 | 情绪分 | 风险分 | 模型模式 | 证据 | 追溯 |
|---|---|---:|---:|---|---|---|
| 2025-01-08 | 春节消费预期回暖 | 5 | 3 | rule-based-fallback | positive_hits=2; negative_hits=1; high_risk_hits=1; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_b4716cc85b; evidence_id=ev_news_risk_600519_4] |
| 2025-01-14 | 监管关注酒类价格秩序 | 2 | 4 | rule-based-fallback | positive_hits=0; negative_hits=1; high_risk_hits=2; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_b4716cc85b; evidence_id=ev_news_risk_600519_4] |
| 2025-01-21 | 公司推进分红规划 | 5 | 2 | rule-based-fallback | positive_hits=3; negative_hits=0; high_risk_hits=0; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_b4716cc85b; evidence_id=ev_news_risk_600519_4] |
| 2025-02-07 | 消费数据分化 | 2 | 3 | rule-based-fallback | positive_hits=0; negative_hits=1; high_risk_hits=1; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_b4716cc85b; evidence_id=ev_news_risk_600519_4] |

重点风险标题：监管关注酒类价格秩序; 春节消费预期回暖; 消费数据分化。[tool_call_id=tc_classify_news_risk_b4716cc85b; evidence_id=ev_news_risk_600519_4]

## 7. 风险提示与可追溯结论

- 新闻风险分处于中等及以上，应核查监管、渠道、价格、库存或违约相关事件。 [tool_call_id=tc_risk_guardrail_48155e6f2d; evidence_id=ev_metrics_600519]
- 相对估值样例高于同业中位数，需要拆分质量溢价、成长预期和估值回撤风险。 [tool_call_id=tc_risk_guardrail_48155e6f2d; evidence_id=ev_metrics_600519]
- 产品池包含较高风险等级样例，展示收益指标时必须同步展示波动、回撤和风险等级。 [tool_call_id=tc_risk_guardrail_48155e6f2d; evidence_id=ev_metrics_600519]
- 输出仅用于投研辅助、风险摘要、产品对标和研究报告生成，正式使用前保留人工复核与合规校验。 [tool_call_id=tc_risk_guardrail_48155e6f2d; evidence_id=ev_metrics_600519]

系统结论：当前输出适合作为投研初稿、风险摘要、产品对标和材料整理的辅助结果。正式决策前，应结合真实数据源、产品说明书、投委会口径、合规审查与人工复核。[tool_call_id=tc_risk_guardrail_48155e6f2d; evidence_id=ev_metrics_600519]
