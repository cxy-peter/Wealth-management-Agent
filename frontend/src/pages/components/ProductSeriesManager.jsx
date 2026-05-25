import { useMemo, useState } from 'react';

function classifySeries(product) {
  const text = `${product.product_name || ''} ${product.product_type || ''} ${product.open_type || ''} ${product.channel || ''}`;
  const rules = [
    ['cash', '现金优选', ['现金', '现金管理', '日开']],
    ['stable_income', '稳健添利', ['稳健', '添利', '纯固收']],
    ['enhanced_income', '持有期增强', ['增强', '固收增强', '持有期']],
    ['balanced', '多元配置', ['多元', '配置', '多资产', '混合']],
    ['global', '全球配置', ['全球', 'QDII', '海外']],
    ['closed', '封闭精选', ['封闭']],
    ['private_income', '悦享固收', ['悦享', '私银']]
  ];
  let best = null;
  let hits = [];
  for (const [id, name, keywords] of rules) {
    const nextHits = keywords.filter((keyword) => text.includes(keyword));
    if (nextHits.length > hits.length) {
      best = [id, name];
      hits = nextHits;
    }
  }
  if (!best) {
    const fallback = product.product_series || product.product_type || '未归类';
    return {
      ...product,
      suggested_series_id: fallback === '未归类' ? 'unclassified' : String(fallback).replace(/\s+/g, '_'),
      suggested_series_name: fallback,
      confidence: product.product_series ? 0.78 : 0.52,
      classify_reason: product.product_series ? 'existing_product_series' : 'fallback_to_product_type'
    };
  }
  return {
    ...product,
    suggested_series_id: best[0],
    suggested_series_name: best[1],
    confidence: Math.min(0.96, 0.62 + hits.length * 0.12),
    classify_reason: `keyword_match:${hits.join(',')}`,
    rule_version: 'frontend_series_rules.v1'
  };
}

function groupBySeries(rows) {
  const groups = new Map();
  for (const row of rows) {
    const id = row.suggested_series_id || 'unclassified';
    if (!groups.has(id)) groups.set(id, { series_id: id, series_name: row.suggested_series_name || id, products: [] });
    groups.get(id).products.push(row);
  }
  return Array.from(groups.values()).sort((a, b) => b.products.length - a.products.length);
}

export default function ProductSeriesManager({ products = [] }) {
  const [query, setQuery] = useState('');
  const [selectedSeriesId, setSelectedSeriesId] = useState('');
  const [manualLog, setManualLog] = useState([]);
  const classified = useMemo(() => products.map(classifySeries), [products]);
  const filtered = useMemo(
    () => classified.filter((row) => !query || `${row.product_code} ${row.product_name}`.toLowerCase().includes(query.toLowerCase())),
    [classified, query]
  );
  const groups = useMemo(() => groupBySeries(filtered), [filtered]);
  const selected = groups.find((item) => item.series_id === selectedSeriesId) || groups[0] || { products: [] };
  const lowConfidence = filtered.filter((row) => Number(row.confidence || 0) < 0.75 || row.suggested_series_id === 'unclassified');
  const uploadedProducts = filtered.filter((row) => row.source_type === 'manual_upload').slice(0, 8);

  function addManual(actionType, product) {
    const item = {
      override_id: `front_override_${Date.now().toString(36)}`,
      product_code: product?.product_code || selected.products[0]?.product_code || '-',
      product_name: product?.product_name || selected.products[0]?.product_name || '-',
      old_series_id: product?.suggested_series_id || selected.series_id,
      new_series_id: selected.series_id,
      action_type: actionType,
      reason: 'frontend demo manual correction',
      evidence_id: `ev_front_series_override_${Date.now().toString(36)}`
    };
    setManualLog((current) => [item, ...current].slice(0, 8));
  }

  return (
    <section className="panel series-manager">
      <div className="section-title">
        <span>产品系列归类与手工修正</span>
        <strong>{groups.length} 个系列</strong>
      </div>
      <div className="series-toolbar">
        <label className="field-group">
          <span>搜索产品</span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="产品代码 / 产品名称" />
        </label>
        <button className="primary-btn secondary" onClick={() => addManual('rename')}>修改系列名称</button>
        <button className="primary-btn secondary" onClick={() => addManual('merge')}>合并系列</button>
        <button className="primary-btn secondary" onClick={() => addManual('split')}>拆分系列</button>
        <button className="primary-btn" onClick={() => addManual('recompute')}>重算系列业绩</button>
      </div>
      {uploadedProducts.length ? (
        <div className="uploaded-series-strip">
          {uploadedProducts.map((row) => (
            <button key={row.product_code} onClick={() => setSelectedSeriesId(row.suggested_series_id)}>
              <strong className="series-product-name">{row.product_name}</strong>
              <span>{row.product_code} · {row.suggested_series_name} · confidence {Number(row.confidence || 0).toFixed(2)}</span>
            </button>
          ))}
        </div>
      ) : null}
      <div className="series-layout">
        <div className="panel inner-panel">
          <div className="section-title"><span>未归类 / 低置信度</span><strong>{lowConfidence.length}</strong></div>
          <div className="series-product-list">
            {lowConfidence.slice(0, 10).map((row) => (
              <button key={row.product_code} onClick={() => addManual('add', row)}>
                <strong className="series-product-name">{row.product_name}</strong>
                <span>{row.product_code} · confidence {Number(row.confidence || 0).toFixed(2)}</span>
              </button>
            ))}
          </div>
        </div>
        <div className="panel inner-panel">
          <div className="section-title"><span>自动识别产品系列</span><strong>{filtered.length} 只产品</strong></div>
          <div className="series-chip-grid">
            {groups.map((group) => (
              <button key={group.series_id} className={group.series_id === selected.series_id ? 'active' : ''} onClick={() => setSelectedSeriesId(group.series_id)}>
                <strong>{group.series_name}</strong>
                <span>{group.products.length} 只</span>
              </button>
            ))}
          </div>
        </div>
        <div className="panel inner-panel">
          <div className="section-title"><span>当前系列详情</span><strong>{selected.series_name || '未选择'}</strong></div>
          <div className="series-product-list">
            {selected.products.slice(0, 8).map((row) => (
              <button key={row.product_code} onClick={() => addManual('move', row)}>
                <strong className="series-product-name">{row.product_name}</strong>
                <span>{row.product_code} · {row.classify_reason}</span>
              </button>
            ))}
          </div>
          <div className="manual-log">
            {manualLog.map((item) => (
              <div key={item.override_id}>
                <strong>{item.action_type}</strong>
                <span>{item.product_code} · {item.evidence_id}</span>
              </div>
            ))}
            {!manualLog.length ? <p className="panel-copy">暂无手工调整记录。</p> : null}
          </div>
        </div>
      </div>
    </section>
  );
}
