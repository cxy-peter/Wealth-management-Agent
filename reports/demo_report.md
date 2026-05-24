# 资管产品周报摘要 Demo

本报告基于 `data/` 下 synthetic/mock 数据生成，仅用于投研辅助、风险摘要、产品对标和报告草稿整理。

## 周报概览

- 周报日期：2025-04-04。[evidence_id=ev_snapshot_WP0001_20250404]
- 覆盖产品数：96 个模拟产品；总规模 1330.05 亿元，较上周 1.42 亿元，较上月 2.86 亿元。[evidence_id=ev_snapshot_WP0001_20250404]
- 基准区间内占比约 36.5%，低于基准下限产品数 28。[evidence_id=ev_snapshot_WP0002_20250404]
- 低收益分位产品数 22，需关注产品数 41；这些样本进入周报风险提示与人工复核队列。[evidence_id=ev_market_issuance_20250404]

## 产品规模变化

规模变化榜按 `abs(scale_wow_bn)` 排序，用于定位本周规模波动较大的样本。规模变动本身不构成配置结论，只作为渠道、期限和风险事件进一步核查的线索。[evidence_id=ev_snapshot_WP0031_20250404]

## 基准状态

`benchmark_status` 由成立以来年化收益与 `benchmark_lower`、`benchmark_upper` 规则比对生成。低于基准下限的产品需结合 NAV、同类分位、渠道变化和风险事件进行复核。[evidence_id=ev_snapshot_WP0028_20250404]

## 市场发行观察

本周市场新发产品数量为 72 只；按投资性质和期限分布聚合，用于对照本产品池的发行节奏与期限结构变化。[evidence_id=ev_market_issuance_20250404]

## 风险提示

- 对低收益分位、低回撤分位或基准未达标样本，报告只提示风险观察点，不给出配置动作。
- 对 R4/R5 或缺失 NAV 比例较高样本，系统路由倾向 `deep_product_review` 并触发更严格的 verifier 检查。
- 所有数字结论均需保留 evidence_id 或 tool_call_id，正式使用前保留人工复核。
