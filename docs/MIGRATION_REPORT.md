# Migration Report

## Scope

本次升级把项目从泛投研 Agent demo 进一步收敛为“周报型资管产品研究与对标工作台”。新增能力均保留 sample/mock fallback，不依赖外部 API key、GPU、真实客户数据或内部文件。

## Capability Audit

| Capability | Current status | Evidence in repo | Notes |
|---|---|---|---|
| `create_react_agent` | Optional adapter | `backend/app/agents/react_common.py` | 配置 LLM key 后可构建 ReAct-capable agent；默认走 deterministic tool pipeline。 |
| `get_mcp_tools` | Async helper | `backend/app/mcp/client.py` | 可连接本地 sample MCP server；默认 workflow 不依赖外部 MCP 进程。 |
| `MultiServerMCPClient` | Implemented | `backend/app/mcp/client.py` | 通过 `langchain_mcp_adapters.client` 配置。 |
| `langchain_mcp_adapters` | Dependency path present | `requirements.txt`, `backend/app/mcp/client.py` | 仅作为可选 MCP-capable 路径。 |
| `add_conditional_edges` | Active | `backend/app/agents/workflow.py` | Planner 动态路由，避免固定跑全部节点。 |
| `checkpointer` | Enabled | `backend/app/agents/workflow.py` | LangGraph 使用 MemorySaver，run_id 作为 thread_id。 |
| `interrupt` | Fallback pending-review | `backend/app/agents/human_review_agent.py` | 当前优先落地 pending_review 状态和审核 API。 |
| `tool_call trace` | Active | `backend/app/tools/tool_registry.py`, `backend/app/storage.py` | tool_call_id、evidence_ids、latency、success 写入审计。 |

## 已迁移能力

- Planner + conditional LangGraph 工作流。
- Tool Registry 和本地 MCP-capable sample tools。
- Verifier、Guardrail、Human Review、SQLite audit trace。
- 产品对标指标计算和 evidence_id 追溯。
- LinUCB contextual bandit 路由评测。

## 新增周报型能力

- `scripts/generate_weekly_report_universe.py` 生成周报快照、规模历史、NAV、市场发行、同业产品池和 DPO preference data。
- `backend/app/weekly_report/` 新增 parser、scale/return/percentile/benchmark metrics、weekly/benchmark report generator。
- `backend/app/weekly_report/weekly_report_verifier.py` 复核规模变化、NAV 指标、分位、基准状态、证据和合规边界。
- 前端收敛为 `WeeklyReportDashboard`、`ProductBenchmarkWorkbench`、`AgentTraceView` 三页。

## 概念复用但未完全迁移

- 外部实时行情、真实产品接口和真实新闻接口：仅保留 `.env` 可配置 adapter 思路，默认不启用。
- 真正 LLM 驱动的 ReAct 推理：路径已准备，默认关闭，避免 API key 成为 demo 前置条件。
- LangGraph interrupt 阻塞式人工确认：当前实现为 pending_review 状态与审核 API。
- 多 MCP server federation：当前只覆盖本地 sample/mock server。

## 下一步待补

- 将 weekly_report 工具接入统一 Tool Registry，形成完整 tool_call trace。
- 为真实数据 adapter 增加凭证加载、脱敏日志、速率限制和缓存。
- 将 pending_review 升级为可恢复 checkpoint/interrupt flow。
- 扩展周报 verifier 到更多格式化报告字段和 cross-period anomaly check。
