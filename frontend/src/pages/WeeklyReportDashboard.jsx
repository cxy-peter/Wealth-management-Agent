import { BarChart3, FileCheck2, FileText, Loader2, RefreshCw, ShieldCheck } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { generateWeeklyReport, getDataFreshness, getWeeklyProducts, getWeeklyReportDates, getWeeklySummary } from '../api.js';
import { dataFreshnessMock, dpoAgentEvalMock, sampleAnalysis, weeklyMock, weeklyProductsMock } from '../data/mockData.js';

function pct(value, digits = 1) {
  return `${(Number(value || 0) * 100).toFixed(digits)}%`;
}

function num(value, digits = 2) {
  return Number(value || 0).toFixed(digits);
}

function KpiCard({ label, value, tone = 'neutral', testId }) {
  return (
    <div className={`metric-tile ${tone}`} data-testid={testId}>
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

function FocusTable({ title, rows, columns, emptyText, onRowClick }) {
  return (
    <section className="table-panel focus-table">
      <div className="section-title table-title">
        <span>{title}</span>
        <strong>{rows.length}</strong>
      </div>
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} className={column.sticky ? `sticky-col ${column.sticky === true ? '' : column.sticky}` : ''}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr
              key={row.product_code || row.evidence_id || index}
              className={onRowClick ? 'clickable-row' : ''}
              onClick={() => onRowClick?.(row.product_code)}
            >
              {columns.map((column) => (
                <td key={column.key} className={column.sticky ? `sticky-col ${column.sticky === true ? '' : column.sticky}` : ''}>
                  {column.render ? column.render(row) : row[column.key]}
                </td>
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

function TaskCard({ icon: Icon, title, description, button, onClick }) {
  return (
    <article className="task-card">
      <div className="task-icon"><Icon size={20} /></div>
      <div>
        <h3>{title}</h3>
        <p>{description}</p>
        <button className="primary-btn" onClick={onClick}>{button}</button>
      </div>
    </article>
  );
}

function DataSourceFreshness({ freshness }) {
  const sources = freshness?.sources || [];
  return (
    <section className="panel technical-panel">
      <div className="section-title">
        <span>数据源与新鲜度</span>
        <strong>{sources.length} 类来源</strong>
      </div>
      <div className="distribution-bars">
        {sources.slice(0, 5).map((item) => (
          <div key={`${item.source_type}-${item.source_name}`}>
            <span>{item.source_type}</span>
            <div><i style={{ width: `${Math.max(8, Math.min(100, 100 - Number(item.staleness_days || 0) * 2))}%` }} /></div>
            <strong>{item.adapter_status}</strong>
          </div>
        ))}
      </div>
      <p className="panel-copy">演示环境区分历史样本、公开披露样本、行业报告、手工上传和 synthetic weekly snapshot，不声称拥有全市场实时产品级数据。</p>
    </section>
  );
}

function AiCalibrationCard({ analysis }) {
  const dpoScore = Math.round((dpoAgentEvalMock.variants.dpo_adapter.average_report_score || 0.93) * 100);
  const templateScore = Math.round((dpoAgentEvalMock.variants.template_baseline.average_report_score || 0.57) * 100);
  return (
    <section className="panel calibration-card">
      <div className="section-title">
        <span>AI 报告校准</span>
        <strong>DPO preference eval demo / 未加载真实 adapter</strong>
      </div>
      <div className="score-row">
        <div><span>模板草稿</span><strong>{templateScore}/100</strong></div>
        <div><span>AI 校准稿</span><strong>{dpoScore}/100</strong></div>
        <div><span>证据覆盖</span><strong>100%</strong></div>
        <div><span>禁用措辞</span><strong>0 次</strong></div>
      </div>
      <p className="panel-copy">AI 报告校准只用于对齐周报文风、证据覆盖、风险提示、分位解释和禁用措辞，不用于生成投资建议。</p>
      <details>
        <summary>查看技术指标</summary>
        <pre className="json-block">{JSON.stringify({ dpo_eval: dpoAgentEvalMock, report: analysis?.verification_result || {} }, null, 2)}</pre>
      </details>
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
          <span>市场新发产品概览</span>
          <strong>{market?.new_product_count || 0} 只</strong>
        </div>
        <div className="two-column-facts">
          <div><span>基准下限均值</span><strong>{pct(market?.benchmark_lower_avg)}</strong></div>
          <div><span>基准上限均值</span><strong>{pct(market?.benchmark_upper_avg)}</strong></div>
        </div>
        <p className="panel-copy">市场发行统计来自演示样本，只用于复刻周报统计口径。</p>
      </div>
      <div className="panel">
        <div className="section-title">
          <span>按投资性质 / 期限</span>
          <strong>{market?.evidence_id || 'demo_evidence'}</strong>
        </div>
        <div className="distribution-bars">
          {[...nature.slice(0, 5), ...duration.slice(0, 5)].map(([label, value]) => (
            <div key={label}>
              <span>{label}</span>
              <div><i style={{ width: `${Math.min(100, Number(value) * 5)}%` }} /></div>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function WeeklyReportDashboard({ analysis, onAnalysis, onOpenBenchmark, onOpenTrace }) {
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
  const [freshness, setFreshness] = useState(dataFreshnessMock);
  const [source, setSource] = useState('演示样本');
  const [loading, setLoading] = useState(false);

  const options = summary.filter_options || weeklyMock.filter_options;
  const kpis = summary.kpis || weeklyMock.kpis;
  const scaleDownRows = useMemo(
    () => [...products].filter((item) => Number(item.scale_wow_bn || 0) < 0).sort((a, b) => Number(a.scale_wow_bn) - Number(b.scale_wow_bn)).slice(0, 10),
    [products]
  );

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  async function refreshWeeklyData(nextFilters = filters) {
    setLoading(true);
    try {
      const [datePayload, summaryPayload, productsPayload, freshnessPayload] = await Promise.all([
        getWeeklyReportDates(),
        getWeeklySummary(nextFilters),
        getWeeklyProducts(nextFilters),
        getDataFreshness()
      ]);
      setDates(datePayload.dates || [summaryPayload.report_date]);
      setSummary(summaryPayload);
      setProducts(productsPayload.products || []);
      setFreshness(freshnessPayload);
      setSource('演示样本');
    } catch {
      setSummary(weeklyMock);
      setProducts(weeklyProductsMock);
      setFreshness(dataFreshnessMock);
      setSource('演示样本');
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
    } catch {
      onAnalysis?.(sampleAnalysis);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refreshWeeklyData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const commonColumns = [
    { key: 'product_name', label: '产品名称', sticky: true, render: (row) => <strong>{row.product_name}</strong> },
    { key: 'product_code', label: '产品代码', sticky: 'second' },
    { key: 'risk_level', label: '风险等级', sticky: 'third', render: (row) => <span className={`risk-chip ${row.risk_level}`}>{row.risk_level}</span> }
  ];

  return (
    <div className="page-stack">
      <section className="workbench-hero">
        <div>
          <p className="eyebrow">产品周报 / 竞品对标 / 报告质检</p>
          <h2>资管产品周报工作台</h2>
          <p>基于产品周报、净值表现、同业产品池与渠道分位数据，自动生成周报摘要、竞品对标、风险提示和报告质检结果。</p>
        </div>
        <div className="hero-meta">
          <span>数据来源：{source}</span>
          <strong>{summary.report_date}</strong>
        </div>
      </section>

      <section className="metric-grid hero-kpis">
        <KpiCard label="产品数" value={summary.product_count || products.length} tone="green" testId="product-count-kpi" />
        <KpiCard label="总规模" value={`${num(kpis.total_scale_bn)} 亿`} />
        <KpiCard label="较上周变化" value={`${num(kpis.scale_wow_bn)} 亿`} tone={Number(kpis.scale_wow_bn) >= 0 ? 'green' : 'red'} />
        <KpiCard label="基准达标率" value={pct(kpis.benchmark_pass_rate)} />
        <KpiCard label="需关注产品数" value={kpis.attention_product_count || 0} tone="red" />
      </section>

      <section className="task-grid">
        <TaskCard
          icon={FileText}
          title="生成产品情况周报"
          description="汇总规模变化、基准达标、收益分位和风险产品。"
          button="生成周报摘要"
          onClick={handleGenerateReport}
        />
        <TaskCard
          icon={BarChart3}
          title="做单产品竞品对标"
          description="选择一个产品，查看竞品、全市场分位、渠道分位和同类绩优产品。"
          button="开始对标"
          onClick={() => onOpenBenchmark?.('WP0031')}
        />
        <TaskCard
          icon={FileCheck2}
          title="查看 AI 报告校准"
          description="对比模板草稿和 AI 校准稿，检查数字、证据和合规措辞。"
          button="查看质检结果"
          onClick={onOpenTrace}
        />
      </section>

      <section className="control-band weekly-control">
        <SelectField label="周报日期" value={filters.report_date} options={dates} onChange={(value) => updateFilter('report_date', value)} />
        <SelectField label="产品系列" value={filters.product_series} options={options.product_series} onChange={(value) => updateFilter('product_series', value)} />
        <SelectField label="产品类型" value={filters.product_type} options={options.product_type} onChange={(value) => updateFilter('product_type', value)} />
        <SelectField label="渠道" value={filters.channel} options={options.channel} onChange={(value) => updateFilter('channel', value)} />
        <SelectField label="风险等级" value={filters.risk_level} options={options.risk_level} onChange={(value) => updateFilter('risk_level', value)} />
        <SelectField label="期限" value={filters.open_type} options={options.open_type} onChange={(value) => updateFilter('open_type', value)} />
        <SelectField label="是否达标" value={filters.benchmark_status} options={options.benchmark_status} onChange={(value) => updateFilter('benchmark_status', value)} />
        <button className="primary-btn secondary" onClick={() => refreshWeeklyData()} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
          更新周报
        </button>
      </section>

      <section className="section-heading">
        <div>
          <p className="eyebrow">本周重点</p>
          <h3>需关注产品、基准状态和市场发行</h3>
        </div>
        <ShieldCheck size={22} />
      </section>

      <section className="split-grid triple">
        <FocusTable
          title="需关注产品 Top 10"
          rows={summary.attention_top10 || []}
          emptyText="当前筛选下暂无需关注样本。"
          onRowClick={onOpenBenchmark}
          columns={[
            ...commonColumns,
            { key: 'attention_score', label: '关注分', render: (row) => num(row.attention_score, 3) },
            { key: 'attention_reason_tags', label: '异常原因', render: (row) => (row.attention_reason_tags || []).join(' / ') },
            { key: 'scale_wow_bn', label: '本周变化', render: (row) => `${num(row.scale_wow_bn)} 亿` }
          ]}
        />
        <FocusTable
          title="基准未达标产品"
          rows={summary.benchmark_failed_products || []}
          emptyText="当前筛选下暂无低于基准下限样本。"
          onRowClick={onOpenBenchmark}
          columns={[
            ...commonColumns,
            { key: 'since_inception_annual_return', label: '成立以来年化', render: (row) => pct(row.since_inception_annual_return) },
            { key: 'benchmark_lower', label: '基准下限', render: (row) => pct(row.benchmark_lower) }
          ]}
        />
        <FocusTable
          title="规模下降 Top 10"
          rows={scaleDownRows}
          emptyText="当前筛选下暂无规模下降样本。"
          onRowClick={onOpenBenchmark}
          columns={[
            ...commonColumns,
            { key: 'product_scale_bn', label: '最新规模', render: (row) => `${num(row.product_scale_bn)} 亿` },
            { key: 'scale_wow_bn', label: '较上周', render: (row) => `${num(row.scale_wow_bn)} 亿` }
          ]}
        />
        <FocusTable
          title="近3个月收益分位下降产品"
          rows={summary.percentile_decline_products || []}
          emptyText="暂无低分位样本。"
          onRowClick={onOpenBenchmark}
          columns={[
            ...commonColumns,
            { key: 'return_3m', label: '3M 收益', render: (row) => pct(row.return_3m) },
            { key: 'return_percentile', label: '收益分位', render: (row) => pct(row.return_percentile, 0) }
          ]}
        />
      </section>

      <MarketBlock market={summary.market_issuance} />

      <section className="split-grid">
        <AiCalibrationCard analysis={analysis} />
        <DataSourceFreshness freshness={freshness} />
      </section>
    </div>
  );
}
