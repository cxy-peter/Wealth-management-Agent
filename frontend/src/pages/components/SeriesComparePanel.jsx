import { useMemo, useState } from 'react';

function pct(value, digits = 1) {
  return `${(Number(value || 0) * 100).toFixed(digits)}%`;
}

function calcSeries(products) {
  const groups = new Map();
  for (const product of products) {
    const name = product.product_series || product.product_type || '未归类';
    if (!groups.has(name)) groups.set(name, []);
    groups.get(name).push(product);
  }
  return Array.from(groups.entries()).map(([seriesName, rows]) => {
    const totalScale = rows.reduce((sum, row) => sum + Number(row.product_scale_bn || 0), 0);
    const weighted = (field) => {
      if (!totalScale) return rows.reduce((sum, row) => sum + Number(row[field] || 0), 0) / Math.max(rows.length, 1);
      return rows.reduce((sum, row) => sum + Number(row[field] || 0) * Number(row.product_scale_bn || 0), 0) / totalScale;
    };
    const mean = (field) => rows.reduce((sum, row) => sum + Number(row[field] || 0), 0) / Math.max(rows.length, 1);
    const sortedReturns = rows.map((row) => Number(row.return_3m || 0)).sort((a, b) => a - b);
    const median = sortedReturns[Math.floor(sortedReturns.length / 2)] || 0;
    return {
      series_name: seriesName,
      product_count: rows.length,
      total_scale_bn: totalScale,
      scale_wow_bn: rows.reduce((sum, row) => sum + Number(row.scale_wow_bn || 0), 0),
      equal_weight_return_3m: mean('return_3m'),
      aum_weighted_return_3m: weighted('return_3m'),
      median_return_3m: median,
      max_drawdown_mean: mean('max_drawdown'),
      volatility_mean: mean('volatility'),
      sharpe_mean: mean('sharpe'),
      benchmark_pass_rate: rows.filter((row) => ['in_range', 'above_upper'].includes(row.benchmark_status)).length / Math.max(rows.length, 1),
      low_percentile_ratio: rows.filter((row) => Number(row.return_percentile ?? 1) <= 0.3).length / Math.max(rows.length, 1),
      attention_product_count: rows.filter((row) => row.benchmark_status === 'below_lower' || Number(row.return_percentile ?? 1) <= 0.3).length
    };
  }).sort((a, b) => b.total_scale_bn - a.total_scale_bn);
}

export default function SeriesComparePanel({ products = [] }) {
  const rows = useMemo(() => calcSeries(products), [products]);
  const [selected, setSelected] = useState([]);
  const visible = selected.length ? rows.filter((row) => selected.includes(row.series_name)) : rows.slice(0, 8);
  const maxScale = Math.max(...visible.map((row) => row.total_scale_bn), 1);
  const maxVol = Math.max(...visible.map((row) => row.volatility_mean), 0.01);
  const maxRet = Math.max(...visible.map((row) => row.aum_weighted_return_3m), 0.01);
  const minRet = Math.min(...visible.map((row) => row.aum_weighted_return_3m), -0.01);

  function toggle(seriesName) {
    setSelected((current) => current.includes(seriesName) ? current.filter((item) => item !== seriesName) : [...current, seriesName]);
  }

  return (
    <section className="panel">
      <div className="section-title">
        <span>系列业绩对比</span>
        <strong>DPO 校准解释：仅改写摘要，不负责算数</strong>
      </div>
      <div className="series-selector">
        {rows.slice(0, 10).map((row) => (
          <label key={row.series_name}>
            <input type="checkbox" checked={selected.includes(row.series_name)} onChange={() => toggle(row.series_name)} />
            <span>{row.series_name}</span>
          </label>
        ))}
      </div>
      <div className="split-grid">
        <div className="table-panel compact-table embedded-table">
          <table>
            <thead>
              <tr><th>系列</th><th>总规模</th><th>规模变化</th><th>等权收益</th><th>规模加权收益</th><th>收益中位数</th><th>最大回撤</th><th>波动率</th><th>Sharpe</th><th>达标率</th><th>低分位占比</th><th>关注数</th></tr>
            </thead>
            <tbody>
              {visible.map((row) => (
                <tr key={row.series_name}>
                  <td><strong>{row.series_name}</strong><span>{row.product_count} 只</span></td>
                  <td>{row.total_scale_bn.toFixed(2)} 亿</td>
                  <td>{row.scale_wow_bn.toFixed(2)} 亿</td>
                  <td>{pct(row.equal_weight_return_3m)}</td>
                  <td>{pct(row.aum_weighted_return_3m)}</td>
                  <td>{pct(row.median_return_3m)}</td>
                  <td>{pct(row.max_drawdown_mean)}</td>
                  <td>{pct(row.volatility_mean)}</td>
                  <td>{row.sharpe_mean.toFixed(2)}</td>
                  <td>{pct(row.benchmark_pass_rate, 0)}</td>
                  <td>{pct(row.low_percentile_ratio, 0)}</td>
                  <td>{row.attention_product_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel scatter-plot mini-series-scatter">
          {visible.map((row) => (
            <span
              key={row.series_name}
              className="series-dot"
              title={`${row.series_name}: ${pct(row.aum_weighted_return_3m)} / ${pct(row.volatility_mean)}`}
              style={{
                left: `${Math.min(94, Math.max(4, (row.volatility_mean / maxVol) * 90))}%`,
                top: `${94 - ((row.aum_weighted_return_3m - minRet) / Math.max(maxRet - minRet, 0.001)) * 88}%`,
                width: `${Math.max(12, Math.min(30, (row.total_scale_bn / maxScale) * 30))}px`,
                height: `${Math.max(12, Math.min(30, (row.total_scale_bn / maxScale) * 30))}px`
              }}
            />
          ))}
          <span className="axis x-axis">波动率</span><span className="axis y-axis">3M规模加权收益</span>
        </div>
      </div>
      <p className="panel-copy">系列周报摘要：{visible.slice(0, 3).map((row) => `${row.series_name} 规模 ${row.total_scale_bn.toFixed(1)} 亿，近3月规模加权收益 ${pct(row.aum_weighted_return_3m)}，关注产品 ${row.attention_product_count} 只`).join('；')}。</p>
    </section>
  );
}

