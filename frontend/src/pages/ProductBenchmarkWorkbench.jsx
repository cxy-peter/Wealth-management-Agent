import { BarChart3, Filter, Loader2, Search, X } from 'lucide-react';
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

function signedPct(value, digits = 2) {
  const number = Number(value || 0);
  return `${number >= 0 ? '+' : ''}${pct(number, digits)}`;
}

function num(value, digits = 3) {
  return Number(value || 0).toFixed(digits);
}

function money(value) {
  return `${Number(value || 0).toFixed(2)} 亿`;
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

function ProductSelector({ products, selectedCode, onSelect }) {
  return (
    <label className="field-group">
      <span>选择产品</span>
      <select value={selectedCode || ''} onChange={(event) => onSelect(event.target.value)}>
        {products.slice(0, 120).map((item) => (
          <option key={item.product_code} value={item.product_code}>
            {item.product_code} · {item.product_name}
          </option>
        ))}
      </select>
    </label>
  );
}

function DetailDrawer({ detail, onClose }) {
  if (!detail) return null;
  const snapshot = detail.snapshot || detail;
  const percentile = detail.percentile || {};
  const nav = detail.nav || [];
  const events = detail.risk_events || [];
  const sourceMatrix = detail.field_source_matrix || [];
  return (
    <div className="drawer-backdrop" role="presentation">
      <aside className="review-drawer product-drawer" aria-label="产品详情">
        <div className="section-title">
          <span>{snapshot.product_name}</span>
          <button className="icon-btn" onClick={onClose} title="关闭详情">
            <X size={18} />
          </button>
        </div>
        <section className="metric-grid compact">
          <div className="metric-tile green">
            <span>近3个月收益</span>
            <strong>{signedPct(snapshot.return_3m)}</strong>
          </div>
          <div className="metric-tile">
            <span>净值波动率</span>
            <strong>{pct(snapshot.volatility)}</strong>
          </div>
          <div className="metric-tile red">
            <span>最大回撤</span>
            <strong>{pct(snapshot.max_drawdown)}</strong>
          </div>
        </section>
        <section className="panel chart-panel">
          <div className="section-title">
            <span>净值与基准曲线</span>
            <strong>{nav.length} 周样本</strong>
          </div>
          <div className="line-chart">
            <MiniLine rows={nav} field="nav" className="nav-line primary-line" />
            <MiniLine rows={nav} field="benchmark_nav" className="nav-line benchmark-line" />
          </div>
          <div className="chart-legend">
            <span className="legend primary" /> 产品净值
            <span className="legend benchmark" /> 基准净值
          </div>
        </section>
        <section className="split-grid">
          <div className="panel">
            <div className="section-title">
              <span>模拟同业池分位</span>
              <strong>{percentile.evidence_id || snapshot.evidence_id}</strong>
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
                <span>可比样本数</span>
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
                  <span>{item.event_date} · 证据编号 {item.evidence_id}</span>
                  <p>{item.event_summary}</p>
                </div>
              ))}
              {!events.length ? <p className="panel-copy">当前演示样本暂无风险事件记录。</p> : null}
            </div>
          </div>
        </section>
        <section className="table-panel">
          <div className="section-title table-title">
            <span>字段来源矩阵</span>
            <strong>{sourceMatrix.length}</strong>
          </div>
          <table>
            <thead>
              <tr>
                <th>字段</th>
                <th>来源</th>
                <th>as_of_date</th>
                <th>confidence</th>
                <th>证据编号</th>
              </tr>
            </thead>
            <tbody>
              {sourceMatrix.map((item) => (
                <tr key={`${item.field}-${item.evidence_id}`}>
                  <td>{item.field}</td>
                  <td>{item.source_type || item.source}</td>
                  <td>{item.as_of_date}</td>
                  <td>{item.confidence}</td>
                  <td>{item.evidence_id}</td>
                </tr>
              ))}
              {!sourceMatrix.length ? (
                <tr>
                  <td colSpan="5">暂无字段来源矩阵，使用演示样本追溯信息兜底。</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </section>
        <details className="technical-panel">
          <summary>查看技术详情</summary>
          <pre className="json-block">{JSON.stringify({ evidence_ids: detail.evidence_ids, snapshot }, null, 2)}</pre>
        </details>
      </aside>
    </div>
  );
}

