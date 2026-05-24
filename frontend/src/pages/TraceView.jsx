import { GitBranch, Loader2, RefreshCw } from 'lucide-react';
import { useState } from 'react';

import { getJobEvents } from '../api.js';

export default function TraceView({ analysis, onTraceLoaded }) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('current run trace');
  const [events, setEvents] = useState(analysis.agent_events || []);
  const [toolCalls, setToolCalls] = useState(analysis.tool_calls || []);

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
            <span>Verifier result</span>
            <strong>{verifier.pass ? 'pass' : 'review'}</strong>
          </div>
          <pre className="json-block">{JSON.stringify(verifier, null, 2)}</pre>
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
    </div>
  );
}
