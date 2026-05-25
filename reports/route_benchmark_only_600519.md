# 资管投研辅助 Agent 报告：贵州茅台（600519）

## 0. 合规说明

本报告仅用于投研辅助、模型流程展示和教育研究，不构成交易指令或收益承诺。所有样例数据均为脱敏/模拟数据。 [tool_call_id=tc_risk_guardrail_fecb96994f; evidence_id=ev_product_benchmark_34]

## 1. Planner、数据与工具调用摘要

- Planner task_type：product_compare；analysis_depth：focused。[evidence_id=ev_planner_plan]
- 行情/净值样本：0 条观测，起始值 0.000，结束值 0.000。[tool_call_id=missing]
- 新闻样本：0 条，平均情绪分 0，平均风险分 0。[tool_call_id=missing]
- 同业产品样本：34 款，覆盖风险等级：R4。[tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_benchmark_34]
- 产品池规模：108 款 synthetic sample 产品。[tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_benchmark_34]
- 数据模式：sample/mock；Qwen 风险适配器：rule-based-fallback。[tool_call_id=missing]

| Tool call | Tool | 状态 | 耗时 | Evidence |
|---|---|---:|---:|---|
| tc_product_benchmark_eac6955829 | product_benchmark | pass | 142.97 ms | ev_product_benchmark_34 |
| tc_risk_guardrail_fecb96994f | risk_guardrail_check | pass | 0.46 ms | ev_product_benchmark_34 |

## 2. 核心量化指标

| 指标 | 数值 | 追溯 |
|---|---:|---|
| 区间收益 | 0.00% | [tool_call_id=missing] |
| 年化收益 | 0.00% | [tool_call_id=missing] |
| 年化波动率 | 0.00% | [tool_call_id=missing] |
| 最大回撤 | 0.00% | [tool_call_id=missing] |
| Sharpe Ratio | 0.000 | [tool_call_id=missing] |

## 3. 基本面与估值摘要

基本面标签：NA [tool_call_id=missing]

- 暂无样例字段。[tool_call_id=missing]

估值区间：NA [tool_call_id=missing]

- 暂无样例字段。[tool_call_id=missing]

## 4. 技术面风险观察

- 趋势标签：NA [tool_call_id=missing]
- 波动状态：NA [tool_call_id=missing]
- MA5 / MA20：0.000 / 0.000 [tool_call_id=missing]
- 5 日动量 / 20 日动量：0.00% / 0.00% [tool_call_id=missing]

- 暂无样例字段。[tool_call_id=missing]

## 5. 同业产品对标样例

