# Resume snippets for 资管投研 / 金融算法方向

## Version A: technical project bullets

资管投研辅助 Agent 系统｜Python, LangGraph, FastAPI, Qwen LoRA Adapter, pandas, React

- 构建 `data_extraction_agent → fundamental_agent → technical_agent → news_risk_agent → product_benchmark_agent → risk_guardrail_agent → report_agent` 的 LangGraph 工作流，自动生成可追溯 Markdown 投研辅助报告。
- 封装 sample 行情/净值、模拟基本面与估值字段、新闻文本和理财产品对标工具，统一 tool call schema、指标口径、异常处理与报告结构。
- 实现 Qwen LoRA 风险/情绪模型 adapter，并保留 rule-based fallback，确保无 GPU、无本地模型权重时仍可运行完整 demo。
- 建立评测脚本与 `eval/results.json`，统计 tool call success、报告格式通过、指标一致性、风险提示覆盖、guardrail 失败率和端到端延迟。
- 搭建 React/Vite 前端工作台，包含研究仪表盘、产品对标、新闻风险、评测面板和教学回放页面，展示投研流程而非交易执行。

## Version B: concise project bullets

资管投研辅助 Agent 系统｜Python, FastAPI, pandas, React

- 搭建面向资管研究的 Agent MVP，将 sample 行情/净值、新闻文本和同业产品表统一接入，自动计算收益率、波动率、最大回撤、Sharpe 等指标并生成结构化报告。
- 构建新闻风险与合规检查模块，对监管、价格、库存、违约等风险信号进行摘要，拦截交易方向、收益承诺和确定性判断类措辞，保留人工复核环节。
- 设计小规模评测集，验证报告格式、指标一致性、风险提示覆盖和 guardrail 规则，支持后续接入 Qwen LoRA 情绪/风险分类模型。

## Wealth product internship bullets

施罗德交银理财｜产品部实习生

- 分渠道梳理 200+ 款同业理财产品，基于 Python 搭建产品清单、净值表与市场业绩数据的清洗和匹配流程，自动计算收益率、最大回撤、波动率、Sharpe 等指标并输出同业排名，支持产品迭代、渠道定价与竞品分析。
- 将投资部周报/月报、净值对比、产品发行材料与参数替换流程模板化，沉淀 Excel/Word 批处理、二维码生成、发行排期整理等自动化工具，统一指标口径并缩短报表制作周期。

## Home Credit project bullets

Home Credit 消费金融信用风险稳定性建模｜Kaggle Bronze Medal, LightGBM, CatBoost, Polars

- 基于 Home Credit 多表信贷申请、征信与还款数据构建客户违约风险预测模型，围绕 Gini stability 目标设计按周级别的验证流程，评估模型排序能力与跨时间稳定性。
- 使用 Polars 搭建多表数据清洗、聚合与特征工程管线，联结申请表、历史借贷、征信及还款记录等数据源，生成高维候选特征并进行内存优化。
- 结合 StratifiedGroupKFold、LightGBM 与 CatBoost 训练多组模型，进行候选参数筛选与 soft voting 融合，最终获得 Kaggle Bronze Medal（221/3856）。