function SelectedProductCard({ product, detail, onOpen }) {
  const snapshot = detail?.snapshot || product || {};
  return (
    <section className="panel product-focus-card">
      <div className="section-title">
        <span>当前对标产品</span>
        <button className="primary-btn secondary" onClick={() => onOpen(snapshot.product_code, true)}>
          查看产品详情
        </button>
      </div>
      <div className="focus-grid">
        <div>
          <strong>{snapshot.product_name || '未选择产品'}</strong>
          <span>{snapshot.product_code} · {snapshot.product_type} · {snapshot.channel}</span>
        </div>
        <div>
          <span>风险等级</span>
          <strong className={`risk-chip ${snapshot.risk_level || ''}`}>{snapshot.risk_level || '-'}</strong>
        </div>
        <div>
          <span>最新净值</span>
          <strong>{num(snapshot.latest_nav)}</strong>
        </div>
        <div>
          <span>产品规模</span>
          <strong>{money(snapshot.product_scale_bn)}</strong>
        </div>
        <div>
          <span>基准区间</span>
          <strong>{snapshot.benchmark || `${pct(snapshot.benchmark_lower)}-${pct(snapshot.benchmark_upper)}`}</strong>
        </div>
      </div>
    </section>
  );
}

function PeerTable({ rows }) {
  return (
    <section className="table-panel">
      <table>
        <thead>
          <tr>
            <th className="sticky-col">发行机构</th>
            <th className="sticky-col second">产品名称</th>
            <th>业绩比较基准</th>
            <th>总费率</th>
            <th>成立日期</th>
            <th>最新净值</th>
            <th>成立以来年化收益</th>
            <th>近3个月年化收益</th>
            <th>近1个月年化收益</th>
            <th>净值波动率</th>
            <th>最大回撤</th>
            <th>近3个月 Sharpe</th>
          </tr>
        </thead>
        <tbody>
          {(rows || []).map((row) => (
            <tr key={row.peer_product_code || row.product_code}>
              <td className="sticky-col">{row.issuer_name || row.issuer_type || '模拟发行机构'}</td>
              <td className="sticky-col second">
                <strong>{row.peer_product_name || row.product_name}</strong>
                <span>{row.peer_product_code || row.product_code}</span>
              </td>
              <td>{row.benchmark || '2.00%-4.00%'}</td>
              <td>{pct(row.total_fee_rate || row.fee_rate, 2)}</td>
              <td>{row.inception_date || '-'}</td>
              <td>{num(row.latest_nav)}</td>
              <td>{signedPct(row.since_inception_annual_return)}</td>
              <td>{signedPct(row.return_3m_annualized || Number(row.return_3m || 0) * 4)}</td>
              <td>{signedPct(row.return_1m_annualized || Number(row.return_1m || 0) * 12)}</td>
              <td>{pct(row.volatility)}</td>
              <td>{pct(row.max_drawdown)}</td>
              <td>{num(row.sharpe)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function MarketPercentile({ peer }) {
  const summary = peer?.market_percentile_summary || {};
  const indicators = summary.indicators || [];
  const conditions = summary.pool_conditions || [];
  return (
    <section className="panel">
      <div className="section-title">
        <span>全市场分位</span>
        <strong>模拟同业池 · {summary.sample_count || peer?.peer_count || 0} 个样本</strong>
      </div>
      <div className="pill-list">
        {conditions.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
      <div className="table-panel embedded-table">
        <table>
          <thead>
            <tr>
              <th>指标</th>
              <th>市场50%分位值</th>
              <th>本产品指标</th>
              <th>本产品市场分位</th>
            </tr>
          </thead>
          <tbody>
            {indicators.map((item) => (
              <tr key={item.metric}>
                <td>{item.metric}</td>
                <td>{item.metric.includes('Sharpe') ? num(item.market_p50) : pct(item.market_p50)}</td>
                <td>{item.metric.includes('Sharpe') ? num(item.product_value) : pct(item.product_value)}</td>
                <td>{pct(item.product_percentile, 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <PeerUniverseExplainer explainer={peer?.peer_universe_explainer} />
    </section>
  );
}

function PeerUniverseExplainer({ explainer }) {
  const included = explainer?.included || [];
  const excluded = explainer?.excluded || [];
  return (
    <div className="explainer-grid">
      <div>
        <h3>入池原因</h3>
        <p className="panel-copy">{explainer?.pool_rule || '按同类型、同风险等级、同期限、同渠道和成立满3个月筛选。'}</p>
        <div className="evidence-list">
          {included.slice(0, 6).map((item) => (
            <div className="evidence-row" key={item.peer_product_code}>
              <strong>{item.peer_product_code}</strong>
              <span>{(item.include_reason || []).join(' / ')}</span>
              <p>证据编号 {item.evidence_id}</p>
            </div>
          ))}
        </div>
      </div>
      <div>
        <h3>剔除原因</h3>
        <div className="evidence-list">
          {excluded.slice(0, 6).map((item) => (
            <div className="evidence-row muted" key={item.peer_product_code}>
              <strong>{item.peer_product_code}</strong>
              <span>{(item.exclude_reason || []).join(' / ')}</span>
              <p>证据编号 {item.evidence_id}</p>
            </div>
          ))}
          {!excluded.length ? <p className="panel-copy">当前演示样本未返回剔除明细。</p> : null}
        </div>
      </div>
    </div>
  );
}

function ChannelTable({ channel, selectedProduct }) {
  const rows = channel?.table || [];
  return (
    <section className="table-panel">
      <table>
        <thead>
          <tr>
            <th className="sticky-col">渠道名称</th>
            <th>同渠道样本数</th>
            <th>近3个月收益中位数</th>
            <th>本产品渠道分位</th>
            <th>渠道内排名</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.channel}-${row.product_type}`}>
              <td className="sticky-col">
                <strong>{row.channel}</strong>
                <span>{row.product_type}</span>
              </td>
              <td>{row.peer_count}</td>
              <td>{pct(row.median_return_3m || row.avg_return_3m)}</td>
              <td>{selectedProduct?.channel === row.channel ? pct(row.product_channel_percentile, 0) : '-'}</td>
              <td>{row.channel_rank || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function TopPeersTable({ topPeers }) {
  const rows = topPeers?.table || [];
  return (
    <section className="table-panel">
      <table>
        <thead>
          <tr>
            <th className="sticky-col">排名</th>
            <th className="sticky-col second">发行机构</th>
            <th>产品名称</th>
            <th>近3个月收益</th>
            <th>最大回撤</th>
            <th>Sharpe</th>
            <th>入选原因</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.peer_product_code}>
              <td className="sticky-col">{row.rank}</td>
              <td className="sticky-col second">{row.issuer_name || row.issuer_type || '模拟发行机构'}</td>
              <td>
                <strong>{row.peer_product_name || row.product_name}</strong>
                <span>{row.peer_product_code}</span>
              </td>
              <td>{signedPct(row.return_3m)}</td>
              <td>{pct(row.max_drawdown)}</td>
              <td>{num(row.sharpe)}</td>
              <td>{row.selection_reason || row.tracking_reason || '同类收益分位和风险调整指标靠前，用于周报跟踪样例。'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export default function ProductBenchmarkWorkbench({ initialProductCode = 'WP0031' }) {
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
  const [status, setStatus] = useState('数据来源：演示样本');
  const [loading, setLoading] = useState(false);
  const [selectedCode, setSelectedCode] = useState(initialProductCode);
  const [detail, setDetail] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [peer, setPeer] = useState(peerBenchmarkMock);
  const [channel, setChannel] = useState(channelBenchmarkMock);
  const [topPeers, setTopPeers] = useState(topPeersMock);
  const selectedProduct = useMemo(
    () => products.find((item) => item.product_code === selectedCode) || detail?.snapshot || products[0],
    [products, selectedCode, detail]
  );

  const filteredProducts = useMemo(() => {
    return products.filter((item) => {
      return Object.entries(filters).every(([key, value]) => {
        if (!value || key === 'report_date') return true;
        return String(item[key] || '') === String(value);
      });
    });
  }, [filters, products]);

  const scatter = useMemo(() => {
    const rows = filteredProducts.length ? filteredProducts : products;
    if (!rows.length) return [];
    const maxVol = Math.max(...rows.map((item) => Number(item.volatility || 0)), 0.01);
    const maxRet = Math.max(...rows.map((item) => Number(item.return_3m || 0)), 0.01);
    const minRet = Math.min(...rows.map((item) => Number(item.return_3m || 0)), -0.01);
    return rows.slice(0, 100).map((item) => ({
      ...item,
      x: (Number(item.volatility || 0) / maxVol) * 94 + 3,
      y: 94 - ((Number(item.return_3m || 0) - minRet) / Math.max(maxRet - minRet, 0.001)) * 88,
      size: Math.min(24, Math.max(8, Math.abs(Number(item.max_drawdown || 0)) * 220))
    }));
  }, [filteredProducts, products]);

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  async function refreshProducts() {
    setLoading(true);
    try {
      const payload = await getWeeklyProducts(filters);
      const nextProducts = payload.products || [];
      setProducts(nextProducts);
      setOptions(payload.filter_options || weeklyMock.filter_options);
      if (!nextProducts.some((item) => item.product_code === selectedCode)) {
        setSelectedCode(nextProducts[0]?.product_code || selectedCode);
      }
      setStatus('数据来源：演示样本');
    } catch {
      setProducts(weeklyProductsMock);
      setStatus('数据来源：演示样本');
    } finally {
      setLoading(false);
    }
  }

  async function openDetail(productCode = selectedCode, showDrawer = false) {
    if (!productCode) return;
    setSelectedCode(productCode);
    if (showDrawer) setDrawerOpen(true);
    setDetail(productDetailMock);
    setLoading(true);
    try {
      const [detailPayload, peerPayload] = await Promise.all([
        getWeeklyProduct(productCode, filters.report_date),
        runPeerBenchmark({ product_code: productCode, report_date: filters.report_date, limit: 16 })
      ]);
      setDetail(detailPayload);
      setPeer(peerPayload);
      setStatus('数据来源：演示样本');
    } catch {
      setDetail(productDetailMock);
      setPeer(peerBenchmarkMock);
      setStatus('数据来源：演示样本');
    } finally {
      setLoading(false);
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
      setStatus('数据来源：演示样本');
    } catch {
      setChannel(channelBenchmarkMock);
      setTopPeers(topPeersMock);
      setStatus('数据来源：演示样本');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshProducts();
    refreshBenchmarkTabs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (initialProductCode) {
      openDetail(initialProductCode);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialProductCode]);

  return (
    <div className="product-workspace">
      <aside className="filter-panel">
        <div className="section-title">
          <span>筛选器</span>
          <strong>{filteredProducts.length || products.length}</strong>
        </div>
        <ProductSelector products={products} selectedCode={selectedCode} onSelect={openDetail} />
        <SelectField label="资产类别" value={filters.product_type} options={options.product_type} onChange={(value) => updateFilter('product_type', value)} />
        <SelectField label="策略/系列" value={filters.product_series} options={options.product_series} onChange={(value) => updateFilter('product_series', value)} />
        <SelectField label="风险等级" value={filters.risk_level} options={options.risk_level} onChange={(value) => updateFilter('risk_level', value)} />
        <SelectField label="期限" value={filters.open_type} options={options.open_type} onChange={(value) => updateFilter('open_type', value)} />
        <SelectField label="渠道" value={filters.channel} options={options.channel} onChange={(value) => updateFilter('channel', value)} />
        <SelectField label="基准状态" value={filters.benchmark_status} options={options.benchmark_status} onChange={(value) => updateFilter('benchmark_status', value)} />
        <button className="primary-btn" onClick={refreshProducts} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <Filter size={18} />}
          更新样本
        </button>
      </aside>
      <main className="page-stack product-main">
        <div className="inline-status">
          <Search size={16} />
          <span>{status}</span>
          <strong>synthetic_weekly_snapshot</strong>
        </div>
        <SelectedProductCard product={selectedProduct} detail={detail} onOpen={openDetail} />
        <section className="panel">
          <div className="section-title">
            <span>收益-波动分布</span>
            <strong>x=净值波动率 · y=近3个月收益 · size=最大回撤</strong>
          </div>
          <div className="scatter-plot">
            {scatter.map((item) => (
              <button
                key={`dot-${item.product_code}`}
                className={`scatter-dot ${item.risk_level} ${item.product_code === selectedCode ? 'selected' : ''}`}
                style={{ left: `${item.x}%`, top: `${item.y}%`, width: item.size, height: item.size }}
                title={`${item.product_name}: ${pct(item.return_3m)} / ${pct(item.volatility)}`}
                onClick={() => openDetail(item.product_code)}
              />
            ))}
            <span className="axis x-axis">净值波动率</span>
            <span className="axis y-axis">近3个月收益</span>
          </div>
        </section>
        <div className="tabs">
          <button className={activeTab === 'peer' ? 'active' : ''} onClick={() => setActiveTab('peer')}>竞品对标</button>
          <button className={activeTab === 'market' ? 'active' : ''} onClick={() => setActiveTab('market')}>全市场分位</button>
          <button className={activeTab === 'channel' ? 'active' : ''} onClick={() => setActiveTab('channel')}>渠道对标</button>
          <button className={activeTab === 'top' ? 'active' : ''} onClick={() => setActiveTab('top')}>同类绩优产品</button>
        </div>
        {activeTab === 'peer' ? <PeerTable rows={peer.table || []} /> : null}
        {activeTab === 'market' ? <MarketPercentile peer={peer} /> : null}
        {activeTab === 'channel' ? <ChannelTable channel={channel} selectedProduct={selectedProduct} /> : null}
        {activeTab === 'top' ? <TopPeersTable topPeers={topPeers} /> : null}
      </main>
      {drawerOpen ? <DetailDrawer detail={detail} onClose={() => setDrawerOpen(false)} /> : null}
    </div>
  );
}
