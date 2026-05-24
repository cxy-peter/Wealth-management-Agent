import { FileText, Loader2, RefreshCw } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { generateWeeklyReport, getWeeklyProducts, getWeeklyReportDates, getWeeklySummary } from '../api.js';
import { sampleAnalysis, weeklyMock, weeklyProductsMock } from '../data/mockData.js';

function pct(value, digits = 1) {
  return `${(Number(value || 0) * 100).toFixed(digits)}%`;
}

function num(value, digits = 2) {
  return Number(value || 0).toFixed(digits);
}

function KpiCard({ label, value, tone = 'neutral' }) {
  return (
    <div className={`metric-tile ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
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

function CompactTable({ title, rows, columns, emptyText }) {
  return (
    <section className="table-panel">
      <div className="section-title table-title">
        <span>{title}</span>
        <strong>{rows.length}</strong>
      </div>
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={row.product_code || row.evidence_id || index}>
              {columns.map((column) => (
                <td key={column.key}>{column.render ? column.render(row) : row[column.key]}</td>
              ))}
            </tr>
          ))}
          {!rows.length ? (
            <tr>
              <td colSpan={columns.length}>{emptyText}</td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </section>
  );
}

function MarketBlock({ market }) {
  const nature = Object.entries(market?.by_investment_nature || {});
  const duration = Object.entries(market?.by_duration || {});
  return (
    <section className="split-grid">
      <div className="panel">
        <div className="section-title">
          <span>市场新发产品</span>
          <strong>{market?.new_product_count || 0} 只</strong>
        </div>
        <div className="two-column-facts">
          <div>
            <span>基准下限均值</span>
            <strong>{pct(market?.benchmark_lower_avg)}</strong>
          </div>
          <div>
            <span>基准上限均值</span>
            <strong>{pct(market?.benchmark_upper_avg)}</strong>
          </div>
        </div>
        <p className="panel-copy">市场发行数据来自 synthetic 周度样本，仅用于复刻周报统计口径。</p>
      </div>
      <div className="panel">
        <div className="section-title">
          <span>按投资性质 / 期限</span>
          <strong>{market?.evidence_id}</strong>
        </div>
        <div className="distribution-bars">
          {[...nature.slice(0, 5), ...duration.slice(0, 5)].map(([label, value]) => (
            <div key={label}>
              <span>{label}</span>
              <div>
                <i style={{ width: `${Math.min(100, Number(value) * 5)}%` }} />
              </div>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function WeeklyReportDashboard({ analysis, onAnalysis }) {
  const [summary, setSummary] = useState(weeklyMock);
  const [products, setProducts] = useState(weeklyProductsMock);
  const [dates, setDates] = useState([weeklyMock.report_date]);
  const [filters, setFilters] = useState({
    report_date: weeklyMock.report_date,
    product_series: '',
    product_type: '',
    channel: '',
    risk_level: '',
    benchmark_status: '',
    open_type: ''
  });
  const [activeTab, setActiveTab] = useState('overview');
  const [source, setSource] = useState('local fallback');
  const [loading, setLoading] = useState(false);

  const options = summary.filter_options || weeklyMock.filter_options;
  const kpis = summary.kpis || weeklyMock.kpis;

  const riskRows = useMemo(
    () => products.filter((item) => item.benchmark_status === 'below_lower' || Number(item.return_percentile || 1) <= 0.3).slice(0, 12),
    [products]
  );

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  async function refreshWeeklyData(nextFilters = filters) {
    setLoading(true);
    try {
      const [datePayload, summaryPayload, productsPayload] = await Promise.all([
        getWeeklyReportDates(),
        getWeeklySummary(nextFilters),
        getWeeklyProducts(nextFilters)
      ]);
      setDates(datePayload.dates || [summaryPayload.report_date]);
      setSummary(summaryPayload);
      setProducts(productsPayload.products || []);
      setSource('backend weekly API');
    } catch {
      setSummary(weeklyMock);
      setProducts(weeklyProductsMock);
      setSource('local mock fallback');
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateReport() {
    setLoading(true);
    try {
      const result = await generateWeeklyReport(filters);
      onAnalysis?.({
        ...sampleAnalysis,
        ...result,
        weekly_report_date: result.report_date,
        planner_plan: { task_type: 'standard_weekly_report', required_tools: result.source_files || [] }
      });
      setSummary(result);
      setSource('backend generated report');
    } catch {
      onAnalysis?.(sampleAnalysis);
      setSource('local mock fallback');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshWeeklyData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="page-stack">
      <section className="control-band weekly-control">
        <SelectField label="周报日期" value={filters.report_date} options={dates} onChange={(value) => updateFilter('report_date', value)} />
        <SelectField label="产品系列" value={filters.product_series} options={options.product_series} onChange={(value) => updateFilter('product_series', value)} />
        <SelectField label="产品类型" value={filters.product_type} options={options.product_type} onChange={(value) => updateFilter('product_type', value)} />
        <SelectField label="渠道" value={filters.channel} options={options.channel} onChange={(value) => updateFilter('channel', value)} />
        <SelectField label="风险等级" value={filters.risk_level} options={options.risk_level} onChange={(value) => updateFilter('risk_level', value)} />
        <SelectField label="期限" value={filters.open_type} options={options.open_type} onChange={(value) => updateFilter('open_type', value)} />
        <SelectField label="是否达标" value={filters.benchmark_status} options={options.benchmark_status} onChange={(value) => updateFilter('benchmark_status', value)} />
        <button className="primary-btn" onClick={() => refreshWeeklyData()} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
          更新周报
        </button>
        <button className="primary-btn secondary" onClick={handleGenerateReport} disabled={loading}>
          <FileText size={18} />
          生成摘要
        </button>
      </section>

      <div className="inline-status">
        <span>Source: {source}</span>
        <strong>{summary.report_date}</strong>
      </div>

      <section className="metric-grid">
        <KpiCard label="总规模" value={`${num(kpis.total_scale_bn)} 亿`} tone="green" />
        <KpiCard label="较上周" value={`${num(kpis.scale_wow_bn)} 亿`} tone={Number(kpis.scale_wow_bn) >= 0 ? 'green' : 'red'} />
        <KpiCard label="较上月" value={`${num(kpis.scale_mom_bn)} 亿`} />
        <KpiCard label="基准达标率" value={pct(kpis.benchmark_pass_rate)} />
        <KpiCard label="低分位产品" value={kpis.low_percentile_product_count || 0} tone="amber" />
        <KpiCard label="需关注产品" value={kpis.attention_product_count || 0} tone="red" />
      </section>

      <div className="tabs">
        <button className={activeTab === 'overview' ? 'active' : ''} onClick={() => setActiveTab('overview')}>周报概览</button>
        <button className={activeTab === 'risk' ? 'active' : ''} onClick={() => setActiveTab('risk')}>风险提示</button>
      </div>

      {activeTab === 'risk' ? (
        <CompactTable
          title="需关注产品清单"
          rows={riskRows}
          emptyText="当前筛选下暂无需关注样本。"
          columns={[
            { key: 'product_name', label: '产品名称' },
            { key: 'product_type', label: '类型' },
            { key: 'channel', label: '渠道' },
            { key: 'return_percentile', label: '收益分位', render: (row) => pct(row.return_percentile, 0) },
            { key: 'max_drawdown', label: '最大回撤', render: (row) => pct(row.max_drawdown, 2) },
            { key: 'evidence_id', label: 'Evidence' }
          ]}
        />
      ) : (
        <>
          <section className="split-grid triple">
            <CompactTable
              title="产品规模变化榜"
              rows={summary.scale_change_rank || []}
              emptyText="暂无规模变化样本。"
              columns={[
                { key: 'product_name', label: '产品名称' },
                { key: 'channel', label: '渠道' },
                { key: 'product_scale_bn', label: '规模', render: (row) => num(row.product_scale_bn) },
                { key: 'scale_wow_bn', label: '周变化', render: (row) => num(row.scale_wow_bn) }
              ]}
            />
            <CompactTable
              title="基准未达标产品"
              rows={summary.benchmark_failed_products || []}
              emptyText="当前筛选下暂无低于基准下限样本。"
              columns={[
                { key: 'product_name', label: '产品名称' },
                { key: 'product_type', label: '类型' },
                { key: 'since_inception_annual_return', label: '成立以来年化', render: (row) => pct(row.since_inception_annual_return) },
                { key: 'benchmark_lower', label: '基准下限', render: (row) => pct(row.benchmark_lower) }
              ]}
            />
            <CompactTable
              title="近 3 个月收益分位下降"
              rows={summary.percentile_decline_products || []}
              emptyText="暂无低分位样本。"
              columns={[
                { key: 'product_name', label: '产品名称' },
                { key: 'product_type', label: '类型' },
                { key: 'return_3m', label: '3M 收益', render: (row) => pct(row.return_3m) },
                { key: 'return_percentile', label: '收益分位', render: (row) => pct(row.return_percentile, 0) }
              ]}
            />
          </section>
          <MarketBlock market={summary.market_issuance} />
        </>
      )}
    </div>
  );
}
