import { AlertTriangle, Newspaper, ShieldAlert } from 'lucide-react';

function tone(score) {
  if (Number(score) >= 4) return 'high';
  if (Number(score) >= 3) return 'medium';
  return 'low';
}

export default function NewsRiskPanel({ analysis }) {
  const summary = analysis.news_summary || {};
  const rows = analysis.news_signals || [];

  return (
    <div className="page-stack">
      <section className="metric-grid compact">
        <div className="metric-tile">
          <span>新闻样本</span>
          <strong>{summary.signal_count || rows.length}</strong>
        </div>
        <div className="metric-tile green">
          <span>平均情绪分</span>
          <strong>{Number(summary.avg_sentiment || 0).toFixed(2)}</strong>
        </div>
        <div className="metric-tile amber">
          <span>平均风险分</span>
          <strong>{Number(summary.avg_risk || 0).toFixed(2)}</strong>
        </div>
      </section>

      <section className="split-grid">
        <div className="panel">
          <div className="section-title">
            <span>风险标题</span>
            <AlertTriangle size={18} />
          </div>
          <div className="evidence-list">
            {(summary.top_risks || []).map((item) => (
              <div className="evidence-row strong" key={item}>
                {item}
              </div>
            ))}
          </div>
        </div>
        <div className="panel">
          <div className="section-title">
            <span>模型兜底</span>
            <ShieldAlert size={18} />
          </div>
          <p className="panel-copy">
            Qwen LoRA 风险/情绪 adapter 仅作为可配置选项；无本地模型或无 GPU 时，系统使用规则兜底，保留证据命中项。
          </p>
        </div>
      </section>

      <section className="table-panel">
        <table>
          <thead>
            <tr>
              <th>日期</th>
              <th>标题</th>
              <th>情绪分</th>
              <th>风险分</th>
              <th>模型模式</th>
              <th>证据</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((item) => (
              <tr key={`${item.date}-${item.title}`}>
                <td>{item.date}</td>
                <td>
                  <strong className="title-with-icon">
                    <Newspaper size={15} />
                    {item.title}
                  </strong>
                </td>
                <td>
                  <span className={`score-chip ${tone(item.sentiment_score)}`}>{item.sentiment_score}</span>
                </td>
                <td>
                  <span className={`score-chip ${tone(item.risk_score)}`}>{item.risk_score}</span>
                </td>
                <td>{item.model_mode}</td>
                <td>{item.evidence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
