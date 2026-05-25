# Resume snippets for 资管产品研究 / 金融算法 / Agent 工程方向

## Version A: technical project bullets

DPO-aligned Skill-Harness 资管产品周报 Agent｜Python, FastAPI, React, pandas, DPO Preference Data, Evidence Lineage

- 构建周报型资管产品研究 Agent，支持上传周报、净值、同业产品池和参考利率 CSV/XLSX，按 `own_company`、`full_market`、`reference_rates` 进行 dataset_scope 治理，并为每条记录生成 `upload_id`、`source_type`、`as_of_date`、`parser_version` 与 `evidence_id`。
- 将产品周报、竞品对标、全市场分位、渠道对标、同类绩优产品追踪和 5 只产品净值对比工程化，计算收益、波动、最大回撤、Sharpe、Calmar、benchmark excess、市场/渠道分位等指标，所有数值由 deterministic tools 计算。
- 设计 DPO Planner 与 DPO Report Writer：Planner 通过 JSON schema 校验后选择 Skill-Harness 路由，Report Writer 只做周报文风、证据覆盖、风险提示、分位解释和禁用措辞校准，不负责收益/回撤/分位计算。
- 实现 Skill-Harness Runtime，将 data upload、weekly summary、peer benchmark、channel benchmark、nav compare、DPO report、verifier 封装为可审计 skill call，并检查 required fields、numeric consistency、source boundary、required evidence 和 forbidden wording。
- 增加 Evidence Lineage 与 External Verification：区分 `manual_upload`、`synthetic_weekly_snapshot`、`official_public_nav`、`official_disclosure_sample`、`registry_lookup_sample`、`public_reference_rate_api`，并对官方净值、登记编码、参考利率和数据来源边界输出核验分数与复核提示。

## Version B: concise project bullets

DPO-aligned Skill-Harness 资管产品周报 Agent｜FastAPI, React, pandas, DPO, Verifier

- 构建资管产品周报工作台，支持上传产品周报/净值/同业对标/参考利率数据，自动完成字段映射、质量检查、数据来源标记和 evidence_id 生成。
- 设计产品系列归类与手工修正模块，支持系列业绩聚合、系列间收益风险对比、基准利率对比和 manual override trace。
- 实现竞品对标、全市场分位、渠道对标、同类绩优产品和 5 只产品净值对比，输出收益、波动、最大回撤、Sharpe、Calmar、benchmark excess 等可追溯指标。
- 设计 DPO Planner / Report Writer 偏好数据与 hard negatives，围绕工具选择、数字一致性、证据覆盖、风险提示、source boundary 和禁用投资建议措辞做报告校准。
- 构建 Verifier / Guardrail / Evidence Lineage / External Verification，保证报告定位为投研辅助、风险摘要、产品对标和周报草稿整理，不生成买入、卖出、持有或收益承诺。

## Interview framing

这个项目的核心不是“让大模型直接写投资结论”，而是把资管产品周报中的数据接入、指标计算、同业对标、来源治理、证据追踪、报告校准和合规边界做成一个可审计工作流。DPO 只用于 Planner 偏好和 Report Writer 文风/证据/风险提示对齐；收益、回撤、分位、Sharpe、Calmar 等数字仍由确定性工具计算，并经过 Verifier 与 Harness 复核。

## Wealth product internship bullets

施罗德交银理财｜产品部实习生

- 分渠道梳理 200+ 款同业理财产品，基于 Python 搭建产品清单、净值表与市场业绩数据的清洗和匹配流程，自动计算收益率、最大回撤、波动率、Sharpe 等指标并输出同业排名，支持产品迭代、渠道定价与竞品分析。
- 将投资部周报/月报、净值对比、产品发行材料与参数替换流程模板化，沉淀 Excel/Word 批处理、二维码生成、发行排期整理等自动化工具，统一指标口径并缩短报表制作周期。

## Home Credit project bullets

Home Credit 消费金融信用风险稳定性建模｜Kaggle Bronze Medal, LightGBM, CatBoost, Polars

- 基于 Home Credit 多表信贷申请、征信与还款数据构建客户违约风险预测模型，围绕 Gini stability 目标设计按周级别的验证流程，评估模型排序能力与跨时间稳定性。
- 使用 Polars 搭建多表数据清洗、聚合与特征工程管线，连接申请表、历史借贷、征信及还款记录等数据源，生成高维候选特征并进行内存优化。
- 结合 StratifiedGroupKFold、LightGBM 与 CatBoost 训练多组模型，进行候选参数筛选与 soft voting 融合，最终获得 Kaggle Bronze Medal。
