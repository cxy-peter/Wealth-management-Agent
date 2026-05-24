# 资管投研辅助 Agent 报告：贵州茅台（600519）

## 0. 合规说明

本报告仅用于投研辅助、模型流程展示和教育研究，不构成交易指令或收益承诺。所有样例数据均为脱敏/模拟数据。 [tool_call_id=tc_risk_guardrail_ac9f7bb2bd; evidence_id=ev_metrics_600519]

## 1. Planner、数据与工具调用摘要

- Planner task_type：risk_only；analysis_depth：focused。[evidence_id=ev_planner_plan]
- 行情/净值样本：25 条观测，起始值 1500.000，结束值 1536.000。[tool_call_id=tc_calculate_metrics_515984b207; evidence_id=ev_metrics_600519]
- 新闻样本：4 条，平均情绪分 3.5，平均风险分 3.0。[tool_call_id=tc_classify_news_risk_bf9e8028c1; evidence_id=ev_news_risk_600519_4]
- 同业产品样本：0 款，覆盖风险等级：。[tool_call_id=missing]
- 产品池规模：0 款 synthetic sample 产品。[tool_call_id=missing]
- 数据模式：sample/mock；Qwen 风险适配器：rule-based-fallback。[tool_call_id=tc_classify_news_risk_bf9e8028c1; evidence_id=ev_news_risk_600519_4]

| Tool call | Tool | 状态 | 耗时 | Evidence |
|---|---|---:|---:|---|
| tc_load_price_series_95bd00febc | load_price_series | pass | 3.1 ms | ev_sample_nav_600519_25 |
| tc_calculate_metrics_515984b207 | calculate_metrics | pass | 3.3 ms | ev_metrics_600519 |
| tc_load_news_5b12f1af4a | load_news | pass | 3.0 ms | ev_sample_news_600519_4 |
| tc_classify_news_risk_bf9e8028c1 | classify_news_risk | pass | 0.66 ms | ev_news_risk_600519_4 |
| tc_risk_guardrail_ac9f7bb2bd | risk_guardrail_check | pass | 0.05 ms | ev_metrics_600519, ev_news_risk_600519_4 |

## 2. 核心量化指标

| 指标 | 数值 | 追溯 |
|---|---:|---|
| 区间收益 | 2.40% | [tool_call_id=tc_calculate_metrics_515984b207; evidence_id=ev_metrics_600519] |
| 年化收益 | 28.28% | [tool_call_id=tc_calculate_metrics_515984b207; evidence_id=ev_metrics_600519] |
| 年化波动率 | 6.87% | [tool_call_id=tc_calculate_metrics_515984b207; evidence_id=ev_metrics_600519] |
| 最大回撤 | -0.79% | [tool_call_id=tc_calculate_metrics_515984b207; evidence_id=ev_metrics_600519] |
| Sharpe Ratio | 3.824 | [tool_call_id=tc_calculate_metrics_515984b207; evidence_id=ev_metrics_600519] |

## 3. 基本面与估值摘要

基本面标签：NA [tool_call_id=missing]

- 暂无样例字段。[tool_call_id=missing]

估值区间：NA [tool_call_id=missing]

- 暂无样例字段。[tool_call_id=missing]

## 4. 技术面风险观察

- 趋势标签：样本内短期趋势偏强 [tool_call_id=tc_calculate_metrics_515984b207; evidence_id=ev_metrics_600519]
- 波动状态：低波动观察 [tool_call_id=tc_calculate_metrics_515984b207; evidence_id=ev_metrics_600519]
- MA5 / MA20：1531.200 / 1520.450 [tool_call_id=tc_calculate_metrics_515984b207; evidence_id=ev_metrics_600519]
- 5 日动量 / 20 日动量：0.39% / 1.79% [tool_call_id=tc_calculate_metrics_515984b207; evidence_id=ev_metrics_600519]

- 最新样例收盘值 1536.000，MA5 为 1531.200，MA20 为 1520.450。[tool_call_id=tc_calculate_metrics_515984b207]
- 5 日动量 0.39%，20 日动量 1.79%。[evidence_id=ev_metrics_600519]

## 5. 同业产品对标样例

| 产品 | 资产类别 | 风险等级 | 期限 | 年化收益 | 年化波动 | 最大回撤 | Sharpe | Calmar | Benchmark excess | 收益排名 | 风险调整排名 | 追溯 |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 无匹配产品 | - | - | - | 0.00% | 0.00% | 0.00% | 0.000 | 0.000 | 0.00% | - | - | [tool_call_id=missing] |

方法说明： [tool_call_id=missing]

## 6. 新闻情绪与风险信号

| 日期 | 标题 | 情绪分 | 风险分 | 模型模式 | 证据 | 追溯 |
|---|---|---:|---:|---|---|---|
| 2025-01-08 | 春节消费预期回暖 | 5 | 3 | rule-based-fallback | positive_hits=2; negative_hits=1; high_risk_hits=1; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_bf9e8028c1; evidence_id=ev_news_risk_600519_4] |
| 2025-01-14 | 监管关注酒类价格秩序 | 2 | 4 | rule-based-fallback | positive_hits=0; negative_hits=1; high_risk_hits=2; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_bf9e8028c1; evidence_id=ev_news_risk_600519_4] |
| 2025-01-21 | 公司推进分红规划 | 5 | 2 | rule-based-fallback | positive_hits=3; negative_hits=0; high_risk_hits=0; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_bf9e8028c1; evidence_id=ev_news_risk_600519_4] |
| 2025-02-07 | 消费数据分化 | 2 | 3 | rule-based-fallback | positive_hits=0; negative_hits=1; high_risk_hits=1; qwen_adapter=rule-based-fallback; fallback=true | [tool_call_id=tc_classify_news_risk_bf9e8028c1; evidence_id=ev_news_risk_600519_4] |

重点风险标题：监管关注酒类价格秩序; 春节消费预期回暖; 消费数据分化。[tool_call_id=tc_classify_news_risk_bf9e8028c1; evidence_id=ev_news_risk_600519_4]

## 7. 风险提示与可追溯结论

- 新闻风险分处于中等及以上，应核查监管、渠道、价格、库存或违约相关事件。 [tool_call_id=tc_risk_guardrail_ac9f7bb2bd; evidence_id=ev_metrics_600519]
- 输出仅用于投研辅助、风险摘要、产品对标和研究报告生成，正式使用前保留人工复核与合规校验。 [tool_call_id=tc_risk_guardrail_ac9f7bb2bd; evidence_id=ev_metrics_600519]

系统结论：当前输出适合作为投研初稿、风险摘要、产品对标和材料整理的辅助结果。正式决策前，应结合真实数据源、产品说明书、投委会口径、合规审查与人工复核。[tool_call_id=tc_risk_guardrail_ac9f7bb2bd; evidence_id=ev_metrics_600519]
