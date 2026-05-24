# 资管投研辅助 Agent 报告：贵州茅台（600519）

## 0. 合规说明

本报告仅用于投研辅助、模型流程展示和教育研究，不构成投资建议、交易指令或收益承诺。所有样例数据均为脱敏/模拟数据。 [tool_call_id=tc_risk_guardrail_4375bce764; evidence_id=ev_product_benchmark_5]

## 1. Planner、数据与工具调用摘要

- Planner task_type：product_compare；analysis_depth：focused。[evidence_id=ev_planner_plan]
- 行情/净值样本：0 条观测，起始值 0.000，结束值 0.000。[tool_call_id=missing]
- 新闻样本：0 条，平均情绪分 0，平均风险分 0。[tool_call_id=missing]
- 同业产品样本：5 款，覆盖风险等级：R1, R2, R3, R4。[tool_call_id=tc_product_benchmark_7bb9fc651c; evidence_id=ev_product_benchmark_5]
- 数据模式：sample/mock；Qwen 风险适配器：rule-based-fallback。[tool_call_id=missing]

| Tool call | Tool | 状态 | 耗时 | Evidence |
|---|---|---:|---:|---|
| tc_product_benchmark_7bb9fc651c | product_benchmark | pass | 6.59 ms | ev_product_benchmark_5 |
| tc_risk_guardrail_4375bce764 | risk_guardrail_check | pass | 0.01 ms | ev_product_benchmark_5 |

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

## 5. 同业产品对比样例

| 产品 | 资产类别 | 渠道 | 风险等级 | 年化收益 | 年化波动 | 最大回撤 | Sharpe | 收益排名 | 追溯 |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 权益精选模拟 | 权益 | 券商渠道 | R4 | 8.80% | 16.00% | -7.20% | 0.425 | 1 | [tool_call_id=tc_product_benchmark_7bb9fc651c; evidence_id=ev_product_benchmark_5] |
| 多资产平衡二号 | 多资产 | 银行渠道 | R3 | 5.20% | 7.50% | -3.38% | 0.427 | 2 | [tool_call_id=tc_product_benchmark_7bb9fc651c; evidence_id=ev_product_benchmark_5] |
| 量化对冲模拟 | 量化 | 机构渠道 | R3 | 4.10% | 7.50% | -3.38% | 0.280 | 3 | [tool_call_id=tc_product_benchmark_7bb9fc651c; evidence_id=ev_product_benchmark_5] |
| 固收+稳健一号 | 固收+ | 银行渠道 | R2 | 3.60% | 3.50% | -1.58% | 0.457 | 4 | [tool_call_id=tc_product_benchmark_7bb9fc651c; evidence_id=ev_product_benchmark_5] |
| 现金管理增强 | 现金管理 | 线上渠道 | R1 | 1.20% | 1.50% | -0.68% | -0.533 | 5 | [tool_call_id=tc_product_benchmark_7bb9fc651c; evidence_id=ev_product_benchmark_5] |

方法说明：基于样例净值、期限、风险等级和渠道字段做横向对标；排序仅用于投研材料整理。 [tool_call_id=tc_product_benchmark_7bb9fc651c; evidence_id=ev_product_benchmark_5]

## 6. 新闻情绪与风险信号

| 日期 | 标题 | 情绪分 | 风险分 | 模型模式 | 证据 | 追溯 |
|---|---|---:|---:|---|---|---|

重点风险标题：暂无。[tool_call_id=missing]

## 7. 风险提示与可追溯结论

- 产品池包含较高风险等级样例，展示收益指标时必须同步展示波动、回撤和风险等级。 [tool_call_id=tc_risk_guardrail_4375bce764; evidence_id=ev_product_benchmark_5]
- 输出仅用于投研辅助、风险摘要、产品对标和研究报告生成，正式使用前保留人工复核与合规校验。 [tool_call_id=tc_risk_guardrail_4375bce764; evidence_id=ev_product_benchmark_5]

系统结论：当前输出适合作为投研初筛、风险摘要、产品对标和材料整理的辅助结果。正式决策前，应结合真实数据源、基金/理财产品说明书、投委会口径、合规审查与人工复核。[tool_call_id=tc_risk_guardrail_4375bce764; evidence_id=ev_product_benchmark_5]
