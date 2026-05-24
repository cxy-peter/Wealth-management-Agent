# Frontend merge plan

MSX/RiskLens 前端只作为交互参考，不整仓复制。当前项目保留三类适合投研投递的交互：

- 产品货架与产品详情式信息密度；
- evidence-backed diligence：证据、memo、红旗、变化项分开展示；
- Paper Replay：教学模拟回放，不连接账户，不发送真实订单。

新页面已经落在：

```text
frontend/src/pages/
  ResearchDashboard.jsx
  ProductBenchmark.jsx
  NewsRiskPanel.jsx
  EvaluationPanel.jsx
  PaperReplay.jsx
```

API contract:

- `POST /api/analyze`
- `POST /api/product-benchmark`
- `POST /api/eval/run`

前端保持 sample/mock fallback，因此后端或模型不可用时仍能展示完整 demo。
