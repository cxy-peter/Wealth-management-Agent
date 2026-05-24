import { Filter, LineChart, Loader2, Search, X } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { getProduct, getProductNav, getProductRiskEvents, runProductBenchmark } from '../api.js';

function pct(value) {
  return `${(Number(value || 0) * 100).toFixed(2)}%`;
}

function num(value, digits = 3) {
  return Number(value || 0).toFixed(digits);
}

function FilterSelect({ label, value, options, onChange }) {
  return (
    <label className="field-group">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">全部</option>
        {(options || []).map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
    </label>
  );
}

function MiniLine({ rows, field, className }) {
  if (!rows?.length) return <div className="empty-chart">暂无净值样本</div>;
  const values = rows.map((item) => Number(item[field] || 0));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const points = values
    .map((value, index) => {
      const x = (index / Math.max(values.length - 1, 1)) * 100;
      const y = 92 - ((value - min) / Math.max(max - min, 0.000001)) * 82;
      return `${x},${y}`;
    })
    .join(' ');
  return (
    <svg className={className} viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
      <polyline points={points} />
    </svg>
  );
}

function DetailDrawer({ selected, detail, navRows, eventRows, onClose }) {
  if (!selected) return null;
  const metrics = detail?.metrics || selected;
  return (
    <div className="drawer-backdrop" role="presentation">
      <aside className="review-drawer product-drawer" aria-label="Product detail">
        <div className="section-title">
          <span>{selected.product_name}</span>
          <button className="icon-btn" onClick={onClose} title="Close product detail">
            <X size={18} />
          </button>
        </div>

        <section className="metric-grid compact">
          <div className="metric-tile green">
            <span>年化收益</span>
            <strong>{pct(metrics.annualized_return)}</strong>
          </div>
          <div className="metric-tile">
            <span>年化波动</span>
            <strong>{pct(metrics.annualized_volatility)}</strong>
          </div>
          <div className="metric-tile red">
            <span>最大回撤</span>
            <strong>{pct(metrics.max_drawdown)}</strong>
          </div>
        </section>

        <section className="panel chart-panel">
          <div className="section-title">
            <span>NAV / Benchmark</span>
            <strong>{navRows.length} 周</strong>
          </div>
          <div className="line-chart">
            <MiniLine rows={navRows} field="nav" className="nav-line primary-line" />
            <MiniLine rows={navRows} field="benchmark_nav" className="nav-line benchmark-line" />
          </div>
          <div className="chart-legend">
            <span className="legend primary" /> NAV
            <span className="legend benchmark" /> Benchmark
          </div>
        </section>

        <section className="panel">
          <div className="section-title">
            <span>风险事件</span>
            <strong>{eventRows.length}</strong>
          </div>
          <div className="evidence-list">
            {eventRows.map((item) => (
              <div className="evidence-row" key={item.evidence_id || `${item.event_date}-${item.event_type}`}>
                <strong>{item.event_type}</strong>
                <span>
                  {item.event_date} · severity {item.severity} · {item.evidence_id}
                </span>
                <p>{item.event_summary}</p>
              </div>
            ))}
            {!eventRows.length ? <div className="evidence-row">暂无风险事件样例。</div> : null}
          </div>
        </section>

        <section className="panel">
          <div className="section-title">
            <span>指标追溯</span>
            <strong>{metrics.metric_evidence_id || selected.metric_evidence_id}</strong>
          </div>
          <pre className="json-block">
            {JSON.stringify(
              {
                product_id: selected.product_id,
                source_tool_call_id: metrics.source_tool_call_id || selected.source_tool_call_id,
                metric_evidence_id: metrics.metric_evidence_id || selected.metric_evidence_id,
                nav_evidence_id: metrics.nav_evidence_id || selected.nav_evidence_id,
                benchmark_excess_return: metrics.benchmark_excess_return,
                drawdown_recovery_days: metrics.drawdown_recovery_days
              },
              null,
              2
            )}
          </pre>
        </section>
      </aside>
    </div>
  );
}

export default function ProductBenchmark({ analysis, onAnalysis }) {
  const peer = analysis.peer_summary || { table: [] };
  const [filters, setFilters] = useState({
    asset_class: '',
    strategy_type: '',
    risk_level: '',
    duration_bucket: '',
    channel: '',
    liquidity_type: ''
  });
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('sample/mock product table');
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [navRows, setNavRows] = useState([]);
  const [eventRows, setEventRows] = useState([]);

  const options = peer.filter_options || {};
  const table = peer.table || [];

  const scatter = useMemo(() => {
    if (!table.length) return [];
    const maxVol = Math.max(...table.map((item) => Number(item.annualized_volatility || 0)), 0.01);
    const maxRet = Math.max(...table.map((item) => Number(item.annualized_return || 0)), 0.01);
    const minRet = Math.min(...table.map((item) => Number(item.annualized_return || 0)), -0.01);
    return table.slice(0, 80).map((item) => ({
      ...item,
      x: (Number(item.annualized_volatility || 0) / maxVol) * 94 + 3,
      y: 94 - ((Number(item.annualized_return || 0) - minRet) / Math.max(maxRet - minRet, 0.001)) * 88,
      size: Math.min(24, Math.max(8, Math.abs(Number(item.max_drawdown || 0)) * 90))
    }));
  }, [table]);

  useEffect(() => {
    if (!table.length || table.length < 10) {
      handleBenchmark();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  async function handleBenchmark() {
    setLoading(true);
    try {
      const result = await runProductBenchmark(filters);
      onAnalysis({ ...analysis, peer_summary: result });
      setStatus('backend api');
    } catch {
      setStatus('local fallback');
    } finally {
      setLoading(false);
    }
  }

  async function openDetail(item) {
    setSelected(item);
    setDetail({ metrics: item });
    setNavRows([]);
    setEventRows([]);
    try {
      const [detailPayload, navPayload, eventsPayload] = await Promise.all([
        getProduct(item.product_id),
        getProductNav(item.product_id),
        getProductRiskEvents(item.product_id)
      ]);
      setDetail(detailPayload);
      setNavRows(navPayload.records || []);
      setEventRows(eventsPayload.records || []);
    } catch {
      setDetail({ metrics: item });
      setNavRows([]);
      setEventRows([]);
    }
  }

  return (
    <div className="product-workspace">
      <aside className="filter-panel">
        <div className="section-title">
          <span>筛选器</span>
          <strong>{peer.product_count || table.length} / {peer.product_universe_size || peer.product_count || table.length}</strong>
        </div>
        <FilterSelect label="资产类别" value={filters.asset_class} options={options.asset_class} onChange={(value) => updateFilter('asset_class', value)} />
        <FilterSelect label="策略" value={filters.strategy_type} options={options.strategy_type} onChange={(value) => updateFilter('strategy_type', value)} />
        <FilterSelect label="风险等级" value={filters.risk_level} options={options.risk_level} onChange={(value) => updateFilter('risk_level', value)} />
        <FilterSelect label="期限" value={filters.duration_bucket} options={options.duration_bucket} onChange={(value) => updateFilter('duration_bucket', value)} />
        <FilterSelect label="渠道" value={filters.channel} options={options.channel} onChange={(value) => updateFilter('channel', value)} />
        <FilterSelect label="流动性" value={filters.liquidity_type} options={options.liquidity_type} onChange={(value) => updateFilter('liquidity_type', value)} />
        <button className="primary-btn" onClick={handleBenchmark} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <Filter size={18} />}
          更新对标
        </button>
      </aside>

      <main className="page-stack product-main">
        <div className="inline-status">
          <Search size={16} />
          <span>{status}</span>
          <strong>{peer.methodology}</strong>
        </div>

        <section className="panel">
          <div className="section-title">
            <span>收益-波动分布</span>
            <strong>size=max drawdown abs</strong>
          </div>
          <div className="scatter-plot">
            {scatter.map((item) => (
              <button
                key={`dot-${item.product_id}`}
                className={`scatter-dot ${item.risk_level}`}
                style={{ left: `${item.x}%`, top: `${item.y}%`, width: item.size, height: item.size }}
                title={`${item.product_name}: ${pct(item.annualized_return)} / ${pct(item.annualized_volatility)}`}
                onClick={() => openDetail(item)}
              />
            ))}
            <span className="axis x-axis">annualized volatility</span>
            <span className="axis y-axis">annualized return</span>
          </div>
        </section>

        <section className="table-panel">
          <table>
            <thead>
              <tr>
                <th>产品名</th>
                <th>资产类别</th>
                <th>风险等级</th>
                <th>期限</th>
                <th>年化收益</th>
                <th>年化波动</th>
                <th>最大回撤</th>
                <th>Sharpe</th>
                <th>Calmar</th>
                <th>Benchmark excess</th>
                <th>收益排名</th>
                <th>风险调整排名</th>
              </tr>
            </thead>
            <tbody>
              {table.map((item) => (
                <tr key={item.product_id} onClick={() => openDetail(item)} className="clickable-row">
                  <td>
                    <strong>{item.product_name}</strong>
                    <span>{item.product_id} · {item.strategy_type}</span>
                  </td>
                  <td>{item.asset_class}</td>
                  <td>
                    <span className={`risk-chip ${item.risk_level}`}>{item.risk_level}</span>
                  </td>
                  <td>{item.duration_bucket}</td>
                  <td>{pct(item.annualized_return)}</td>
                  <td>{pct(item.annualized_volatility)}</td>
                  <td>{pct(item.max_drawdown)}</td>
                  <td>{num(item.sharpe_ratio)}</td>
                  <td>{num(item.calmar_ratio)}</td>
                  <td>{pct(item.benchmark_excess_return)}</td>
                  <td>{item.return_rank}</td>
                  <td>{item.risk_adjusted_rank}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </main>

      <DetailDrawer selected={selected} detail={detail} navRows={navRows} eventRows={eventRows} onClose={() => setSelected(null)} />
    </div>
  );
}
