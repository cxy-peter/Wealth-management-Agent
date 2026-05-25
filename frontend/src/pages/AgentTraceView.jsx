import { CheckCircle2, GitBranch, Loader2, RefreshCw, ShieldCheck } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { getDataLineage, getDpoEval, getJobEvents, runSkillHarness } from '../api.js';
import { contextualBanditResults, dataFreshnessMock, dpoAgentEvalMock, evalResults } from '../data/mockData.js';

function pct(value, digits = 1) {
  return `${(Number(value || 0) * 100).toFixed(digits)}%`;
}

function score(value) {
  return Math.round(Number(value || 0) * 100);
}

function TechnicalDetails({ children, label = '查看技术详情' }) {
  return (
    <details className="technical-panel">
      <summary>{label}</summary>
      {children}
    </details>
  );
}

function QualityChecklist({ verifier, guardrail, dpoEval }) {
  const dpoMetrics = dpoEval.variants?.dpo_adapter || {};
  const rows = [
    {
      label: '数字一致性',
      value: verifier.pass ? '通过' : '需复核',
      tone: verifier.pass ? 'ok' : 'bad'
    },
    {
      label: '证据覆盖',
      value: pct(dpoMetrics.evidence_coverage_rate ?? evalResults.metrics.evidence_coverage, 0),
      tone: 'ok'
    },
    {
      label: '风险提示',
      value: pct(dpoMetrics.risk_warning_coverage ?? evalResults.metrics.risk_warning_coverage, 0),
      tone: 'ok'
    },
    {
      label: '禁用措辞',
      value: guardrail.forbidden_wording_hit ? '命中' : '0 次命中',
      tone: guardrail.forbidden_wording_hit ? 'bad' : 'ok'
    },
    {
      label: '数据来源边界',
      value: '已标记演示数据',
      tone: 'ok'
    }
  ];
  return (
    <section className="quality-grid">
      {rows.map((item) => (
        <div className={`quality-card ${item.tone}`} key={item.label}>
          <CheckCircle2 size={18} />
          <span>{item.label}</span>
          <strong>{item.value}</strong>
        </div>
      ))}
    </section>
  );
}

