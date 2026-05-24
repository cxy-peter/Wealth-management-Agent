import { GitBranch, Loader2, RefreshCw } from 'lucide-react';
import { useState } from 'react';

import { getDataLineage, getJobEvents } from '../api.js';
import { contextualBanditResults, dataFreshnessMock, dpoAgentEvalMock, evalResults } from '../data/mockData.js';

function pct(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function StrategyCard({ name, data }) {
  const distribution = data.action_distribution || {};
  const total = Object.values(distribution).reduce((sum, value) => sum + Number(value || 0), 0) || 1;
  return (
    <div className="panel">
      <div className="section-title">
        <span>{name}</span>
        <strong>reward {Number(data.average_reward || 0).toFixed(4)}</strong>
      </div>
      <div className="two-column-facts">
        <div>
          <span>Avg latency</span>
          <strong>{Number(data.average_latency_ms || 0).toFixed(1)} ms</strong>
        </div>
        <div>
          <span>Verifier pass</span>
          <strong>{pct(data.verifier_pass_rate)}</strong>
        </div>
        <div>
          <span>Regret</span>
          <strong>{Number(data.regret_vs_oracle || 0).toFixed(4)}</strong>
        </div>
        <div>
          <span>Forbidden fail</span>
          <strong>{pct(data.forbidden_wording_fail_rate)}</strong>
        </div>
      </div>
      <div className="distribution-bars">
        {Object.entries(distribution).map(([action, count]) => (
          <div key={action}>
            <span>{action}</span>
            <div>
              <i style={{ width: `${(Number(count) / total) * 100}%` }} />
            </div>
            <strong>{count}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function AdvancedEval() {
  const strategies = contextualBanditResults.strategies || {};
  return (
    <div className="page-stack nested-stack">
      <section className="metric-grid compact">
        <div className="metric-tile green">
          <span>Contextual cases</span>
          <strong>{contextualBanditResults.case_count}</strong>
        </div>
        <div className="metric-tile">
          <span>Best policy</span>
          <strong>{contextualBanditResults.best_policy}</strong>
        </div>
        <div className="metric-tile amber">
          <span>Report eval</span>
          <strong>{pct(evalResults.metrics.report_format_pass)}</strong>
        </div>
      </section>
      <section className="split-grid triple">
        {Object.entries(strategies).map(([name, data]) => (
          <StrategyCard key={name} name={name} data={data} />
        ))}
      </section>
    </div>
  );
}

function DpoPanel({ dpoTrace }) {
  const samples = dpoTrace?.samples || [];
  return (
    <section className="panel">
      <div className="section-title">
        <span>DPO chosen / rejected</span>
        <strong>{dpoTrace?.pair_count || samples.length} pairs</strong>
      </div>
      <div className="split-grid">
        {samples.slice(0, 2).map((item) => (
          <div className="two-column-facts" key={item.id}>
            <div>
              <span>chosen</span>
              <strong>{item.chosen}</strong>
            </div>
            <div>
              <span>rejected</span>
              <strong>{item.rejected}</strong>
            </div>
          </div>
        ))}
        {!samples.length ? <p className="panel-copy">暂无 DPO 样本，默认仅做数据集校验。</p> : null}
      </div>
    </section>
  );
}

function DpoAlignmentPanel({ analysis }) {
  const samples = analysis.dpo_trace?.samples || [];
  const metrics = dpoAgentEvalMock.variants || {};
  return (
    <div className="page-stack nested-stack">
      <section className="split-grid">
        <div className="panel">
          <div className="section-title">
            <span>DPO preference sample</span>
            <strong>{samples.length || 1}</strong>
          </div>
          <pre className="json-block">{JSON.stringify(samples[0] || {
            hard_negative_type: 'source_overclaim',
            chosen: '数字一致、证据充分、包含风险提示，不输出投资建议。',
            rejected: '把 synthetic/mock 写成真实全市场数据，缺少 evidence_id。'
          }, null, 2)}</pre>
        </div>
        <div className="panel">
          <div className="section-title">
            <span>DPO eval metrics</span>
            <strong>{dpoAgentEvalMock.training_status}</strong>
          </div>
          <pre className="json-block">{JSON.stringify(metrics, null, 2)}</pre>
        </div>
      </section>
      <section className="split-grid">
        <div className="panel">
          <div className="section-title">
            <span>Baseline output</span>
            <strong>template/base</strong>
          </div>
          <p className="panel-copy">模板基线能保留 evidence_id，但风险提示和分位解释覆盖不足；zero-shot/base 输出容易泛化。</p>
        </div>
        <div className="panel">
          <div className="section-title">
            <span>DPO output</span>
            <strong>fallback/demo</strong>
          </div>
          <p className="panel-copy">{analysis.dpo_report?.generated_text || '未配置 adapter 时展示 DPO-aligned 模板输出；若配置本地 adapter，输出仍需 verifier 与 guardrail 复核。'}</p>
        </div>
      </section>
    </div>
  );
}

function LineagePanel({ lineage, evidenceIds, onLookup }) {
  return (
    <div className="page-stack nested-stack">
      <section className="panel">
        <div className="section-title">
          <span>Data Lineage</span>
          <strong>{evidenceIds.length} evidence ids</strong>
        </div>
        <div className="evidence-list">
          {evidenceIds.slice(0, 12).map((evidenceId) => (
            <button className="evidence-row clickable-row" key={evidenceId} onClick={() => onLookup(evidenceId)}>
              <strong>{evidenceId}</strong>
              <span>点击查询 source_type / source_name / parser_version</span>
            </button>
          ))}
        </div>
      </section>
      <section className="split-grid">
        <div className="panel">
          <div className="section-title">
            <span>Lineage result</span>
            <strong>{lineage?.source_type || 'mock'}</strong>
          </div>
          <pre className="json-block">{JSON.stringify(lineage || dataFreshnessMock.sources[0], null, 2)}</pre>
        </div>
        <div className="panel">
          <div className="section-title">
            <span>Source boundary</span>
            <strong>official vs synthetic</strong>
          </div>
          <p className="panel-copy">official_disclosure_sample 只代表公开披露样本；synthetic_weekly_snapshot 只用于 demo 和回测，不代表真实全市场排名。</p>
        </div>
      </section>
    </div>
  );
}

export default function AgentTraceView({ analysis }) {
  const [activeTab, setActiveTab] = useState('trace');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('current weekly run');
  const [events, setEvents] = useState(analysis.agent_events || []);
  const [toolCalls, setToolCalls] = useState(analysis.tool_calls || []);
  const [lineage, setLineage] = useState(null);

  async function refreshTrace() {
    if (!analysis.run_id) return;
    setLoading(true);
    try {
      const payload = await getJobEvents(analysis.run_id);
      setEvents(payload.events || []);
      setToolCalls(payload.tool_calls || []);
      setStatus('backend audit store');
    } catch {
      setEvents(analysis.agent_events || []);
      setToolCalls(analysis.tool_calls || []);
      setStatus('local fallback trace');
    } finally {
      setLoading(false);
    }
  }

  const planner = analysis.planner_plan || {};
  const verifier = analysis.verification_result || {};
  const guardrail = analysis.guardrail || analysis.compliance_boundary || {};
  const evidenceIds = analysis.evidence_ids || [];

  async function lookupLineage(evidenceId) {
    try {
      setLineage(await getDataLineage(evidenceId));
    } catch {
      setLineage({ evidence_id: evidenceId, source_type: 'synthetic_weekly_snapshot', source_name: 'local mock fallback', found: false });
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
        <button className={activeTab === 'trace' ? 'active' : ''} onClick={() => setActiveTab('trace')}>Trace</button>
        <button className={activeTab === 'verify' ? 'active' : ''} onClick={() => setActiveTab('verify')}>Verifier / Guardrail</button>
        <button className={activeTab === 'lineage' ? 'active' : ''} onClick={() => setActiveTab('lineage')}>Data Lineage</button>
        <button className={activeTab === 'dpo' ? 'active' : ''} onClick={() => setActiveTab('dpo')}>DPO Alignment</button>
        <button className={activeTab === 'eval' ? 'active' : ''} onClick={() => setActiveTab('eval')}>Advanced Eval</button>
      </div>
      {activeTab === 'eval' ? <AdvancedEval /> : null}
      {activeTab === 'dpo' ? <DpoAlignmentPanel analysis={analysis} /> : null}
      {activeTab === 'lineage' ? <LineagePanel lineage={lineage} evidenceIds={evidenceIds} onLookup={lookupLineage} /> : null}
      {activeTab === 'verify' ? (
        <section className="split-grid">
          <div className="panel">
            <div className="section-title">
              <span>Verifier result</span>
              <strong>{verifier.pass ? 'pass' : 'review'}</strong>
            </div>
            <pre className="json-block">{JSON.stringify(verifier, null, 2)}</pre>
          </div>
          <div className="panel">
            <div className="section-title">
              <span>Guardrail result</span>
              <strong>{guardrail.forbidden_wording_hit ? 'hit' : 'clean'}</strong>
            </div>
            <pre className="json-block">{JSON.stringify(guardrail, null, 2)}</pre>
          </div>
        </section>
      ) : null}
      {activeTab === 'trace' ? (
        <>
          <section className="split-grid">
            <div className="panel">
              <div className="section-title">
                <span>Planner plan</span>
                <strong>{planner.task_type || 'standard_weekly_report'}</strong>
              </div>
              <pre className="json-block">{JSON.stringify(planner, null, 2)}</pre>
            </div>
            <div className="panel">
              <div className="section-title">
                <span>Evidence ids</span>
                <strong>{(analysis.evidence_ids || []).length}</strong>
              </div>
              <pre className="json-block">{JSON.stringify(analysis.evidence_ids || [], null, 2)}</pre>
            </div>
          </section>
          <section className="table-panel">
            <table>
              <thead>
                <tr><th>Tool call</th><th>Tool</th><th>Status</th><th>Latency</th><th>Evidence</th></tr>
              </thead>
              <tbody>
                {toolCalls.map((item) => (
                  <tr key={item.tool_call_id}>
                    <td>{item.tool_call_id}</td>
                    <td>{item.tool_name}</td>
                    <td>{item.success ? 'pass' : 'fail'}</td>
                    <td>{Number(item.latency_ms || 0).toFixed(1)} ms</td>
                    <td>{(item.evidence_ids || []).join(', ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          <section className="panel">
            <div className="section-title">
              <span>Agent events</span>
              <strong>{events.length}</strong>
            </div>
            <div className="timeline-list">
              {events.map((item, index) => (
                <div className="timeline-item" key={`${item.agent_name}-${item.event_type}-${index}`}>
                  <strong>{item.agent_name}</strong>
                  <span>{item.event_type}</span>
                  <pre>{JSON.stringify(item.payload || {}, null, 2)}</pre>
                </div>
              ))}
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}
