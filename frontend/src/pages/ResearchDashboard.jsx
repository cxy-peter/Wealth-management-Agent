import { FileText, Loader2, Play, RefreshCw } from 'lucide-react';
import { useState } from 'react';

import { runAnalyze } from '../api.js';
import { instrumentOptions, sampleAnalysis } from '../data/mockData.js';

function pct(value) {
  return `${(Number(value || 0) * 100).toFixed(2)}%`;
}

function num(value, digits = 3) {
  return Number(value || 0).toFixed(digits);
}

function MetricTile({ label, value, tone = 'neutral' }) {
  return (
    <div className={`metric-tile ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function NewsTab({ analysis }) {
  const news = analysis.news_signals || [];
  return (
    <section className="split-grid">
      <div className="panel">
        <div className="section-title">
          <span>新闻风险信号</span>
          <strong>{news.length} 条</strong>
        </div>
        <div className="evidence-list">
          {news.map((item) => (
            <div className={`evidence-row ${Number(item.risk_score || 0) >= 4 ? 'strong' : ''}`} key={`${item.date}-${item.title}`}>
              <strong>{item.title}</strong>
              <span>
                {item.date} · 情绪 {item.sentiment_score} · 风险 {item.risk_score} · {item.model_mode}
              </span>
              <p>{item.evidence}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="panel">
        <div className="section-title">
          <span>风险摘要</span>
          <strong>Guardrail</strong>
        </div>
        <div className="evidence-list">
          {(analysis.risk_flags || []).map((item) => (
            <div className="evidence-row" key={item}>
              {item}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function ResearchDashboard({ analysis, onAnalysis }) {
  const [symbol, setSymbol] = useState(analysis.symbol || '600519');
  const [company, setCompany] = useState(analysis.company || '贵州茅台');
  const [selectedInstrument, setSelectedInstrument] = useState(analysis.symbol || '600519');
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [source, setSource] = useState('mock preview');
  const [error, setError] = useState('');

  async function handleRun() {
    setLoading(true);
    setError('');
    try {
      const result = await runAnalyze({ symbol, company, analysis_type: 'full' });
      onAnalysis(result);
      setSource('backend api');
    } catch {
      onAnalysis({ ...sampleAnalysis, symbol, company });
      setSource('local fallback');
      setError('后端暂不可用，当前显示 mock 数据。');
    } finally {
      setLoading(false);
    }
  }

  function handleSelectInstrument(value) {
    setSelectedInstrument(value);
    const option = instrumentOptions.find((item) => item.symbol === value);
    if (option) {
      setSymbol(option.symbol);
      setCompany(option.company);
    }
  }

  const metrics = analysis.metrics || {};
  const fundamental = analysis.fundamental_analysis || {};
  const valuation = analysis.valuation_analysis || {};
  const technical = analysis.technical_analysis || {};

  return (
    <div className="page-stack">
      <section className="control-band">
        <div className="field-group">
          <label htmlFor="instrument">样例选项</label>
          <select id="instrument" value={selectedInstrument} onChange={(event) => handleSelectInstrument(event.target.value)}>
            {instrumentOptions.map((item) => (
              <option key={item.symbol} value={item.symbol}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
        <div className="field-group">
          <label htmlFor="symbol">Symbol</label>
          <input id="symbol" value={symbol} onChange={(event) => setSymbol(event.target.value)} />
        </div>
        <div className="field-group wide">
          <label htmlFor="company">Company / Product</label>
          <input id="company" value={company} onChange={(event) => setCompany(event.target.value)} />
        </div>
        <button className="primary-btn" onClick={handleRun} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
          运行分析
        </button>
        <button className="icon-btn" onClick={() => onAnalysis(sampleAnalysis)} title="恢复 mock 预览">
          <RefreshCw size={18} />
        </button>
      </section>

      <div className="inline-status">
        <FileText size={16} />
        <span>Source: {source}</span>
        {error ? <strong>{error}</strong> : null}
      </div>

      <div className="tabs">
        <button className={activeTab === 'overview' ? 'active' : ''} onClick={() => setActiveTab('overview')}>
          Overview
        </button>
        <button className={activeTab === 'news' ? 'active' : ''} onClick={() => setActiveTab('news')}>
          News Risk
        </button>
      </div>

      {activeTab === 'news' ? (
        <NewsTab analysis={analysis} />
      ) : (
        <>
          <section className="metric-grid">
            <MetricTile label="区间收益" value={pct(metrics.total_return)} tone="green" />
            <MetricTile label="年化波动" value={pct(metrics.annualized_volatility)} />
            <MetricTile label="最大回撤" value={pct(metrics.max_drawdown)} tone="red" />
            <MetricTile label="Sharpe" value={num(metrics.sharpe_ratio)} />
            <MetricTile label="新闻风险均值" value={num(analysis.news_summary?.avg_risk, 2)} tone="amber" />
            <MetricTile label="产品池规模" value={analysis.peer_summary?.product_universe_size || analysis.peer_summary?.product_count || 0} />
          </section>

          <section className="split-grid">
            <div className="panel">
              <div className="section-title">
                <span>基本面 / 估值</span>
                <strong>{fundamental.quality_label || 'NA'}</strong>
              </div>
              <div className="evidence-list">
                {(fundamental.points || []).map((item) => (
                  <div className="evidence-row" key={item}>
                    {item}
                  </div>
                ))}
                {(valuation.points || []).map((item) => (
                  <div className="evidence-row" key={item}>
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <div className="panel">
              <div className="section-title">
                <span>技术面风险观察</span>
                <strong>{technical.risk_regime || 'NA'}</strong>
              </div>
              <div className="two-column-facts">
                <div>
                  <span>趋势标签</span>
                  <strong>{technical.trend_label || 'NA'}</strong>
                </div>
                <div>
                  <span>MA5 / MA20</span>
                  <strong>
                    {num(technical.ma5)} / {num(technical.ma20)}
                  </strong>
                </div>
                <div>
                  <span>5 日动量</span>
                  <strong>{pct(technical.momentum_5d)}</strong>
                </div>
                <div>
                  <span>20 日动量</span>
                  <strong>{pct(technical.momentum_20d)}</strong>
                </div>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="section-title">
              <span>报告预览</span>
              <strong>{analysis.report_path ? 'markdown generated' : 'mock markdown'}</strong>
            </div>
            <pre className="report-preview">{analysis.report_markdown}</pre>
          </section>
        </>
      )}
    </div>
  );
}
