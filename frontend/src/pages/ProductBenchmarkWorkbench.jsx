import { BarChart3, Download, Filter, Loader2, Search, X } from 'lucide-react';
import { memo, useEffect, useMemo, useState } from 'react';

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
import { sessionNavRecords } from '../sessionDataStore.js';

const COLORS = ['#22776f', '#b08324', '#415b76', '#b8463f', '#6d6aa8'];

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
          <option key={item} value={item}>{item}</option>
        ))}
      </select>
    </label>
  );
}

function LoadingPanel({ label = '加载中' }) {
  return (
    <section className="panel skeleton-panel">
      <Loader2 className="spin" size={20} />
      <span>{label}</span>
    </section>
  );
}

function buildSeriesFromMetric(row, range) {
  const weeksByRange = { '1m': 5, '3m': 13, '6m': 26, all: 40 };
  const weeks = weeksByRange[range] || 13;
  const endReturn = Number(row.return_3m || row.return_1m || 0);
  const drawdown = Math.abs(Number(row.max_drawdown || 0.02));
  const baseDate = new Date('2025-04-04T00:00:00Z');
  return Array.from({ length: weeks }, (_, index) => {
    const t = weeks <= 1 ? 0 : index / (weeks - 1);
    const wave = Math.sin(index * 1.7 + Number(String(row.product_code || row.peer_product_code || '').replace(/\D/g, '') || 1)) * drawdown * 0.18;
    const nav = 1 + endReturn * t + wave;
    const benchmarkNav = 1 + (Number(row.benchmark_lower || 0.02) / 52) * index;
    const date = new Date(baseDate);
    date.setDate(baseDate.getDate() - (weeks - 1 - index) * 7);
    return {
      date: date.toISOString().slice(0, 10),
      nav: Number(nav.toFixed(6)),
      benchmark_nav: Number(benchmarkNav.toFixed(6))
    };
  });
}

function normalizeSeries(rows) {
  if (!rows?.length) return [];
  const first = Number(rows[0].nav || 1) || 1;
  return rows.map((row) => ({ ...row, normalized_nav: Number((Number(row.nav || 0) / first).toFixed(6)) }));
}

function buildPolyline(rows, field, bounds) {
  if (!rows?.length) return '';
  const min = bounds.min;
  const max = bounds.max;
  return rows
    .map((row, index) => {
      const x = (index / Math.max(rows.length - 1, 1)) * 100;
      const y = 92 - ((Number(row[field] || 0) - min) / Math.max(max - min, 0.000001)) * 84;
      return `${x},${y}`;
    })
    .join(' ');
}

function metricFromSeries(rows, benchmarkRows) {
  if (!rows?.length) return {};
  const start = Number(rows[0].nav || 1);
  const end = Number(rows[rows.length - 1].nav || start);
  const returns = rows.slice(1).map((row, index) => Number(row.nav || 0) / Number(rows[index].nav || 1) - 1);
  const periodReturn = end / start - 1;
  const annualizedReturn = (1 + periodReturn) ** (52 / Math.max(rows.length, 1)) - 1;
  const avg = returns.reduce((sum, value) => sum + value, 0) / Math.max(returns.length, 1);
  const variance = returns.reduce((sum, value) => sum + (value - avg) ** 2, 0) / Math.max(returns.length, 1);
  const annualizedVolatility = Math.sqrt(variance) * Math.sqrt(52);
  let peak = start;
  let maxDrawdown = 0;
  for (const row of rows) {
    const nav = Number(row.nav || 0);
    peak = Math.max(peak, nav);
    maxDrawdown = Math.min(maxDrawdown, nav / peak - 1);
  }
  const sharpe = annualizedVolatility ? annualizedReturn / annualizedVolatility : 0;
  const calmar = maxDrawdown ? annualizedReturn / Math.abs(maxDrawdown) : 0;
  const benchmarkStart = Number(benchmarkRows?.[0]?.benchmark_nav || benchmarkRows?.[0]?.nav || 1);
  const benchmarkEnd = Number(benchmarkRows?.[benchmarkRows.length - 1]?.benchmark_nav || benchmarkRows?.[benchmarkRows.length - 1]?.nav || benchmarkStart);
  const benchmarkExcess = periodReturn - (benchmarkEnd / benchmarkStart - 1);
  return { periodReturn, annualizedReturn, annualizedVolatility, maxDrawdown, sharpe, calmar, benchmarkExcess };
}