| 产品 | 资产类别 | 风险等级 | 期限 | 年化收益 | 年化波动 | 最大回撤 | Sharpe | Calmar | Benchmark excess | 收益排名 | 风险调整排名 | 追溯 |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 商品/黄金商品趋势样例070 | 商品/黄金 | R4 | 3Y+ | 25.96% | 11.95% | -5.33% | 2.006 | 4.869 | 10.98% | 1 | 1 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0070] |
| 权益增强指数增强样例014 | 权益增强 | R4 | 0-3M | 22.70% | 13.28% | -5.96% | 1.558 | 3.811 | 5.13% | 2 | 2 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0014] |
| 商品/黄金商品趋势样例025 | 商品/黄金 | R4 | 3Y+ | 22.49% | 14.11% | -10.75% | 1.453 | 2.093 | 19.57% | 3 | 3 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0025] |
| 商品/黄金贵金属配置样例016 | 商品/黄金 | R4 | 3-6M | 15.80% | 14.28% | -5.80% | 0.967 | 2.724 | 0.45% | 4 | 4 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0016] |
| 权益增强红利增强样例023 | 权益增强 | R4 | 1-3Y | 11.99% | 18.27% | -13.88% | 0.547 | 0.864 | 4.25% | 5 | 6 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0023] |
| 多资产目标波动样例067 | 多资产 | R4 | 6-12M | 9.97% | 10.77% | -4.49% | 0.740 | 2.222 | 3.49% | 6 | 5 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0067] |
| 养老目标/FOF目标风险样例072 | 养老目标/FOF | R4 | 3Y+ | 5.41% | 13.79% | -10.84% | 0.248 | 0.500 | 8.11% | 7 | 8 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0072] |
| 养老目标/FOFFOF稳健样例108 | 养老目标/FOF | R4 | 3-6M | 5.27% | 11.16% | -6.22% | 0.293 | 0.848 | 5.83% | 8 | 7 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0108] |
| 商品/黄金黄金ETF联接样例088 | 商品/黄金 | R4 | 0-3M | 4.88% | 14.57% | -11.21% | 0.198 | 0.435 | -7.05% | 9 | 9 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0088] |
| 权益增强指数增强样例104 | 权益增强 | R4 | 0-3M | 4.73% | 27.65% | -21.56% | 0.099 | 0.219 | -20.58% | 10 | 12 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0104] |
| 商品/黄金商品趋势样例034 | 商品/黄金 | R4 | 6-12M | 4.41% | 18.29% | -18.60% | 0.132 | 0.237 | 8.74% | 11 | 11 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0034] |
| 量化对冲市场中性样例078 | 量化对冲 | R4 | 6-12M | 3.79% | 12.35% | -6.40% | 0.145 | 0.593 | 5.18% | 12 | 10 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0078] |
| 多资产风险平价样例004 | 多资产 | R4 | 6-12M | 1.31% | 13.69% | -7.42% | -0.051 | 0.176 | -2.75% | 13 | 13 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0004] |
| 量化对冲CTA样例042 | 量化对冲 | R4 | 3-6M | 0.18% | 10.87% | -6.01% | -0.167 | 0.030 | 11.18% | 14 | 14 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0042] |
| 固收+可转债增强样例075 | 固收+ | R4 | 6-12M | -3.94% | 9.53% | -9.02% | -0.624 | -0.437 | -6.94% | 15 | 18 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0075] |
| 权益增强红利增强样例032 | 权益增强 | R4 | 6-12M | -4.13% | 23.40% | -16.04% | -0.262 | -0.258 | 2.61% | 16 | 15 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0032] |
| QDII/全球配置全球多资产样例017 | QDII/全球配置 | R4 | 0-3M | -5.18% | 23.03% | -20.31% | -0.312 | -0.255 | -7.45% | 17 | 16 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0017] |
| 商品/黄金黄金ETF联接样例007 | 商品/黄金 | R4 | 6-12M | -6.24% | 13.68% | -11.12% | -0.602 | -0.561 | -1.09% | 18 | 17 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0007] |
| 多资产风险平价样例013 | 多资产 | R4 | 1-3Y | -9.57% | 14.18% | -11.14% | -0.816 | -0.859 | -2.29% | 19 | 21 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0013] |
| 固收+股债平衡样例048 | 固收+ | R4 | 1-3Y | -9.96% | 9.44% | -6.82% | -1.267 | -1.461 | -8.05% | 20 | 22 | [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_metric_SP0048] |

方法说明：基于 synthetic sample 产品周度 NAV 与 benchmark_nav 计算收益、波动、回撤、Sharpe、Calmar、benchmark excess、胜率和回撤修复天数；排序仅用于投研材料整理。 [tool_call_id=tc_product_benchmark_eac6955829; evidence_id=ev_product_benchmark_34]

## 6. 新闻情绪与风险信号

| 日期 | 标题 | 情绪分 | 风险分 | 模型模式 | 证据 | 追溯 |
|---|---|---:|---:|---|---|---|

重点风险标题：暂无。[tool_call_id=missing]

## 7. 风险提示与可追溯结论

- 产品池包含较高风险等级样例，展示收益指标时必须同步展示波动、回撤和风险等级。 [tool_call_id=tc_risk_guardrail_fecb96994f; evidence_id=ev_product_benchmark_34]
- 输出仅用于投研辅助、风险摘要、产品对标和研究报告生成，正式使用前保留人工复核与合规校验。 [tool_call_id=tc_risk_guardrail_fecb96994f; evidence_id=ev_product_benchmark_34]

系统结论：当前输出适合作为投研初稿、风险摘要、产品对标和材料整理的辅助结果。正式决策前，应结合真实数据源、产品说明书、投委会口径、合规审查与人工复核。[tool_call_id=tc_risk_guardrail_fecb96994f; evidence_id=ev_product_benchmark_34]
