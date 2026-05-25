# 资管投研辅助 Agent 报告：得润固收添益30天持有期（WP0001）

## 0. 合规说明

本报告仅用于投研辅助、模型流程展示和教育研究，不构成交易指令或收益承诺。所有样例数据均为脱敏/模拟数据。 [tool_call_id=tc_risk_guardrail_f956da67f6; evidence_id=ev_product_benchmark_108]

## 1. Planner、数据与工具调用摘要

- Planner task_type：product_compare；analysis_depth：focused。[evidence_id=ev_planner_plan]
- 行情/净值样本：0 条观测，起始值 0.000，结束值 0.000。[tool_call_id=missing]
- 新闻样本：0 条，平均情绪分 0，平均风险分 0。[tool_call_id=missing]
- 同业产品样本：108 款，覆盖风险等级：R1, R2, R3, R4, R5。[tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_benchmark_108]
- 产品池规模：108 款 synthetic sample 产品。[tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_benchmark_108]
- 数据模式：sample/mock；Qwen 风险适配器：rule-based-fallback。[tool_call_id=missing]

| Tool call | Tool | 状态 | 耗时 | Evidence |
|---|---|---:|---:|---|
| tc_product_benchmark_3b4f74f40a | product_benchmark | pass | 382.76 ms | ev_product_benchmark_108 |
| tc_risk_guardrail_f956da67f6 | risk_guardrail_check | pass | 1.09 ms | ev_product_benchmark_108 |

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
| 权益增强指数增强样例077 | 权益增强 | R5 | 0-3M | 34.92% | 26.32% | -15.36% | 1.250 | 2.273 | 36.50% | 1 | 14 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0077] |
| QDII/全球配置全球权益样例098 | QDII/全球配置 | R3 | 0-3M | 28.24% | 11.34% | -3.87% | 2.314 | 7.288 | 12.91% | 2 | 3 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0098] |
| 商品/黄金商品趋势样例070 | 商品/黄金 | R4 | 3Y+ | 25.96% | 11.95% | -5.33% | 2.006 | 4.869 | 10.98% | 3 | 4 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0070] |
| 多资产风险平价样例103 | 多资产 | R3 | 0-3M | 24.06% | 8.45% | -7.31% | 2.610 | 3.290 | 10.49% | 4 | 2 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0103] |
| 权益增强指数增强样例014 | 权益增强 | R4 | 0-3M | 22.70% | 13.28% | -5.96% | 1.558 | 3.811 | 5.13% | 5 | 10 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0014] |
| 商品/黄金商品趋势样例025 | 商品/黄金 | R4 | 3Y+ | 22.49% | 14.11% | -10.75% | 1.453 | 2.093 | 19.57% | 6 | 12 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0025] |
| 养老目标/FOF目标日期样例045 | 养老目标/FOF | R2 | 0-3M | 21.81% | 5.30% | -1.27% | 3.741 | 17.180 | 9.71% | 7 | 1 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0045] |
| 权益增强主动权益样例068 | 权益增强 | R5 | 6-12M | 21.54% | 31.54% | -21.65% | 0.620 | 0.995 | 5.63% | 8 | 24 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0068] |
| 商品/黄金贵金属配置样例016 | 商品/黄金 | R4 | 3-6M | 15.80% | 14.28% | -5.80% | 0.967 | 2.724 | 0.45% | 9 | 18 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0016] |
| 养老目标/FOF目标风险样例099 | 养老目标/FOF | R3 | 0-3M | 12.94% | 6.76% | -2.36% | 1.617 | 5.491 | 2.67% | 10 | 9 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0099] |
| 权益增强指数增强样例005 | 权益增强 | R5 | 0-3M | 12.40% | 22.11% | -14.34% | 0.470 | 0.865 | 31.65% | 11 | 28 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0005] |
| 权益增强红利增强样例023 | 权益增强 | R4 | 1-3Y | 11.99% | 18.27% | -13.88% | 0.547 | 0.864 | 4.25% | 12 | 25 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0023] |
| 养老目标/FOFFOF稳健样例036 | 养老目标/FOF | R2 | 3-6M | 10.43% | 4.93% | -2.66% | 1.711 | 3.922 | 7.51% | 13 | 7 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0036] |
| 多资产目标波动样例067 | 多资产 | R4 | 6-12M | 9.97% | 10.77% | -4.49% | 0.740 | 2.222 | 3.49% | 14 | 22 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0067] |
| 多资产股债商多资产样例085 | 多资产 | R3 | 0-3M | 9.08% | 8.31% | -4.32% | 0.852 | 2.103 | 1.29% | 15 | 20 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0085] |
| 固收+可转债增强样例057 | 固收+ | R3 | 3-6M | 8.18% | 5.46% | -3.71% | 1.133 | 2.208 | 4.95% | 16 | 17 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0057] |
| 固收+债券增强样例039 | 固收+ | R3 | 3Y+ | 7.66% | 3.74% | -1.67% | 1.513 | 4.592 | 1.44% | 17 | 11 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0039] |
| 固收+股债平衡样例012 | 固收+ | R2 | 3-6M | 6.60% | 2.77% | -1.26% | 1.660 | 5.247 | 0.44% | 18 | 8 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0012] |
| 养老目标/FOF目标风险样例018 | 养老目标/FOF | R2 | 6-12M | 6.37% | 3.55% | -1.41% | 1.233 | 4.513 | 3.63% | 19 | 16 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0018] |
| 纯债固收利率债样例101 | 纯债固收 | R3 | 0-3M | 5.60% | 1.90% | -0.36% | 1.899 | 15.464 | 1.36% | 20 | 5 | [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_metric_SP0101] |

方法说明：基于 synthetic sample 产品周度 NAV 与 benchmark_nav 计算收益、波动、回撤、Sharpe、Calmar、benchmark excess、胜率和回撤修复天数；排序仅用于投研材料整理。 [tool_call_id=tc_product_benchmark_3b4f74f40a; evidence_id=ev_product_benchmark_108]

## 6. 新闻情绪与风险信号

| 日期 | 标题 | 情绪分 | 风险分 | 模型模式 | 证据 | 追溯 |
|---|---|---:|---:|---|---|---|

重点风险标题：暂无。[tool_call_id=missing]

## 7. 风险提示与可追溯结论

- 产品池包含较高风险等级样例，展示收益指标时必须同步展示波动、回撤和风险等级。 [tool_call_id=tc_risk_guardrail_f956da67f6; evidence_id=ev_product_benchmark_108]
- 输出仅用于投研辅助、风险摘要、产品对标和研究报告生成，正式使用前保留人工复核与合规校验。 [tool_call_id=tc_risk_guardrail_f956da67f6; evidence_id=ev_product_benchmark_108]

系统结论：当前输出适合作为投研初稿、风险摘要、产品对标和材料整理的辅助结果。正式决策前，应结合真实数据源、产品说明书、投委会口径、合规审查与人工复核。[tool_call_id=tc_risk_guardrail_f956da67f6; evidence_id=ev_product_benchmark_108]
