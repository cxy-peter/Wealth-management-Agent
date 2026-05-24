import { GitBranch, Loader2, RefreshCw } from 'lucide-react';
import { useState } from 'react';

import { getJobEvents } from '../api.js';
import { contextualBanditResults, evalResults, replayBars, routeOptimizationResults } from '../data/mockData.js';

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
          <span>Regret</span>
          <strong>{Number(data.regret_vs_oracle || 0).toFixed(4)}</strong>
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
          <span>Route reward</span>
          <strong>{Number(routeOptimizationResults.average_reward || 0).toFixed(3)}</strong>
        </div>
      </section>

      <section className="split-grid triple">
        {Object.entries(strategies).map(([name, data]) => (
          <StrategyCard key={name} name={name} data={data} />
        ))}
      </section>

      <section className="panel">
        <div className="section-title">
          <span>Report eval summary</span>
          <strong>{evalResults.cases?.length || 0} sample cases</strong>
        </div>
        <div className="two-column-facts">
          <div>
            <span>Tool success</span>
            <strong>{pct(evalResults.metrics.tool_call_success)}</strong>
          </div>
          <div>
            <span>Metric consistency</span>
            <strong>{pct(evalResults.metrics.metric_consistency)}</strong>
          </div>
          <div>
            <span>Evidence coverage</span>
            <strong>{pct(evalResults.metrics.evidence_coverage)}</strong>
          </div>
          <div>
            <span>Forbidden wording fail rate</span>
            <strong>{pct(evalResults.metrics.forbidden_wording_fail_rate)}</strong>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="section-title">
          <span>ScenarioReplay</span>
          <strong>advanced only</strong>
        </div>
        <div className="bar-chart compact-bars">
          {replayBars.map((item, index) => (
            <div className={`bar ${index === replayBars.length - 1 ? 'focus' : ''}`} style={{ height: `${Math.max(20, item.value - 85)}%` }} key={item.date}>
              <span>{item.date}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default function TraceView({ analysis, onTraceLoaded }) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('current run trace');
  const [events, setEvents] = useState(analysis.agent_events || []);
  const [toolCalls, setToolCalls] = useState(analysis.tool_calls || []);
  const [activeTab, setActiveTab] = useState('trace');

  async function refreshTrace() {
    if (!analysis.run_id) return;
    setLoading(true);
    try {
      const payload = await getJobEvents(analysis.run_id);
      setEvents(payload.events || []);
      setToolCalls(payload.tool_calls || []);
      onTraceLoaded?.(payload);
      setStatus('backend audit store');
    } catch {
      setEvents(analysis.agent_events || []);
      setToolCalls(analysis.tool_calls || []);
      setStatus('local fallback trace');
    } finally {
      setLoading(false);
    }
  }

  const verifier = analysis.verification_result || {};
  const planner = analysis.planner_plan || {};
  const guardrail = analysis.compliance_boundary || {};

  return (
    <div className="page-stack">
      <section className="control-band trace-control">
        <button className="primary-btn" onClick={refreshTrace} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
          刷新轨迹
        </button>
        <div className="inline-status">
          <GitBranch size={16} />
          <span>{analysis.run_id || 'run_mock_preview'}</span>
          <strong>{status}</strong>
        </div>
      </section>

      <div className="tabs">
        <button className={activeTab === 'trace' ? 'active' : ''} onClick={() => setActiveTab('trace')}>
          Trace
        </button>
        <button className={activeTab === 'verify' ? 'active' : ''} onClick={() => setActiveTab('verify')}>
          Verifier / Guardrail
        </button>
        <button className={activeTab === 'eval' ? 'active' : ''} onClick={() => setActiveTab('eval')}>
          Advanced Eval
        </button>
      </div>

      {activeTab === 'eval' ? (
        <AdvancedEval />
      ) : activeTab === 'verify' ? (
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
              <strong>{guardrail.forbidden_wording_found ? 'hit' : 'clean'}</strong>
            </div>
            <pre className="json-block">{JSON.stringify(guardrail, null, 2)}</pre>
          </div>
        </section>
      ) : (
        <>
          <section className="split-grid">
            <div className="panel">
              <div className="section-title">
                <span>Planner plan</span>
                <strong>{planner.task_type || 'standard_research'}</strong>
              </div>
              <pre className="json-block">{JSON.stringify(planner, null, 2)}</pre>
            </div>
            <div className="panel">
              <div className="section-title">
                <span>Run audit</span>
                <strong>{toolCalls.length} tool calls</strong>
              </div>
              <pre className="json-block">
                {JSON.stringify(
                  {
                    run_id: analysis.run_id,
                    workflow_engine: analysis.workflow_engine,
                    human_review: analysis.human_review
                  },
                  null,
                  2
                )}
              </pre>
            </div>
          </section>

          <section className="table-panel">
            <table>
              <thead>
                <tr>
                  <th>Tool call</th>
                  <th>Tool</th>
                  <th>Status</th>
                  <th>Latency</th>
                  <th>Evidence</th>
                </tr>
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
      )}
    </div>
  );
}