function downloadText(filename, text) {
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function DetailDrawer({ detail, peer, onClose }) {
  const [tab, setTab] = useState('overview');
  if (!detail) return null;
  const snapshot = detail.snapshot || detail;
  const nav = detail.nav || [];
  const sourceMatrix = detail.field_source_matrix || [];
  const diligenceItems = [
    ['收益表现', `近3个月收益 ${pct(snapshot.return_3m)}，收益分位 ${pct(detail.percentile?.return_percentile, 0)}。`],
    ['风险暴露', `最大回撤 ${pct(snapshot.max_drawdown)}，波动率 ${pct(snapshot.volatility)}。`],
    ['基准达标', `当前基准状态 ${snapshot.benchmark_status}。`],
    ['市场分位', `模拟同业池样本 ${detail.percentile?.peer_count || 0} 个。`],
    ['渠道分位', '渠道分位需结合渠道对标 tab 复核。']
  ];
  return (
    <div className="drawer-backdrop" role="presentation">
      <aside className="review-drawer product-drawer" aria-label="产品详情">
        <div className="section-title">
          <span>{snapshot.product_name}</span>
          <button className="icon-btn" onClick={onClose} title="关闭详情"><X size={18} /></button>
        </div>
        <div className="tabs compact-tabs">
          {[
            ['overview', 'Overview'],
            ['nav', 'NAV Timeline'],
            ['peer', 'Peer Benchmark'],
            ['diligence', 'AI Diligence'],
            ['lineage', 'Evidence / Lineage']
          ].map(([id, label]) => (
            <button key={id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}>{label}</button>
          ))}
        </div>
        {tab === 'overview' ? (
          <section className="metric-grid compact">
            <div className="metric-tile green"><span>近3个月收益</span><strong>{signedPct(snapshot.return_3m)}</strong></div>
            <div className="metric-tile"><span>净值波动率</span><strong>{pct(snapshot.volatility)}</strong></div>
            <div className="metric-tile red"><span>最大回撤</span><strong>{pct(snapshot.max_drawdown)}</strong></div>
          </section>
        ) : null}
        {tab === 'nav' ? <NavCompareChart series={[{ code: snapshot.product_code, name: snapshot.product_name, rows: normalizeSeries(nav) }]} mode="raw" /> : null}
        {tab === 'peer' ? <PeerTable rows={(peer?.table || []).slice(0, 8)} /> : null}
        {tab === 'diligence' ? (
          <section className="panel">
            <div className="section-title"><span>产品质检解释</span><strong>非投资建议</strong></div>
            <div className="evidence-list">
              {diligenceItems.map(([title, body]) => (
                <div className="evidence-row" key={title}><strong>{title}</strong><span>{body}</span></div>
              ))}
              <div className="evidence-row strong"><strong>red flags</strong><span>关注基准状态、低分位、规模下降和数据缺失。</span></div>
              <div className="evidence-row"><strong>follow-up questions</strong><span>是否有最新公告、是否有渠道反馈、是否需要上传更近净值？</span></div>
            </div>
          </section>
        ) : null}
        {tab === 'lineage' ? (
          <section className="table-panel compact-table">
            <table>
              <thead><tr><th>字段</th><th>来源</th><th>as_of_date</th><th>confidence</th><th>证据编号</th></tr></thead>
              <tbody>
                {sourceMatrix.map((item) => (
                  <tr key={`${item.field}-${item.evidence_id}`}>
                    <td>{item.field}</td><td>{item.source_type || item.source}</td><td>{item.as_of_date}</td><td>{item.confidence}</td><td>{item.evidence_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        ) : null}
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
        <button className="primary-btn secondary" onClick={() => onOpen(snapshot.product_code, true)}>查看产品详情</button>
      </div>
      <div className="focus-grid">
        <div><strong>{snapshot.product_name || '未选择产品'}</strong><span>{snapshot.product_code} · {snapshot.product_type} · {snapshot.channel}</span></div>
        <div><span>风险等级</span><strong className={`risk-chip ${snapshot.risk_level || ''}`}>{snapshot.risk_level || '-'}</strong></div>
        <div><span>最新净值</span><strong>{num(snapshot.latest_nav)}</strong></div>
        <div><span>产品规模</span><strong>{money(snapshot.product_scale_bn)}</strong></div>
        <div><span>基准区间</span><strong>{snapshot.benchmark || `${pct(snapshot.benchmark_lower)}-${pct(snapshot.benchmark_upper)}`}</strong></div>
      </div>
    </section>
  );
}

const PeerTable = memo(function PeerTable({ rows }) {
  return (
    <section className="table-panel compact-table">
      <table>
        <thead>
          <tr>
            <th className="sticky-col">发行机构</th><th className="sticky-col second">产品名称</th><th>业绩比较基准</th><th>总费率</th><th>成立日期</th><th>最新净值</th><th>成立以来年化</th><th>近3个月年化</th><th>近1个月年化</th><th>波动率</th><th>最大回撤</th><th>Sharpe</th>
          </tr>
        </thead>
        <tbody>
          {(rows || []).map((row) => (
            <tr key={row.peer_product_code || row.product_code}>
              <td className="sticky-col">{row.issuer_name || row.issuer_type || '模拟发行机构'}</td>
              <td className="sticky-col second"><strong>{row.peer_product_name || row.product_name}</strong><span>{row.peer_product_code || row.product_code}</span></td>
              <td>{row.benchmark || '2.00%-4.00%'}</td><td>{pct(row.total_fee_rate || row.fee_rate, 2)}</td><td>{row.inception_date || '-'}</td><td>{num(row.latest_nav)}</td><td>{signedPct(row.since_inception_annual_return)}</td><td>{signedPct(row.return_3m_annualized || Number(row.return_3m || 0) * 4)}</td><td>{signedPct(row.return_1m_annualized || Number(row.return_1m || 0) * 12)}</td><td>{pct(row.volatility)}</td><td>{pct(row.max_drawdown)}</td><td>{num(row.sharpe)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
});

const MarketPercentile = memo(function MarketPercentile({ peer }) {
  const summary = peer?.market_percentile_summary || {};
  const indicators = summary.indicators || [];
  const histogram = summary.return_histogram || [];
  return (
    <section className="panel">
      <div className="section-title">
        <span>全市场分位</span>
        <strong>模拟同业池 · {summary.sample_count || peer?.peer_count || 0} 个样本</strong>
      </div>
      <div className="pill-list">
        {(summary.pool_conditions || []).map((item) => <span key={item}>{item}</span>)}
      </div>
      <div className="split-grid">
        <div className="table-panel compact-table embedded-table">
          <table>
            <thead><tr><th>指标</th><th>市场50%分位值</th><th>本产品指标</th><th>本产品分位</th></tr></thead>
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
        <div className="panel histogram-panel">
          <div className="section-title"><span>收益率分布</span><strong>bucket histogram</strong></div>
          <div className="histogram-bars">
            {histogram.map((bucket) => (
              <div key={`${bucket.from}-${bucket.to}`} title={`${pct(bucket.from)} 至 ${pct(bucket.to)}: ${bucket.count}`}>
                <i style={{ height: `${Math.max(8, bucket.count * 9)}px` }} />
                <span>{bucket.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      <section className="split-grid">
        <SmallPeerList title="Top 10" rows={summary.top_10 || []} />
        <SmallPeerList title="Bottom 10" rows={summary.bottom_10 || []} />
      </section>
    </section>
  );
});

function SmallPeerList({ title, rows }) {
  return (
    <div className="table-panel compact-table">
      <div className="section-title table-title"><span>{title}</span><strong>{rows.length}</strong></div>
      <table>
        <thead><tr><th>产品</th><th>3M收益</th><th>回撤</th><th>Sharpe</th></tr></thead>
        <tbody>{rows.map((row) => <tr key={row.peer_product_code}><td>{row.peer_product_name}</td><td>{pct(row.return_3m)}</td><td>{pct(row.max_drawdown)}</td><td>{num(row.sharpe)}</td></tr>)}</tbody>
      </table>
    </div>
  );
}

function ChannelTable({ channel, selectedProduct }) {
  const rows = channel?.table || [];
  return (
    <section className="table-panel compact-table">
      <table>
        <thead><tr><th className="sticky-col">渠道名称</th><th>同渠道样本数</th><th>近3个月收益中位数</th><th>本产品渠道分位</th><th>渠道内排名</th></tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.channel}-${row.product_type}`}>
              <td className="sticky-col"><strong>{row.channel}</strong><span>{row.product_type}</span></td>
              <td>{row.peer_count}</td><td>{pct(row.median_return_3m || row.avg_return_3m)}</td><td>{selectedProduct?.channel === row.channel ? pct(row.product_channel_percentile, 0) : '-'}</td><td>{row.channel_rank || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

const TopPeersTable = memo(function TopPeersTable({ topPeers }) {
  const rows = topPeers?.table || [];
  return (
    <section className="table-panel compact-table">
      <table>
        <thead><tr><th className="sticky-col">排名</th><th className="sticky-col second">发行机构</th><th>产品名称</th><th>近3个月收益</th><th>最大回撤</th><th>Sharpe</th><th>入选原因</th></tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.peer_product_code}>
              <td className="sticky-col">{row.rank}</td><td className="sticky-col second">{row.issuer_name || row.issuer_type || '模拟发行机构'}</td><td><strong>{row.peer_product_name || row.product_name}</strong><span>{row.peer_product_code}</span></td><td>{signedPct(row.return_3m)}</td><td>{pct(row.max_drawdown)}</td><td>{num(row.sharpe)}</td><td>{row.selection_reason || row.tracking_reason || '同类收益分位和风险调整指标靠前，用于周报跟踪样例。'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
});

function NavCompareChart({ series, mode }) {
  const field = mode === 'normalized' ? 'normalized_nav' : 'nav';
  const allValues = series.flatMap((item) => item.rows.map((row) => Number(row[field] || 0)));
  const bounds = { min: Math.min(...allValues, 0.95), max: Math.max(...allValues, 1.05) };
  return (
    <section className="panel">
      <div className="multi-line-chart">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none">
          {series.map((item, index) => (
            <polyline key={item.code} points={buildPolyline(item.rows, field, bounds)} style={{ stroke: COLORS[index % COLORS.length] }} />
          ))}
        </svg>
      </div>
      <div className="chart-legend wrap">
        {series.map((item, index) => (
          <span key={item.code}><i style={{ background: COLORS[index % COLORS.length] }} />{item.name}</span>
        ))}
      </div>
    </section>
  );
}

function FiveProductCompare({ selectedProduct, detail, peer }) {
  const [range, setRange] = useState('3m');
  const [mode, setMode] = useState('normalized');
  const peerRows = peer?.table || [];
  const defaultCodes = useMemo(() => [selectedProduct?.product_code, ...peerRows.slice(0, 4).map((row) => row.peer_product_code)].filter(Boolean), [selectedProduct, peerRows]);
  const [selectedCodes, setSelectedCodes] = useState(defaultCodes);

  useEffect(() => {
    setSelectedCodes(defaultCodes);
  }, [defaultCodes.join('|')]);

  const candidates = useMemo(() => {
    const productRows = [{ ...selectedProduct, peer_product_code: selectedProduct?.product_code, peer_product_name: selectedProduct?.product_name, isOwn: true }, ...peerRows].filter(Boolean);
    return productRows.slice(0, 18);
  }, [selectedProduct, peerRows]);

  const series = useMemo(() => {
    const uploadedNav = sessionNavRecords(selectedCodes);
    return selectedCodes.map((code) => {
      const candidate = candidates.find((row) => (row.peer_product_code || row.product_code) === code) || {};
      const uploadedRows = uploadedNav.filter((row) => row.product_code === code).map((row) => ({ date: row.nav_date, nav: row.nav, benchmark_nav: row.benchmark_nav || row.nav }));
      const baseRows = code === selectedProduct?.product_code && detail?.nav?.length ? detail.nav : buildSeriesFromMetric(candidate, range);
      return {
        code,
        name: candidate.peer_product_name || candidate.product_name || code,
        rows: normalizeSeries(uploadedRows.length ? uploadedRows : baseRows)
      };
    });
  }, [selectedCodes, candidates, detail, range, selectedProduct]);

  const metrics = useMemo(() => series.map((item) => ({ ...item, metrics: metricFromSeries(item.rows, item.rows) })), [series]);

  function toggleCode(code) {
    setSelectedCodes((current) => {
      if (current.includes(code)) return current.filter((item) => item !== code);
      if (current.length >= 5) return current;
      return [...current, code];
    });
  }

  function exportCsv() {
    const header = ['product_code', 'product_name', 'date', 'nav', 'benchmark_nav', 'normalized_nav'];
    const lines = [header.join(',')];
    for (const item of series) {
      for (const row of item.rows) {
        lines.push([item.code, item.name, row.date, row.nav, row.benchmark_nav, row.normalized_nav].join(','));
      }
    }
    downloadText('five_product_nav_compare.csv', lines.join('\n'));
  }

  function exportMarkdown() {
    const lines = ['# 5只产品净值对比摘要', '', '本摘要基于演示数据或用户本地上传数据生成，仅用于投研辅助，不构成投资建议。', ''];
    for (const item of metrics) {
      lines.push(`- ${item.name}: 区间收益 ${pct(item.metrics.periodReturn)}，最大回撤 ${pct(item.metrics.maxDrawdown)}，Sharpe ${num(item.metrics.sharpe)}。`);
    }
    downloadText('five_product_nav_compare.md', lines.join('\n'));
  }

  return (
    <div className="page-stack nested-stack">
      <section className="panel">
        <div className="section-title"><span>5只产品净值对比</span><strong>{selectedCodes.length}/5</strong></div>
        <div className="compare-controls">
          <label className="field-group"><span>时间范围</span><select value={range} onChange={(event) => setRange(event.target.value)}><option value="1m">近1月</option><option value="3m">近3月</option><option value="6m">近6月</option><option value="all">成立以来</option></select></label>
          <label className="field-group"><span>曲线模式</span><select value={mode} onChange={(event) => setMode(event.target.value)}><option value="normalized">起点归一化净值</option><option value="raw">原始净值</option></select></label>
          <button className="primary-btn secondary" onClick={exportCsv}><Download size={16} />导出 CSV</button>
          <button className="primary-btn secondary" onClick={exportMarkdown}><Download size={16} />导出 Markdown</button>
        </div>
        <div className="check-list">
          {candidates.map((row) => {
            const code = row.peer_product_code || row.product_code;
            return (
              <label key={code}>
                <input type="checkbox" checked={selectedCodes.includes(code)} onChange={() => toggleCode(code)} />
                <span>{row.peer_product_name || row.product_name}</span>
              </label>
            );
          })}
        </div>
      </section>
      <NavCompareChart series={series} mode={mode} />
      <section className="table-panel compact-table">
        <table>
          <thead><tr><th>产品</th><th>period_return</th><th>annualized_return</th><th>annualized_volatility</th><th>max_drawdown</th><th>sharpe</th><th>calmar</th><th>benchmark_excess</th><th>market_percentile</th></tr></thead>
          <tbody>
            {metrics.map((item, index) => (
              <tr key={item.code}>
                <td>{item.name}</td><td>{pct(item.metrics.periodReturn)}</td><td>{pct(item.metrics.annualizedReturn)}</td><td>{pct(item.metrics.annualizedVolatility)}</td><td>{pct(item.metrics.maxDrawdown)}</td><td>{num(item.metrics.sharpe)}</td><td>{num(item.metrics.calmar)}</td><td>{pct(item.metrics.benchmarkExcess)}</td><td>{index === 0 ? pct(peer?.percentile?.return_percentile, 0) : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

export default function ProductBenchmarkWorkbench({ initialProductCode = 'WP0031' }) {
  const [filters, setFilters] = useState({ report_date: weeklyMock.report_date, product_series: '', product_type: '', risk_level: '', channel: '', open_type: '', benchmark_status: '' });
  const [products, setProducts] = useState(weeklyProductsMock);
  const [options, setOptions] = useState(weeklyMock.filter_options);
  const [activeTab, setActiveTab] = useState('peer');
  const [status, setStatus] = useState('数据来源：演示样本');
  const [loading, setLoading] = useState(false);
  const [tabLoading, setTabLoading] = useState({});
  const [selectedCode, setSelectedCode] = useState(initialProductCode);
  const [detail, setDetail] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [peer, setPeer] = useState(peerBenchmarkMock);
  const [channel, setChannel] = useState(null);
  const [topPeers, setTopPeers] = useState(null);
  const [cache, setCache] = useState({});

  const cacheKey = (tabName, productCode = selectedCode) => `${productCode}_${filters.report_date}_${tabName}_${JSON.stringify(filters)}`;
  const selectedProduct = useMemo(() => products.find((item) => item.product_code === selectedCode) || detail?.snapshot || products[0], [products, selectedCode, detail]);

  const filteredProducts = useMemo(() => products.filter((item) => Object.entries(filters).every(([key, value]) => !value || key === 'report_date' || String(item[key] || '') === String(value))), [filters, products]);

  const scatter = useMemo(() => {
    const rows = filteredProducts.length ? filteredProducts : products;
    if (!rows.length) return [];
    const maxVol = Math.max(...rows.map((item) => Number(item.volatility || 0)), 0.01);
    const maxRet = Math.max(...rows.map((item) => Number(item.return_3m || 0)), 0.01);
    const minRet = Math.min(...rows.map((item) => Number(item.return_3m || 0)), -0.01);
    return rows.slice(0, 100).map((item) => ({ ...item, x: (Number(item.volatility || 0) / maxVol) * 94 + 3, y: 94 - ((Number(item.return_3m || 0) - minRet) / Math.max(maxRet - minRet, 0.001)) * 88, size: Math.min(24, Math.max(8, Math.abs(Number(item.max_drawdown || 0)) * 220)) }));
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
      if (!nextProducts.some((item) => item.product_code === selectedCode)) setSelectedCode(nextProducts[0]?.product_code || selectedCode);
      setStatus(payload.source_type === 'manual_upload_overlay' ? '数据来源：用户上传 + 演示样本' : '数据来源：演示样本');
    } catch {
      setProducts(weeklyProductsMock);
      setStatus('数据来源：演示样本');
    } finally {
      setLoading(false);
    }
  }

  async function loadPeer(productCode = selectedCode, showDrawer = false) {
    if (!productCode) return;
    setSelectedCode(productCode);
    if (showDrawer) setDrawerOpen(true);
    const key = cacheKey('peer', productCode);
    if (cache[key]) {
      setDetail(cache[key].detail);
      setPeer(cache[key].peer);
      return;
    }
    setTabLoading((current) => ({ ...current, peer: true }));
    try {
      const [detailPayload, peerPayload] = await Promise.all([
        getWeeklyProduct(productCode, filters.report_date),
        runPeerBenchmark({ product_code: productCode, report_date: filters.report_date, limit: 16 })
      ]);
      setDetail(detailPayload);
      setPeer(peerPayload);
      setCache((current) => ({ ...current, [key]: { detail: detailPayload, peer: peerPayload } }));
    } catch {
      setDetail(productDetailMock);
      setPeer(peerBenchmarkMock);
    } finally {
      setTabLoading((current) => ({ ...current, peer: false }));
    }
  }

  async function ensureTab(tabName) {
    setActiveTab(tabName);
    const key = cacheKey(tabName);
    if (cache[key]) {
      if (tabName === 'channel') setChannel(cache[key]);
      if (tabName === 'top') setTopPeers(cache[key]);
      return;
    }
    if (tabName === 'market' || tabName === 'nav') return;
    setTabLoading((current) => ({ ...current, [tabName]: true }));
    try {
      if (tabName === 'channel') {
        const payload = await runChannelBenchmark({ product_type: filters.product_type || undefined, channel: filters.channel || undefined });
        setChannel(payload);
        setCache((current) => ({ ...current, [key]: payload }));
      }
      if (tabName === 'top') {
        const payload = await runTopPeers({ product_type: filters.product_type || undefined, report_date: filters.report_date, limit: 20 });
        setTopPeers(payload);
        setCache((current) => ({ ...current, [key]: payload }));
      }
    } catch {
      if (tabName === 'channel') setChannel(channelBenchmarkMock);
      if (tabName === 'top') setTopPeers(topPeersMock);
    } finally {
      setTabLoading((current) => ({ ...current, [tabName]: false }));
    }
  }

  useEffect(() => {
    refreshProducts();
    loadPeer(initialProductCode);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (initialProductCode) loadPeer(initialProductCode);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialProductCode]);

  const tabs = [
    ['peer', '竞品对标'],
    ['market', '全市场分位'],
    ['channel', '渠道对标'],
    ['top', '同类绩优产品'],
    ['nav', '净值对比']
  ];

  return (
    <div className="product-workspace">
      <aside className="filter-panel">
        <div className="section-title"><span>筛选器</span><strong>{filteredProducts.length || products.length}</strong></div>
        <label className="field-group"><span>选择产品</span><select value={selectedCode || ''} onChange={(event) => loadPeer(event.target.value)}>{products.slice(0, 120).map((item) => <option key={item.product_code} value={item.product_code}>{item.product_code} · {item.product_name}</option>)}</select></label>
        <SelectField label="资产类别" value={filters.product_type} options={options.product_type} onChange={(value) => updateFilter('product_type', value)} />
        <SelectField label="策略/系列" value={filters.product_series} options={options.product_series} onChange={(value) => updateFilter('product_series', value)} />
        <SelectField label="风险等级" value={filters.risk_level} options={options.risk_level} onChange={(value) => updateFilter('risk_level', value)} />
        <SelectField label="期限" value={filters.open_type} options={options.open_type} onChange={(value) => updateFilter('open_type', value)} />
        <SelectField label="渠道" value={filters.channel} options={options.channel} onChange={(value) => updateFilter('channel', value)} />
        <SelectField label="基准状态" value={filters.benchmark_status} options={options.benchmark_status} onChange={(value) => updateFilter('benchmark_status', value)} />
        <button className="primary-btn" onClick={refreshProducts} disabled={loading}>{loading ? <Loader2 className="spin" size={18} /> : <Filter size={18} />}更新样本</button>
      </aside>
      <main className="page-stack product-main">
        <div className="inline-status"><Search size={16} /><span>{status}</span><strong>synthetic_weekly_snapshot / manual_upload</strong></div>
        <SelectedProductCard product={selectedProduct} detail={detail} onOpen={loadPeer} />
        <section className="panel">
          <div className="section-title"><span>收益-波动分布</span><strong>x=净值波动率 · y=近3个月收益 · size=最大回撤</strong></div>
          <div className="scatter-plot">
            {scatter.map((item) => <button key={`dot-${item.product_code}`} className={`scatter-dot ${item.risk_level} ${item.product_code === selectedCode ? 'selected' : ''}`} style={{ left: `${item.x}%`, top: `${item.y}%`, width: item.size, height: item.size }} title={`${item.product_name}: ${pct(item.return_3m)} / ${pct(item.volatility)}`} onClick={() => loadPeer(item.product_code)} />)}
            <span className="axis x-axis">净值波动率</span><span className="axis y-axis">近3个月收益</span>
          </div>
        </section>
        <div className="tabs">{tabs.map(([id, label]) => <button key={id} className={activeTab === id ? 'active' : ''} onClick={() => ensureTab(id)}>{label}</button>)}</div>
        {activeTab === 'peer' ? (tabLoading.peer ? <LoadingPanel label="加载竞品池" /> : <PeerTable rows={peer.table || []} />) : null}
        {activeTab === 'market' ? (tabLoading.market ? <LoadingPanel label="加载全市场分位" /> : <MarketPercentile peer={peer} />) : null}
        {activeTab === 'channel' ? (tabLoading.channel ? <LoadingPanel label="加载渠道对标" /> : <ChannelTable channel={channel || channelBenchmarkMock} selectedProduct={selectedProduct} />) : null}
        {activeTab === 'top' ? (tabLoading.top ? <LoadingPanel label="加载绩优产品" /> : <TopPeersTable topPeers={topPeers || topPeersMock} />) : null}
        {activeTab === 'nav' ? <FiveProductCompare selectedProduct={selectedProduct} detail={detail} peer={peer} /> : null}
      </main>
      {drawerOpen ? <DetailDrawer detail={detail} peer={peer} onClose={() => setDrawerOpen(false)} /> : null}
    </div>
  );
}
