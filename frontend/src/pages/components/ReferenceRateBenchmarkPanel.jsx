import { useEffect, useMemo, useState } from 'react';

import { getReferenceRates } from '../../api.js';
import { sessionReferenceRates } from '../../sessionDataStore.js';

function pct(value, digits = 2) {
  return `${(Number(value || 0) * 100).toFixed(digits)}%`;
}

function closestRate(rates, tenorDays, rateType) {
  const candidates = rates.filter((row) => !rateType || row.rate_type === rateType);
  const rows = candidates.length ? candidates : rates;
  return [...rows].sort((a, b) => Math.abs(Number(a.tenor_days || 0) - tenorDays) - Math.abs(Number(b.tenor_days || 0) - tenorDays))[0];
}

export default function ReferenceRateBenchmarkPanel({ products = [] }) {
  const [rates, setRates] = useState([]);
  const [selectedCode, setSelectedCode] = useState(products[0]?.product_code || '');
  const uploadedRates = sessionReferenceRates();
  const selectedProduct = products.find((row) => row.product_code === selectedCode) || products[0] || {};

  useEffect(() => {
    getReferenceRates().then((payload) => setRates(payload.rates || [])).catch(() => setRates([]));
    const listener = () => setRates((current) => [...sessionReferenceRates(), ...current.filter((row) => row.source_type !== 'manual_upload')]);
    window.addEventListener('wealth-agent-session-data-updated', listener);
    return () => window.removeEventListener('wealth-agent-session-data-updated', listener);
  }, []);

  useEffect(() => {
    if (!selectedCode && products[0]?.product_code) setSelectedCode(products[0].product_code);
  }, [products, selectedCode]);

  const allRates = useMemo(() => {
    const ids = new Set();
    return [...uploadedRates, ...rates].filter((row) => {
      const key = `${row.rate_id}_${row.as_of_date}`;
      if (ids.has(key)) return false;
      ids.add(key);
      return true;
    });
  }, [uploadedRates, rates]);

  const comparisons = useMemo(() => {
    const tenor = Number(selectedProduct.holding_period_days || 90);
    const productAnnualized = Number(selectedProduct.return_3m || 0) * 4;
    return ['deposit', 'us_treasury', 'gov_bond', 'ncd'].map((type) => {
      const rate = closestRate(allRates, tenor, type);
      if (!rate) return null;
      return {
        ...rate,
        product_annualized_return: productAnnualized,
        product_minus_reference: productAnnualized - Number(rate.annual_yield || 0),
        benchmark_lower_minus_reference: Number(selectedProduct.benchmark_lower || 0) - Number(rate.annual_yield || 0),
        benchmark_upper_minus_reference: Number(selectedProduct.benchmark_upper || 0) - Number(rate.annual_yield || 0),
        benchmark_excess: productAnnualized - Number(selectedProduct.benchmark_lower || 0)
      };
    }).filter(Boolean);
  }, [allRates, selectedProduct]);

  return (
    <section className="panel">
      <div className="section-title">
        <span>基准利率对比</span>
        <strong>{uploadedRates.length ? 'manual_upload + synthetic_reference_rates' : 'synthetic_reference_rates'}</strong>
      </div>
      <label className="field-group reference-product-select">
        <span>选择产品</span>
        <select value={selectedProduct.product_code || ''} onChange={(event) => setSelectedCode(event.target.value)}>
          {products.slice(0, 80).map((row) => (
            <option key={row.product_code} value={row.product_code}>{row.product_code} · {row.product_name}</option>
          ))}
        </select>
      </label>
      <div className="table-panel compact-table embedded-table">
        <table>
          <thead><tr><th>参考利率</th><th>币种</th><th>期限</th><th>年化利率</th><th>产品收益-参考</th><th>基准下限-参考</th><th>基准上限-参考</th><th>benchmark excess</th><th>来源</th><th>证据编号</th></tr></thead>
          <tbody>
            {comparisons.map((row) => (
              <tr key={`${row.rate_id}-${row.as_of_date}`}>
                <td>{row.rate_id}</td><td>{row.currency}</td><td>{row.tenor_label}</td><td>{pct(row.annual_yield)}</td><td>{pct(row.product_minus_reference)}</td><td>{pct(row.benchmark_lower_minus_reference)}</td><td>{pct(row.benchmark_upper_minus_reference)}</td><td>{pct(row.benchmark_excess)}</td><td>{row.source_type}</td><td>{row.evidence_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="panel-copy">demo 利率仅标记为 synthetic_reference_rates 或 manual_upload；除非接入真实 adapter 并记录来源，否则不声称实时抓取官方利率。</p>
    </section>
  );
}
