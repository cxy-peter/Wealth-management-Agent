# Migration Report

## Scope

本次升级把固定顺序 demo 改为 Planner + conditional LangGraph + ReAct/MCP adapter + verifier + guardrail + human review + audit persistence + route optimization。默认仍使用 `data/` 下 sample/mock 数据。

## Capability Audit

| Capability | Current status | Evidence in repo | Notes |
|---|---|---|---|
| `create_react_agent` | Optional adapter implemented | `backend/app/agents/react_common.py` | 有 API key 时可构建 LangGraph ReAct agent；默认走 deterministic tool pipeline。 |
| `get_mcp_tools` | Implemented as async helper | `backend/app/mcp/client.py` | 连接本地 sample MCP server；默认 workflow 不强依赖外部进程。 |
| `MultiServerMCPClient` | Implemented in MCP client | `backend/app/mcp/client.py` | 使用 `langchain_mcp_adapters.client`。 |
| `langchain_mcp_adapters` | Real dependency path present | `requirements.txt`, `backend/app/mcp/client.py` | 已加入 requirements。 |
| `add_conditional_edges` | Actively used | `backend/app/agents/workflow.py` | Planner 根据 required tools 动态路由，不再固定跑所有节点。 |
| `checkpointer` | MemorySaver checkpointer enabled | `backend/app/agents/workflow.py` | LangGraph compile 使用 MemorySaver；run_id 作为 thread_id。 |
| `interrupt` | Imported, pending-review fallback active | `backend/app/agents/human_review_agent.py` | 当前默认不阻塞流程，先落地 `pending_review` 状态与审核 API。 |
| `tool_call trace` | Actively used | `backend/app/tools/tool_registry.py`, `backend/app/storage.py` | 每个工具返回 `tool_call_id`、`evidence_ids`、latency、success，并写 SQLite。 |

## 已迁移自 financial-agent 的能力

- 多 Agent 分工：基本面、技术面、估值、新闻风险拆成独立 agent。
- ReAct tool-agent 形态：每个 agent 有工具白名单和可选 `create_react_agent` 路径。
- MCP 思路：本地 sample tools 暴露为 MCP server，并提供 `MultiServerMCPClient` 连接方法。
- 新闻风险模型扩展：保留 Qwen LoRA adapter，同时默认 rule-based fallback。

## 概念复用但未完全迁移的能力

- 外部实时行情、财报、新闻接口：当前只保留 `.env` 可配置扩展，不默认启用。
- 真正 LLM 驱动的 ReAct 推理：代码路径已准备，默认不开启，避免 API key 成为 demo 前置条件。
- LangGraph `interrupt` 阻塞式人工确认：当前实现为 pending-review 状态和审批 API。
- 多 MCP server federation：当前只接本地 sample/mock server。

## 下一步待补

- 为真实数据 adapter 增加独立凭证加载、速率限制、缓存和脱敏日志。
- 将 human review 从 pending 状态升级为可恢复的 interrupt/checkpoint flow。
- 扩展 route optimization case 到更多标的、产品类型和新闻风险场景。
- 增加前端 TraceView 的 diff 比对和审核历史视图。
