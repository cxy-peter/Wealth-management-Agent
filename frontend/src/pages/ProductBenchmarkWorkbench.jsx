import { Filter, Loader2, Search, X } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import {
  getWeeklyProduct,
  getWeeklyProducts,
  runChannelBenchmark,
  runPeerBenchmark,
  runTopPeers
} from '../api.js';
import {
  channelBenchmarkMock,
  peerBenchmarkMock,
  productDetailMock,
  topPeersMock,
  weeklyMock,
  weeklyProductsMock
} from '../data/mockData.js';

function pct(value, digits = 2) {
  return `${(Number(value || 0) * 100).toFixed(digits)}%`;
}

function num(value, digits = 3) {
  return Number(value || 0).toFixed(digits);
}

function SelectField({ label, value, options, onChange }) {
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

function DetailDrawer({ detail, onClose }) {
  if (!detail) return null;
  const snapshot = detail.snapshot || detail;
  const percentile = detail.percentile || {};
  const nav = detail.nav || [];
  const events = detail.risk_events || [];
  return (
    <div className="drawer-backdrop" role="presentation">
      <aside className="review-drawer product-drawer" aria-label="Product detail">
        <div className="section-title">
          <span>{snapshot.product_name}</span>
          <button className="icon-btn" onClick={onClose} title="关闭详情">
            <X size={18} />
          </button>
        </div>
        <section className="metric-grid compact">
          <div className="metric-tile green">
            <span>3M 收益</span>
            <strong>{pct(snapshot.return_3m)}</strong>
          </div>
          <div className="metric-tile">
            <span>年化波动</span>
            <strong>{pct(snapshot.volatility)}</strong>
          </div>
          <div className="metric-tile red">
            <span>最大回撤</span>
            <strong>{pct(snapshot.max_drawdown)}</strong>
          </div>
        </section>
        <section className="panel chart-panel">
          <div className="section-title">
            <span>NAV / Benchmark</span>
            <strong>{nav.length} 周</strong>
          </div>
          <div className="line-chart">
            <MiniLine rows={nav} field="nav" className="nav-line primary-line" />
            <MiniLine rows={nav} field="benchmark_nav" className="nav-line benchmark-line" />
          </div>
          <div className="chart-legend">
            <span className="legend primary" /> NAV
            <span className="legend benchmark" /> Benchmark
          </div>
        </section>
        <section className="split-grid">
          <div className="panel">
            <div className="section-title">
              <span>市场分位</span>
              <strong>{percentile.evidence_id}</strong>
            </div>
            <div className="two-column-facts">
              <div>
                <span>收益分位</span>
                <strong>{pct(percentile.return_percentile, 0)}</strong>
              </div>
              <div>
                <span>回撤分位</span>
                <strong>{pct(percentile.drawdown_percentile, 0)}</strong>
              </div>
              <div>
                <span>Sharpe 分位</span>
                <strong>{pct(percentile.sharpe_percentile, 0)}</strong>
              </div>
              <div>
                <span>同类样本数</span>
                <strong>{percentile.peer_count || 0}</strong>
              </div>
            </div>
          </div>
          <div className="panel">
            <div className="section-title">
              <span>风险事件</span>
              <strong>{events.length}</strong>
            </div>
            <div className="evidence-list">
              {events.map((item) => (
                <div className="evidence-row" key={`${item.event_date}-${item.evidence_id}`}>
                  <strong>{item.event_type}</strong>
                  <span>{item.event_date} · {item.evidence_id}</span>
                  <p>{item.event_summary}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
        <section className="panel">
          <div className="section-title">
            <span>指标追溯</span>
            <strong>tool/evidence</strong>
          </div>
          <pre className="json-block">{JSON.stringify({ evidence_ids: detail.evidence_ids, snapshot }, null, 2)}</pre>
        </section>
      </aside>
    </div>
  );
}

function ProductTable({ rows, onOpen }) {
  return (
    <section className="table-panel">
      <table>
        <thead>
          <tr>
            <th>产品名</th>
            <th>资产类别</th>
            <th>风险等级</th>
            <th>期限</th>
            <th>3M 收益</th>
            <th>年化波动</th>
            <th>最大回撤</th>
            <th>Sharpe</th>
            <th>收益分位</th>
            <th>回撤分位</th>
            <th>Evidence</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((item) => (
            <tr key={item.product_code} className="clickable-row" onClick={() => onOpen(item.product_code)}>
              <td>
                <strong>{item.product_name}</strong>
                <span>{item.product_code} · {item.product_series}</span>
              </td>
              <td>{item.product_type}</td>
              <td><span className={`risk-chip ${item.risk_level}`}>{item.risk_level}</span></td>
              <td>{item.open_type || `${item.holding_period_days || 0} 天`}</td>
              <td>{pct(item.return_3m)}</td>
              <td>{pct(item.volatility)}</td>
              <td>{pct(item.max_drawdown)}</td>
              <td>{num(item.sharpe)}</td>
              <td>{pct(item.return_percentile, 0)}</td>
              <td>{pct(item.drawdown_percentile, 0)}</td>
              <td>{item.evidence_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export default function ProductBenchmarkWorkbench({ onAnalysis }) {
  const [filters, setFilters] = useState({
    report_date: weeklyMock.report_date,
    product_series: '',
    product_type: '',
    risk_level: '',
    channel: '',
    open_type: '',
    benchmark_status: ''
  });
  const [products, setProducts] = useState(weeklyProductsMock);
  const [options, setOptions] = useState(weeklyMock.filter_options);
  const [activeTab, setActiveTab] = useState('peer');
  const [status, setStatus] = useState('local fallback');
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState(null);
  const [peer, setPeer] = useState(peerBenchmarkMock);
  const [channel, setChannel] = useState(channelBenchmarkMock);
  const [topPeers, setTopPeers] = useState(topPeersMock);

  const scatter = useMemo(() => {
    if (!products.length) return [];
    const maxVol = Math.max(...products.map((item) => Number(item.volatility || 0)), 0.01);
    const maxRet = Math.max(...products.map((item) => Number(item.return_3m || 0)), 0.01);
    const minRet = Math.min(...products.map((item) => Number(item.return_3m || 0)), -0.01);
    return products.slice(0, 90).map((item) => ({
      ...item,
      x: (Number(item.volatility || 0) / maxVol) * 94 + 3,
      y: 94 - ((Number(item.return_3m || 0) - minRet) / Math.max(maxRet - minRet, 0.001)) * 88,
      size: Math.min(24, Math.max(8, Math.abs(Number(item.max_drawdown || 0)) * 220))
    }));
  }, [products]);

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  async function refreshProducts() {
    setLoading(true);
    try {
      const payload = await getWeeklyProducts(filters);
      setProducts(payload.products || []);
      setOptions(payload.filter_options || weeklyMock.filter_options);
      setStatus('backend weekly products');
    } catch {
      setProducts(weeklyProductsMock);
      setStatus('local fallback');
    } finally {
      setLoading(false);
    }
  }

  async function openDetail(productCode) {
    setDetail(productDetailMock);
    try {
      const payload = await getWeeklyProduct(productCode, filters.report_date);
      setDetail(payload);
      const benchmark = await runPeerBenchmark({ product_code: productCode, report_date: filters.report_date, limit: 12 });
      setPeer(benchmark);
    } catch {
      setDetail(productDetailMock);
      setPeer(peerBenchmarkMock);
    }
  }

  async function refreshBenchmarkTabs() {
    setLoading(true);
    try {
      const [channelPayload, topPayload] = await Promise.all([
        runChannelBenchmark({ product_type: filters.product_type || undefined, channel: filters.channel || undefined }),
        runTopPeers({ product_type: filters.product_type || undefined, report_date: filters.report_date, limit: 20 })
      ]);
      setChannel(channelPayload);
      setTopPeers(topPayload);
      setStatus('backend benchmark API');
    } catch {
      setChannel(channelBenchmarkMock);
      setTopPeers(topPeersMock);
      setStatus('local fallback');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshProducts();
    refreshBenchmarkTabs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="product-workspace">
      <aside className="filter-panel">
        <div className="section-title">
          <span>筛选器</span>
          <strong>{products.length}</strong>
        </div>
        <SelectField label="资产类别" value={filters.product_type} options={options.product_type} onChange={(value) => updateFilter('product_type', value)} />
        <SelectField label="策略" value={filters.product_series} options={options.product_series} onChange={(value) => updateFilter('product_series', value)} />
        <SelectField label="风险等级" value={filters.risk_level} options={options.risk_level} onChange={(value) => updateFilter('risk_level', value)} />
        <SelectField label="期限" value={filters.open_type} options={options.open_type} onChange={(value) => updateFilter('open_type', value)} />
        <SelectField label="渠道" value={filters.channel} options={options.channel} onChange={(value) => updateFilter('channel', value)} />
        <SelectField label="达标状态" value={filters.benchmark_status} options={options.benchmark_status} onChange={(value) => updateFilter('benchmark_status', value)} />
        <button className="primary-btn" onClick={refreshProducts} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <Filter size={18} />}
          更新样本
        </button>
      </aside>
      <main className="page-stack product-main">
        <div className="inline-status">
          <Search size={16} />
          <span>{status}</span>
          <strong>synthetic weekly universe</strong>
        </div>
        <section className="panel">
          <div className="section-title">
            <span>收益-波动分布</span>
            <strong>x=volatility · y=3M return · size=max drawdown</strong>
          </div>
          <div className="scatter-plot">
            {scatter.map((item) => (
              <button
                key={`dot-${item.product_code}`}
                className={`scatter-dot ${item.risk_level}`}
                style={{ left: `${item.x}%`, top: `${item.y}%`, width: item.size, height: item.size }}
                title={`${item.product_name}: ${pct(item.return_3m)} / ${pct(item.volatility)}`}
                onClick={() => openDetail(item.product_code)}
              />
            ))}
            <span className="axis x-axis">annualized volatility</span>
            <span className="axis y-axis">3M return</span>
          </div>
        </section>
        <div className="tabs">
          <button className={activeTab === 'peer' ? 'active' : ''} onClick={() => setActiveTab('peer')}>竞品对标</button>
          <button className={activeTab === 'market' ? 'active' : ''} onClick={() => setActiveTab('market')}>全市场分位</button>
          <button className={activeTab === 'channel' ? 'active' : ''} onClick={() => setActiveTab('channel')}>渠道对标</button>
          <button className={activeTab === 'top' ? 'active' : ''} onClick={() => setActiveTab('top')}>同类绩优产品</button>
        </div>
        {activeTab === 'peer' ? <ProductTable rows={products} onOpen={openDetail} /> : null}
        {activeTab === 'market' ? (
          <section className="panel">
            <div className="section-title">
              <span>全市场分位样本</span>
              <strong>{peer.peer_count || 0} peers</strong>
            </div>
            <pre className="json-block">{JSON.stringify(peer.percentile || {}, null, 2)}</pre>
          </section>
        ) : null}
        {activeTab === 'channel' ? (
          <section className="table-panel">
            <table>
              <thead><tr><th>渠道</th><th>类型</th><th>样本数</th><th>3M 均值</th><th>规模合计</th></tr></thead>
              <tbody>
                {(channel.table || []).map((row) => (
                  <tr key={`${row.channel}-${row.product_type}`}>
                    <td>{row.channel}</td><td>{row.product_type}</td><td>{row.peer_count}</td><td>{pct(row.avg_return_3m)}</td><td>{num(row.total_scale_bn)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        ) : null}
        {activeTab === 'top' ? (
          <section className="table-panel">
            <table>
              <thead><tr><th>排名</th><th>产品</th><th>类型</th><th>3M 收益</th><th>收益分位</th><th>最大回撤</th><th>Sharpe</th><th>Evidence</th></tr></thead>
              <tbody>
                {(topPeers.table || []).map((row) => (
                  <tr key={row.peer_product_code}>
                    <td>{row.rank}</td><td>{row.peer_product_name}</td><td>{row.product_type}</td><td>{pct(row.return_3m)}</td><td>{pct(row.return_percentile, 0)}</td><td>{pct(row.max_drawdown)}</td><td>{num(row.sharpe)}</td><td>{row.evidence_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        ) : null}
      </main>
      <DetailDrawer detail={detail} onClose={() => setDetail(null)} />
    </div>
  );
}