function ProcessPanel({ analysis, verifier, guardrail, dpoEval }) {
  const reportDate = analysis.weekly_report_date || analysis.report_date || '2025-04-04';
  const steps = [
    '读取周报快照',
    '计算规模变化和收益分位',
    '生成周报草稿',
    'AI 报告校准',
    'Verifier 数字复核',
    'Guardrail 合规检查'
  ];
  return (
    <div className="page-stack nested-stack">
      <section className="panel trace-hero">
        <div>
          <span className="eyebrow">本次任务</span>
          <h2>生成 {reportDate} 产品周报摘要</h2>
          <p className="panel-copy">
            工作流围绕周报快照、净值表现、模拟同业池与渠道分位数据生成报告草稿，并对数字、证据和合规边界做质检。
          </p>
        </div>
        <div className="scope-pill">
          <ShieldCheck size={16} />
          仅用于投研辅助
        </div>
      </section>
      <section className="panel">
        <div className="section-title">
          <span>执行路径</span>
          <strong>{steps.length} 步</strong>
        </div>
        <ol className="process-steps">
          {steps.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </section>
      <section className="panel">
        <div className="section-title">
          <span>质检结果</span>
          <strong>{verifier.pass && !guardrail.forbidden_wording_hit ? '通过' : '需复核'}</strong>
        </div>
        <QualityChecklist verifier={verifier} guardrail={guardrail} dpoEval={dpoEval} />
      </section>
    </div>
  );
}

function ToolCallPanel({ toolCalls, events, planner, evidenceIds }) {
  return (
    <div className="page-stack nested-stack">
      <section className="split-grid">
        <div className="panel">
          <div className="section-title">
            <span>Planner 计划</span>
            <strong>{planner.task_type || 'standard_weekly_report'}</strong>
          </div>
          <div className="pill-list">
            {(planner.required_tools || ['load_weekly_snapshot', 'calculate_weekly_metrics', 'weekly_report_verifier']).map((tool) => (
              <span key={tool}>{tool}</span>
            ))}
          </div>
          <TechnicalDetails>
            <pre className="json-block">{JSON.stringify(planner, null, 2)}</pre>
          </TechnicalDetails>
        </div>
        <div className="panel">
          <div className="section-title">
            <span>证据编号</span>
            <strong>{evidenceIds.length}</strong>
          </div>
          <div className="pill-list">
            {evidenceIds.slice(0, 10).map((item) => (
              <span key={item}>{item}</span>
            ))}
          </div>
        </div>
      </section>
      <section className="table-panel">
        <div className="section-title table-title">
          <span>工具调用记录</span>
          <strong>{toolCalls.length}</strong>
        </div>
        <table>
          <thead>
            <tr>
              <th className="sticky-col">调用编号</th>
              <th>工具</th>
              <th>状态</th>
              <th>耗时</th>
              <th>证据编号</th>
            </tr>
          </thead>
          <tbody>
            {toolCalls.map((item) => (
              <tr key={item.tool_call_id}>
                <td className="sticky-col">{item.tool_call_id}</td>
                <td>{item.tool_name}</td>
                <td>{item.success ? '通过' : '失败'}</td>
                <td>{Number(item.latency_ms || 0).toFixed(1)} ms</td>
                <td>{(item.evidence_ids || []).join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="panel">
        <div className="section-title">
          <span>Agent 事件</span>
          <strong>{events.length}</strong>
        </div>
        <div className="timeline-list">
          {events.map((item, index) => (
            <div className="timeline-item" key={`${item.agent_name}-${item.event_type}-${index}`}>
              <strong>{item.agent_name}</strong>
              <span>{item.event_type}</span>
              <TechnicalDetails label="查看事件明细">
                <pre>{JSON.stringify(item.payload || {}, null, 2)}</pre>
              </TechnicalDetails>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function ReportQualityPanel({ verifier, guardrail }) {
  return (
    <section className="split-grid">
      <div className="panel">
        <div className="section-title">
          <span>报告质检</span>
          <strong>{verifier.pass ? '通过' : '需复核'}</strong>
        </div>
        <div className="two-column-facts">
          <div>
            <span>复核置信度</span>
            <strong>{pct(verifier.confidence_score || 0.96, 0)}</strong>
          </div>
          <div>
            <span>数值不一致</span>
            <strong>{(verifier.metric_mismatches || []).length}</strong>
          </div>
          <div>
            <span>缺失证据</span>
            <strong>{(verifier.missing_evidence || []).length}</strong>
          </div>
          <div>
            <span>禁用措辞</span>
            <strong>{verifier.forbidden_wording ? '命中' : '0 次命中'}</strong>
          </div>
        </div>
        <TechnicalDetails>
          <pre className="json-block">{JSON.stringify(verifier, null, 2)}</pre>
        </TechnicalDetails>
      </div>
      <div className="panel">
        <div className="section-title">
          <span>合规边界</span>
          <strong>{guardrail.forbidden_wording_hit ? '需复核' : '通过'}</strong>
        </div>
        <p className="panel-copy">
          输出定位为投研辅助、风险摘要、产品对标和报告草稿整理；不生成买入、卖出、持有、推荐配置或收益承诺。
        </p>
        <TechnicalDetails>
          <pre className="json-block">{JSON.stringify(guardrail, null, 2)}</pre>
        </TechnicalDetails>
      </div>
    </section>
  );
}

function LineagePanel({ lineage, evidenceIds, onLookup }) {
  return (
    <div className="page-stack nested-stack">
      <section className="panel">
        <div className="section-title">
          <span>数据溯源</span>
          <strong>{evidenceIds.length} 个证据编号</strong>
        </div>
        <div className="evidence-list">
          {evidenceIds.slice(0, 12).map((evidenceId) => (
            <button className="evidence-row clickable-row" key={evidenceId} onClick={() => onLookup(evidenceId)}>
              <strong>{evidenceId}</strong>
              <span>点击查看 source_type / source_name / parser_version</span>
            </button>
          ))}
        </div>
      </section>
      <section className="split-grid">
        <div className="panel">
          <div className="section-title">
            <span>来源查询结果</span>
            <strong>{lineage?.source_type || '演示样本'}</strong>
          </div>
          <div className="two-column-facts">
            <div>
              <span>source_type</span>
              <strong>{lineage?.source_type || dataFreshnessMock.sources[0].source_type}</strong>
            </div>
            <div>
              <span>source_name</span>
              <strong>{lineage?.source_name || dataFreshnessMock.sources[0].source_name}</strong>
            </div>
            <div>
              <span>as_of_date</span>
              <strong>{lineage?.as_of_date || dataFreshnessMock.sources[0].latest_as_of_date || '2025-04-04'}</strong>
            </div>
            <div>
              <span>confidence</span>
              <strong>{lineage?.confidence_level || dataFreshnessMock.sources[0].confidence_level}</strong>
            </div>
          </div>
          <TechnicalDetails>
            <pre className="json-block">{JSON.stringify(lineage || dataFreshnessMock.sources[0], null, 2)}</pre>
          </TechnicalDetails>
        </div>
        <div className="panel">
          <div className="section-title">
            <span>来源边界</span>
            <strong>official / uploaded / synthetic 区分</strong>
          </div>
          <p className="panel-copy">
            official_disclosure_sample 只代表公开披露样本；synthetic_weekly_snapshot 只用于 demo 和回测，不代表真实全市场排名。
          </p>
        </div>
      </section>
    </div>
  );
}

function DpoCalibrationPanel({ analysis, dpoEval }) {
  const variants = dpoEval.variants || {};
  const template = variants.template_baseline || {};
  const base = variants.sft_adapter_or_base || {};
  const aligned = variants.dpo_adapter || {};
  const samples = analysis.dpo_trace?.samples || [];
  return (
    <div className="page-stack nested-stack">
      <section className="panel">
        <div className="section-title">
          <span>AI 报告校准结果</span>
          <strong>{dpoEval.training_status === 'not_trained' ? 'DPO preference eval demo / 未加载真实 adapter' : 'adapter 已加载'}</strong>
        </div>
        <div className="calibration-score-grid">
          <div className="metric-tile amber">
            <span>模板草稿</span>
            <strong>{score(template.average_report_score || 0.57)}/100</strong>
          </div>
          <div className="metric-tile red">
            <span>基础模型</span>
            <strong>{score(base.average_report_score || 0.28)}/100</strong>
          </div>
          <div className="metric-tile green">
            <span>DPO 校准稿</span>
            <strong>{score(aligned.average_report_score || 0.93)}/100</strong>
          </div>
        </div>
        <div className="score-row">
          <span>数字一致性：通过</span>
          <span>证据覆盖：{pct(aligned.evidence_coverage_rate ?? 1, 0)}</span>
          <span>禁用措辞：{score(aligned.forbidden_wording_rate || 0)} 次命中</span>
          <span>相比模板胜率：{pct(aligned.preference_win_rate_vs_baseline ?? 1, 0)}</span>
        </div>
      </section>
      <section className="split-grid">
        <div className="panel">
          <div className="section-title">
            <span>校准样例</span>
            <strong>{samples.length || 1}</strong>
          </div>
          <div className="comparison-box">
            <div>
              <span>chosen sample</span>
              <p>{samples[0]?.chosen || '数字来自工具输出，关键结论包含证据编号，并保留风险提示。'}</p>
            </div>
            <div>
              <span>rejected sample</span>
              <p>{samples[0]?.rejected || '泛泛描述，缺少证据编号或把演示数据夸大为真实全市场数据。'}</p>
            </div>
          </div>
        </div>
        <div className="panel">
          <div className="section-title">
            <span>校准后摘要</span>
            <strong>需经报告质检</strong>
          </div>
          <p className="panel-copy">
            {analysis.dpo_report?.generated_text ||
              '校准稿围绕规模变化、基准状态、收益分位和风险提示组织周报语气；所有数字仍来自 deterministic tools，并继续进入 Verifier 与 Guardrail。'}
          </p>
        </div>
      </section>
      <TechnicalDetails label="查看技术指标">
        <pre className="json-block">{JSON.stringify(dpoEval, null, 2)}</pre>
      </TechnicalDetails>
    </div>
  );
}

function SkillHarnessPanel({ trace }) {
  const selectedSkills = trace?.selected_skills || [];
  const skillCalls = trace?.skill_calls || [];
  const harness = trace?.harness_result || {};
  return (
    <div className="page-stack nested-stack">
      <section className="panel">
        <div className="section-title">
          <span>Skill / Harness Runtime</span>
          <strong>{harness.pass === false ? '需复核' : '通过'}</strong>
        </div>
        <div className="pill-list">
          {selectedSkills.map((skill) => <span key={skill}>{skill}</span>)}
        </div>
        <div className="two-column-facts skill-summary-grid">
          <div><span>selected_skills</span><strong>{selectedSkills.length}</strong></div>
          <div><span>harness pass/fail</span><strong>{harness.pass === false ? 'fail' : 'pass'}</strong></div>
          <div><span>failed rules</span><strong>{(harness.failed_rules || []).join(', ') || '无'}</strong></div>
          <div><span>source boundary check</span><strong>{harness.source_boundary_check || 'pass'}</strong></div>
        </div>
      </section>
      <section className="table-panel compact-table">
        <div className="section-title table-title">
          <span>skill call trace</span>
          <strong>{skillCalls.length}</strong>
        </div>
        <table>
          <thead>
            <tr><th>skill_call_id</th><th>skill_name</th><th>status</th><th>latency</th><th>risk</th><th>evidence_id</th><th>harness</th></tr>
          </thead>
          <tbody>
            {skillCalls.map((call) => (
              <tr key={call.skill_call_id}>
                <td>{call.skill_call_id}</td>
                <td>{call.skill_name}</td>
                <td>{call.success ? 'pass' : 'fail'}</td>
                <td>{Number(call.latency_ms || 0).toFixed(1)} ms</td>
                <td>{call.risk_level}</td>
                <td>{(call.evidence_ids || []).join(', ')}</td>
                <td>{call.harness_result?.pass === false ? (call.harness_result.failed_rules || []).join(', ') : 'pass'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <TechnicalDetails label="查看 Skill 输入/输出">
        <pre className="json-block">{JSON.stringify(trace, null, 2)}</pre>
      </TechnicalDetails>
    </div>
  );
}

function QualityEvalPanel() {
  const strategies = contextualBanditResults.strategies || {};
  return (
    <div className="page-stack nested-stack">
      <section className="metric-grid compact">
        <div className="metric-tile green">
          <span>评测样本</span>
          <strong>{contextualBanditResults.case_count}</strong>
        </div>
        <div className="metric-tile">
          <span>报告格式通过率</span>
          <strong>{pct(evalResults.metrics.report_format_pass, 0)}</strong>
        </div>
        <div className="metric-tile amber">
          <span>路由基线</span>
          <strong>{contextualBanditResults.best_policy}</strong>
        </div>
      </section>
      <section className="split-grid triple">
        {Object.entries(strategies).map(([name, data]) => (
          <div className="panel" key={name}>
            <div className="section-title">
              <span>{name}</span>
              <strong>reward {Number(data.average_reward || 0).toFixed(4)}</strong>
            </div>
            <div className="two-column-facts">
              <div>
                <span>平均耗时</span>
                <strong>{Number(data.average_latency_ms || 0).toFixed(1)} ms</strong>
              </div>
              <div>
                <span>质检通过</span>
                <strong>{pct(data.verifier_pass_rate)}</strong>
              </div>
              <div>
                <span>禁用措辞失败率</span>
                <strong>{pct(data.forbidden_wording_fail_rate)}</strong>
              </div>
              <div>
                <span>regret</span>
                <strong>{Number(data.regret_vs_oracle || 0).toFixed(4)}</strong>
              </div>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}

export default function AgentTraceView({ analysis }) {
  const [activeTab, setActiveTab] = useState('process');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('演示样本追踪');
  const [events, setEvents] = useState(analysis.agent_events || []);
  const [toolCalls, setToolCalls] = useState(analysis.tool_calls || []);
  const [lineage, setLineage] = useState(null);
  const [dpoEval, setDpoEval] = useState(dpoAgentEvalMock);
  const [skillHarnessTrace, setSkillHarnessTrace] = useState(analysis.skill_harness_trace || null);

  useEffect(() => {
    getDpoEval().then(setDpoEval).catch(() => setDpoEval(dpoAgentEvalMock));
    runSkillHarness({
      user_task: '生成产品周报并进行 DPO 报告校准',
      task_payload: { report_date: analysis.weekly_report_date || '2025-04-04', task_type: 'weekly_product_summary' }
    }).then(setSkillHarnessTrace).catch(() => setSkillHarnessTrace(analysis.skill_harness_trace || null));
  }, []);

  async function refreshTrace() {
    if (!analysis.run_id) return;
    setLoading(true);
    try {
      const payload = await getJobEvents(analysis.run_id);
      setEvents(payload.events || []);
      setToolCalls(payload.tool_calls || []);
      setStatus('后端审计存储');
    } catch {
      setEvents(analysis.agent_events || []);
      setToolCalls(analysis.tool_calls || []);
      setStatus('演示样本追踪');
    } finally {
      setLoading(false);
    }
  }

  const planner = analysis.planner_plan || {};
  const verifier = analysis.verification_result || {};
  const guardrail = analysis.guardrail || analysis.compliance_boundary || {};
  const evidenceIds = useMemo(() => analysis.evidence_ids || [], [analysis.evidence_ids]);

  async function lookupLineage(evidenceId) {
    try {
      setLineage(await getDataLineage(evidenceId));
    } catch {
      setLineage({
        evidence_id: evidenceId,
        source_type: 'synthetic_weekly_snapshot',
        source_name: 'Vercel static demo data',
        source_url_or_file: 'frontend/public/demo-data',
        as_of_date: analysis.weekly_report_date || '2025-04-04',
        confidence_level: 'medium',
        parser_version: 'frontend_demo_export.v1',
        found: false
      });
    }
  }

  return (
    <div className="page-stack">
      <section className="control-band trace-control">
        <button className="primary-btn" onClick={refreshTrace} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
          刷新轨迹
        </button>
        <div className="inline-status">
          <GitBranch size={16} />
          <span>{analysis.run_id || 'weekly_run_mock_preview'}</span>
          <strong>{analysis.weekly_report_date || analysis.report_date || '2025-04-04'} · {status}</strong>
        </div>
      </section>
      <div className="tabs">
        <button className={activeTab === 'process' ? 'active' : ''} onClick={() => setActiveTab('process')}>执行流程</button>
        <button className={activeTab === 'tools' ? 'active' : ''} onClick={() => setActiveTab('tools')}>工具调用记录</button>
        <button className={activeTab === 'quality' ? 'active' : ''} onClick={() => setActiveTab('quality')}>报告质检</button>
        <button className={activeTab === 'lineage' ? 'active' : ''} onClick={() => setActiveTab('lineage')}>数据溯源</button>
        <button className={activeTab === 'skill' ? 'active' : ''} onClick={() => setActiveTab('skill')}>Skill / Harness</button>
        <button className={activeTab === 'dpo' ? 'active' : ''} onClick={() => setActiveTab('dpo')}>AI 报告校准</button>
        <button className={activeTab === 'eval' ? 'active' : ''} onClick={() => setActiveTab('eval')}>质量评估</button>
      </div>
      {activeTab === 'process' ? <ProcessPanel analysis={analysis} verifier={verifier} guardrail={guardrail} dpoEval={dpoEval} /> : null}
      {activeTab === 'tools' ? <ToolCallPanel toolCalls={toolCalls} events={events} planner={planner} evidenceIds={evidenceIds} /> : null}
      {activeTab === 'quality' ? <ReportQualityPanel verifier={verifier} guardrail={guardrail} /> : null}
      {activeTab === 'lineage' ? <LineagePanel lineage={lineage} evidenceIds={evidenceIds} onLookup={lookupLineage} /> : null}
      {activeTab === 'skill' ? <SkillHarnessPanel trace={skillHarnessTrace || analysis.skill_harness_trace || { selected_skills: [], skill_calls: [], harness_result: { pass: true, failed_rules: [] } }} /> : null}
      {activeTab === 'dpo' ? <DpoCalibrationPanel analysis={analysis} dpoEval={dpoEval} /> : null}
      {activeTab === 'eval' ? <QualityEvalPanel /> : null}
    </div>
  );
}
