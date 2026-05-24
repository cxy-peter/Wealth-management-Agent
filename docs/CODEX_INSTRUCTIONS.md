# Codex implementation notes

本仓库定位为 `wealth-research-agent`：面向资管投研、理财产品研究、金融算法实习投递的可运行 demo。

## Hard constraints

1. 所有页面、API 和报告统一定位为投研辅助、风险摘要、产品对标、研究报告生成。
2. 不输出交易方向、收益承诺或确定性上涨判断。
3. 不提交密钥、私有数据、真实客户数据或公司内部文件。
4. 默认数据只来自 `data/` 下 sample/mock 文件；真实接口只能通过 `.env` 或 CLI 参数配置。
5. 每个结论必须能追溯到样例数据、指标工具、新闻风险证据或 guardrail。

## Backend architecture

```text
data_extraction_agent
  -> fundamental_agent
  -> technical_agent
  -> news_risk_agent
  -> product_benchmark_agent
  -> risk_guardrail_agent
  -> report_agent
```

关键文件：

- `backend/app/agents/workflow.py`: LangGraph workflow。
- `backend/app/models/qwen_risk_adapter.py`: 可选 Qwen LoRA 风险/情绪 adapter。
- `backend/app/tools/news_risk.py`: 规则兜底。
- `backend/app/evaluation.py`: CLI 与 API 共用评测逻辑。
- `eval/results.json`: 当前评测输出。

## Frontend architecture

```text
frontend/src/pages/
  ResearchDashboard.jsx
  ProductBenchmark.jsx
  NewsRiskPanel.jsx
  EvaluationPanel.jsx
  PaperReplay.jsx
```

前端默认访问 `VITE_WEALTH_AGENT_API_BASE`，未配置时使用 `http://127.0.0.1:8000`。API 不可用时保留本地 mock 预览。

## Verification

```bash
python scripts/run_demo.py --symbol 600519 --company 贵州茅台
python eval/run_eval.py
cd frontend
npm install
npm run build
```
