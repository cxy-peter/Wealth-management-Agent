import { Filter, Loader2, Search } from 'lucide-react';
import { useMemo, useState } from 'react';

import { runProductBenchmark } from '../api.js';

function pct(value) {
  return `${(Number(value || 0) * 100).toFixed(2)}%`;
}

export default function ProductBenchmark({ analysis, onAnalysis }) {
  const peer = analysis.peer_summary || { table: [] };
  const [riskLevel, setRiskLevel] = useState('');
  const [assetClass, setAssetClass] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('sample/mock product table');

  const assetClasses = useMemo(
    () => [...new Set((peer.table || []).map((item) => item.asset_class).filter(Boolean))],
    [peer.table]
  );
  const riskLevels = peer.risk_levels || [];

  async function handleBenchmark() {
    setLoading(true);
    try {
      const result = await runProductBenchmark({
        risk_level: riskLevel || undefined,
        asset_class: assetClass || undefined
      });
      onAnalysis({
        ...analysis,
        peer_summary: result
      });
      setStatus('backend api');
    } catch {
      setStatus('local fallback');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-stack">
      <section className="control-band">
        <div className="field-group">
          <label>资产类别</label>
          <select value={assetClass} onChange={(event) => setAssetClass(event.target.value)}>
            <option value="">全部</option>
            {assetClasses.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
        <div className="field-group">
          <label>风险等级</label>
          <select value={riskLevel} onChange={(event) => setRiskLevel(event.target.value)}>
            <option value="">全部</option>
            {riskLevels.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
        <button className="primary-btn" onClick={handleBenchmark} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <Filter size={18} />}
          更新对标
        </button>
      </section>

      <div className="inline-status">
        <Search size={16} />
        <span>{status}</span>
        <strong>{peer.methodology}</strong>
      </div>

      <section className="table-panel">
        <table>
          <thead>
            <tr>
              <th>产品</th>
              <th>资产类别</th>
              <th>渠道</th>
              <th>风险等级</th>
              <th>年化收益</th>
              <th>年化波动</th>
              <th>最大回撤</th>
              <th>Sharpe</th>
              <th>收益排名</th>
            </tr>
          </thead>
          <tbody>
            {(peer.table || []).map((item) => (
              <tr key={item.product_id}>
                <td>
                  <strong>{item.product_name}</strong>
                  <span>{item.product_id}</span>
                </td>
                <td>{item.asset_class}</td>
                <td>{item.channel}</td>
                <td>
                  <span className={`risk-chip ${item.risk_level}`}>{item.risk_level}</span>
                </td>
                <td>{pct(item.annualized_return)}</td>
                <td>{pct(item.annualized_volatility)}</td>
                <td>{pct(item.max_drawdown)}</td>
                <td>{Number(item.sharpe_ratio || 0).toFixed(3)}</td>
                <td>{item.return_rank}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
