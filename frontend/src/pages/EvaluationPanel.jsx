import { CheckCircle2, Loader2, PlayCircle, XCircle } from 'lucide-react';
import { useState } from 'react';

import { runEvaluation } from '../api.js';
import { evalResults } from '../data/mockData.js';

function pct(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function EvalMetric({ label, value, danger = false }) {
  return (
    <div className={`metric-tile ${danger ? 'red' : 'green'}`}>
      <span>{label}</span>
      <strong>{label.includes('fail') ? pct(value) : pct(value)}</strong>
    </div>
  );
}

export default function EvaluationPanel() {
  const [results, setResults] = useState(evalResults);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('mock preview');

  async function handleRun() {
    setLoading(true);
    try {
      const payload = await runEvaluation({});
      setResults(payload);
      setStatus('backend api');
    } catch {
      setResults(evalResults);
      setStatus('local fallback');
    } finally {
      setLoading(false);
    }
  }

  const metrics = results.metrics || {};
  const cases = results.cases || [];

  return (
    <div className="page-stack">
      <section className="control-band">
        <button className="primary-btn" onClick={handleRun} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <PlayCircle size={18} />}
          运行评测
        </button>
        <div className="inline-status">
          <span>Source: {status}</span>
          {results.results_path ? <strong>{results.results_path}</strong> : null}
        </div>
      </section>

      <section className="metric-grid compact">
        <EvalMetric label="tool_call_success" value={metrics.tool_call_success} />
        <EvalMetric label="report_format_pass" value={metrics.report_format_pass} />
        <EvalMetric label="metric_consistency" value={metrics.metric_consistency} />
        <EvalMetric label="risk_warning_coverage" value={metrics.risk_warning_coverage} />
        <EvalMetric label="forbidden_wording_fail_rate" value={metrics.forbidden_wording_fail_rate} danger />
        <div className="metric-tile">
          <span>avg_latency_ms</span>
          <strong>{Number(metrics.avg_latency_ms || 0).toFixed(1)}</strong>
        </div>
      </section>

      <section className="table-panel">
        <table>
          <thead>
            <tr>
              <th>Case</th>
              <th>Workflow</th>
              <th>Latency</th>
              <th>Tool</th>
              <th>Format</th>
              <th>Metrics</th>
              <th>Risk</th>
              <th>Guardrail</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((item) => (
              <tr key={item.symbol}>
                <td>{item.symbol}</td>
                <td>{item.workflow_engine}</td>
                <td>{Number(item.latency_ms || 0).toFixed(1)} ms</td>
                <td>{item.tool_call_success ? <CheckCircle2 className="ok" size={18} /> : <XCircle className="bad" size={18} />}</td>
                <td>{item.report_format_pass ? <CheckCircle2 className="ok" size={18} /> : <XCircle className="bad" size={18} />}</td>
                <td>{item.metric_consistency ? <CheckCircle2 className="ok" size={18} /> : <XCircle className="bad" size={18} />}</td>
                <td>{item.risk_warning_coverage ? <CheckCircle2 className="ok" size={18} /> : <XCircle className="bad" size={18} />}</td>
                <td>{!item.forbidden_wording_fail ? <CheckCircle2 className="ok" size={18} /> : <XCircle className="bad" size={18} />}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
