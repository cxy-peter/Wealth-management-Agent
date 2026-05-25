const STORE_KEY = 'wealth_agent_session_uploads_v2';

export const DATASET_SCOPES = {
  own_company: {
    label: '自家公司产品数据',
    schemas: ['product_weekly_snapshot', 'product_nav_weekly', 'product_scale_history', 'product_benchmark_status']
  },
  full_market: {
    label: '全市场/同业产品数据',
    schemas: ['peer_product_universe', 'peer_product_metrics', 'channel_peer_universe', 'top_peer_products']
  },
  reference_rates: {
    label: '基准利率数据',
    schemas: ['reference_rates']
  }
};

const REQUIRED_FIELDS = {
  product_weekly_snapshot: ['product_code', 'product_name', 'report_date'],
  product_nav_weekly: ['product_code', 'nav_date', 'nav'],
  product_scale_history: ['product_code', 'report_date', 'product_scale_bn'],
  product_benchmark_status: ['product_code', 'report_date', 'benchmark_status'],
  peer_product_universe: ['peer_product_code', 'peer_product_name', 'product_type'],
  peer_product_metrics: ['peer_product_code', 'report_date', 'return_3m'],
  channel_peer_universe: ['channel'],
  top_peer_products: ['peer_product_code', 'peer_product_name', 'return_3m'],
  market_issuance_weekly: ['report_date'],
  reference_rates: ['rate_id', 'as_of_date', 'tenor_days', 'annual_yield']
};

function safeJsonParse(value, fallback) {
  try {
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

export function readSessionStore() {
  return safeJsonParse(window.localStorage.getItem(STORE_KEY), { uploads: [], records: {} });
}

export function writeSessionStore(nextStore) {
  window.localStorage.setItem(STORE_KEY, JSON.stringify(nextStore));
  window.dispatchEvent(new CustomEvent('wealth-agent-session-data-updated', { detail: nextStore }));
}

export function normalizeDate(value) {
  if (!value) return '';
  if (typeof value === 'number' && Number.isFinite(value) && value > 20000) {
    const base = new Date(Date.UTC(1899, 11, 30));
    base.setUTCDate(base.getUTCDate() + Math.round(value));
    return base.toISOString().slice(0, 10);
  }
  const text = String(value).trim();
  const normalized = text.replace(/\//g, '-').replace(/\./g, '-');
  const match = normalized.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (!match) return text;
  return `${match[1]}-${match[2].padStart(2, '0')}-${match[3].padStart(2, '0')}`;
}

export function normalizeNumber(value) {
  if (value === null || value === undefined || value === '') return null;
  if (typeof value === 'number') return Number.isFinite(value) ? value : null;
  const raw = String(value).trim();
  if (!raw || raw === '-' || raw === '--') return null;
  const isPercent = raw.includes('%');
  const isBp = /\bbp\b|BP|基点/.test(raw);
  const cleaned = raw.replace(/[,，]/g, '').replace(/%|亿元|亿|bp|BP|基点/g, '');
  const number = Number(cleaned);
  if (!Number.isFinite(number)) return null;
  if (isBp) return number / 10000;
  if (isPercent) return number / 100;
  return number;
}

function loweredColumns(columns = []) {
  return columns.map((column) => String(column).trim().toLowerCase());
}

export function inferSchema(columns = [], datasetScope = '') {
  const normalized = loweredColumns(columns);
  const has = (needles) => needles.some((needle) => normalized.some((column) => column.includes(String(needle).toLowerCase())));
  if (datasetScope === 'reference_rates' || has(['rate_id', 'annual_yield', 'tenor_days', '利率代码', '年化利率'])) return 'reference_rates';
  if (datasetScope === 'full_market' && has(['rank', '排名', 'tracking_reason'])) return 'top_peer_products';
  if (datasetScope === 'full_market' && has(['peer_product_code', '同业产品代码']) && !has(['return_3m', '近3月'])) return 'peer_product_universe';
  if (has(['nav_date', '净值日期']) || (has(['nav', '单位净值']) && !has(['latest_nav', '最新净值']))) return 'product_nav_weekly';
  if (has(['peer_product_code', '同业产品代码', '竞品代码'])) return 'peer_product_metrics';
  if (has(['market', 'new_product', '新发'])) return 'market_issuance_weekly';
  if (has(['channel', '渠道']) && has(['peer', '同业']) && !has(['product_scale'])) return 'channel_peer_universe';
  return 'product_weekly_snapshot';
}

export function allowedSchemasForScope(datasetScope) {
  return DATASET_SCOPES[datasetScope]?.schemas || [];
}

export function autoMapColumns(columns = []) {
  const dictionary = [
    ['product_name', ['product_name', '产品名称', '产品名', '名称']],
    ['product_code', ['product_code', '产品代码', '产品编号', '登记编码']],
    ['peer_product_code', ['peer_product_code', '竞品代码', '同业产品代码']],
    ['peer_product_name', ['peer_product_name', '竞品名称', '同业产品名称']],
    ['issuer_name', ['issuer_name', '发行机构', '管理人', 'issuer']],
    ['report_date', ['report_date', '周报日期', '报告日期', '日期']],
    ['nav_date', ['nav_date', '净值日期']],
    ['channel', ['channel', '渠道']],
    ['risk_level', ['risk_level', '风险等级']],
    ['product_type', ['product_type', '产品类型', '投资性质']],
    ['product_series', ['product_series', '产品系列', '系列']],
    ['open_type', ['open_type', '期限', '开放类型', '持有期']],
    ['holding_period_days', ['holding_period_days', '期限天数', '持有期天数']],
    ['product_scale_bn', ['product_scale_bn', '产品规模', '规模']],
    ['scale_wow_bn', ['scale_wow_bn', '较上周', '周变化']],
    ['scale_mom_bn', ['scale_mom_bn', '较上月', '月变化']],
    ['latest_nav', ['latest_nav', '最新净值']],
    ['nav', ['nav', '单位净值', '净值']],
    ['benchmark_nav', ['benchmark_nav', '基准净值']],
    ['return_1m', ['return_1m', '近1月', '近一月']],
    ['return_3m', ['return_3m', '近3月', '近三月']],
    ['return_6m', ['return_6m', '近6月', '近六月']],
    ['return_1y', ['return_1y', '近1年', '近一年']],
    ['max_drawdown', ['max_drawdown', '最大回撤']],
    ['volatility', ['volatility', '波动率']],
    ['sharpe', ['sharpe', '夏普']],
    ['benchmark_lower', ['benchmark_lower', '基准下限']],
    ['benchmark_upper', ['benchmark_upper', '基准上限']],
    ['benchmark_status', ['benchmark_status', '达标状态', '基准状态']],
    ['rank', ['rank', '排名']],
    ['tracking_reason', ['tracking_reason', '入选原因', '跟踪原因']],
    ['rate_id', ['rate_id', '利率代码', '基准代码']],
    ['as_of_date', ['as_of_date', '基准日期', '日期']],
    ['currency', ['currency', '币种']],
    ['rate_type', ['rate_type', '利率类型', '基准类型']],
    ['tenor_days', ['tenor_days', '期限天数']],
    ['tenor_label', ['tenor_label', '期限']],
    ['annual_yield', ['annual_yield', '年化利率', '参考收益率', 'yield']]
  ];
  const mapping = {};
  for (const column of columns) {
    const source = String(column).trim();
    const lowered = source.toLowerCase();
    const match = dictionary.find(([, aliases]) =>
      aliases.some((alias) => lowered === alias.toLowerCase() || lowered.includes(alias.toLowerCase()))
    );
    if (match && !mapping[match[0]]) {
      mapping[match[0]] = source;
    }
  }
  return mapping;
}

export function normalizeRecords(rows, schema, mapping, uploadId, datasetScope = 'own_company', fileName = '') {
  const evidencePrefix = `ev_upload_${uploadId}`;
  return rows
    .filter((row) => Object.values(row || {}).some((value) => value !== null && value !== undefined && String(value).trim() !== ''))
    .map((row, index) => {
      const next = {};
      for (const [target, source] of Object.entries(mapping || {})) {
        next[target] = row[source];
      }
      for (const field of ['report_date', 'nav_date', 'as_of_date']) {
        if (next[field]) next[field] = normalizeDate(next[field]);
      }
      for (const field of [
        'product_scale_bn',
        'scale_wow_bn',
        'scale_mom_bn',
        'latest_nav',
        'nav',
        'benchmark_nav',
        'return_1m',
        'return_3m',
        'return_6m',
        'return_1y',
        'max_drawdown',
        'volatility',
        'sharpe',
        'benchmark_lower',
        'benchmark_upper',
        'holding_period_days',
        'rank',
        'tenor_days',
        'annual_yield'
      ]) {
        if (field in next) next[field] = normalizeNumber(next[field]);
      }
      const code = next.product_code || next.peer_product_code || next.rate_id || `UPLOAD_${String(index + 1).padStart(3, '0')}`;
      const asOfDate = next.report_date || next.nav_date || next.as_of_date || new Date().toISOString().slice(0, 10);
      return {
        ...next,
        upload_id: uploadId,
        dataset_scope: datasetScope,
        source_type: 'manual_upload',
        source_name: schema,
        source_url_or_file: fileName ? `browser_upload:${fileName}` : `browser_upload:${uploadId}`,
        fetched_at: new Date().toISOString(),
        as_of_date: asOfDate,
        staleness_days: 0,
        confidence_level: 'user_uploaded',
        evidence_id: `${evidencePrefix}_${code}_${index + 1}`,
        parser_version: 'frontend_upload_parser.v2'
      };
    });
}

export function qualityReport(rows, schema, mapping, datasetScope = '') {
  const required = REQUIRED_FIELDS[schema] || [];
  const scopeValid = Boolean(datasetScope && allowedSchemasForScope(datasetScope).includes(schema));
  const mappedFields = new Set(Object.keys(mapping || {}));
  const missingRequiredFields = required.filter((field) => !mappedFields.has(field));
  const normalizedRows = normalizeRecords(rows, schema, mapping, 'preview', datasetScope || 'own_company');
  const duplicateKeys = new Set();
  const seen = new Set();
  let badDateCount = 0;
  for (const row of normalizedRows) {
    const date = row.report_date || row.nav_date || row.as_of_date;
    if (date && !/^\d{4}-\d{2}-\d{2}$/.test(String(date))) badDateCount += 1;
    const key = `${row.product_code || row.peer_product_code || row.rate_id || ''}_${date || ''}`;
    if (seen.has(key)) duplicateKeys.add(key);
    seen.add(key);
  }
  const numericFields = ['product_scale_bn', 'latest_nav', 'nav', 'return_3m', 'max_drawdown', 'volatility', 'sharpe', 'annual_yield'];
  const missingRate = {};
  for (const field of numericFields) {
    if (!mappedFields.has(field)) continue;
    const missing = normalizedRows.filter((row) => row[field] === null || row[field] === undefined || row[field] === '').length;
    missingRate[field] = normalizedRows.length ? Number((missing / normalizedRows.length).toFixed(3)) : 0;
  }
  return {
    schema,
    dataset_scope: datasetScope,
    scope_valid: scopeValid,
    row_count: normalizedRows.length,
    missing_required_fields: missingRequiredFields,
    bad_date_count: badDateCount,
    duplicate_key_count: duplicateKeys.size,
    numeric_missing_rate: missingRate,
    parser_status: !scopeValid ? 'needs_scope_or_schema' : missingRequiredFields.length ? 'needs_mapping' : 'parsed'
  };
}

export function saveUpload({ fileName, schema, rows, mapping, datasetScope }) {
  if (!datasetScope || !DATASET_SCOPES[datasetScope]) {
    throw new Error('dataset_scope is required');
  }
  const uploadId = `upload_${Date.now().toString(36)}`;
  const normalized = normalizeRecords(rows, schema, mapping, uploadId, datasetScope, fileName);
  const report = qualityReport(rows, schema, mapping, datasetScope);
  const store = readSessionStore();
  const upload = {
    upload_id: uploadId,
    dataset_scope: datasetScope,
    source_type: 'manual_upload',
    file_name: fileName,
    schema,
    mapping,
    quality_report: report,
    created_at: new Date().toISOString(),
    row_count: normalized.length,
    parser_version: 'frontend_upload_parser.v2',
    as_of_date: normalized[0]?.as_of_date || new Date().toISOString().slice(0, 10),
    evidence_id: normalized[0]?.evidence_id || `ev_upload_${uploadId}`
  };
  store.uploads = [upload, ...(store.uploads || [])].slice(0, 20);
  store.records = store.records || {};
  store.records[schema] = [...normalized, ...(store.records[schema] || [])].slice(0, 8000);
  writeSessionStore(store);
  return { upload, records: normalized };
}

export function applySessionProducts(payload, filters = {}) {
  const store = readSessionStore();
  const uploaded = (store.records?.product_weekly_snapshot || []).filter((row) => (row.dataset_scope || 'own_company') === 'own_company');
  if (!uploaded.length) return payload;
  const reportDate = filters.report_date || payload.report_date;
  const rows = uploaded.filter((row) => !reportDate || row.report_date === reportDate);
  if (!rows.length) return payload;
  const byCode = new Map((payload.products || []).map((row) => [row.product_code, row]));
  for (const row of rows) {
    byCode.set(row.product_code, {
      ...byCode.get(row.product_code),
      ...row,
      risk_level: row.risk_level || byCode.get(row.product_code)?.risk_level || 'R2',
      benchmark_status: row.benchmark_status || byCode.get(row.product_code)?.benchmark_status || 'uploaded'
    });
  }
  const products = Array.from(byCode.values());
  return {
    ...payload,
    products,
    count: products.length,
    source_type: 'manual_upload_overlay'
  };
}

export function applySessionSummary(summary, productsPayload) {
  const products = productsPayload?.products || [];
  if (!products.length || productsPayload.source_type !== 'manual_upload_overlay') return summary;
  const totalScale = products.reduce((sum, row) => sum + Number(row.product_scale_bn || 0), 0);
  const scaleWow = products.reduce((sum, row) => sum + Number(row.scale_wow_bn || 0), 0);
  const benchmarkPass = products.filter((row) => row.benchmark_status === 'in_range' || row.benchmark_status === 'above_upper').length;
  const attention = products
    .filter((row) => Number(row.return_percentile ?? 1) <= 0.3 || Number(row.scale_wow_bn || 0) < -0.2 || row.benchmark_status === 'below_lower')
    .slice(0, 10);
  return {
    ...summary,
    product_count: products.length,
    kpis: {
      ...summary.kpis,
      total_scale_bn: Number(totalScale.toFixed(4)),
      scale_wow_bn: Number(scaleWow.toFixed(4)),
      benchmark_pass_rate: products.length ? benchmarkPass / products.length : 0,
      attention_product_count: attention.length
    },
    attention_top10: attention.length ? attention : summary.attention_top10,
    source_type: 'manual_upload_overlay'
  };
}

export function sessionNavRecords(productCodes = []) {
  const store = readSessionStore();
  const rows = (store.records?.product_nav_weekly || []).filter((row) => (row.dataset_scope || 'own_company') === 'own_company');
  const codeSet = new Set(productCodes);
  return rows.filter((row) => !codeSet.size || codeSet.has(row.product_code));
}

export function sessionPeerRecords() {
  const store = readSessionStore();
  return {
    universe: (store.records?.peer_product_universe || []).filter((row) => row.dataset_scope === 'full_market'),
    metrics: (store.records?.peer_product_metrics || []).filter((row) => row.dataset_scope === 'full_market'),
    channel: (store.records?.channel_peer_universe || []).filter((row) => row.dataset_scope === 'full_market'),
    top: (store.records?.top_peer_products || []).filter((row) => row.dataset_scope === 'full_market')
  };
}

export function applySessionPeerBenchmark(peerPayload, productCode = '') {
  const { metrics, universe } = sessionPeerRecords();
  if (!metrics.length) return peerPayload;
  const universeByCode = new Map(universe.map((row) => [row.peer_product_code, row]));
  const productType = peerPayload?.product?.product_type;
  const rows = metrics
    .map((row) => ({ ...universeByCode.get(row.peer_product_code), ...row }))
    .filter((row) => !productType || !row.product_type || row.product_type === productType)
    .sort((a, b) => Number(b.return_3m || 0) - Number(a.return_3m || 0))
    .slice(0, 24);
  if (!rows.length) return peerPayload;
  return {
    ...peerPayload,
    product_code: productCode || peerPayload?.product_code,
    peer_count: rows.length,
    table: rows,
    source_type: 'manual_upload_overlay',
    evidence_ids: [...new Set([...(peerPayload?.evidence_ids || []), ...rows.map((row) => row.evidence_id).filter(Boolean)])]
  };
}

export function applySessionTopPeers(payload) {
  const rows = sessionPeerRecords().top;
  if (!rows.length) return payload;
  const sorted = [...rows].sort((a, b) =>
    Number(b.return_3m || 0) - Number(a.return_3m || 0) ||
    Number(b.sharpe || 0) - Number(a.sharpe || 0) ||
    Number(a.max_drawdown || 0) - Number(b.max_drawdown || 0) ||
    Number(b.product_scale_bn || 0) - Number(a.product_scale_bn || 0) ||
    String(a.peer_product_code || '').localeCompare(String(b.peer_product_code || ''))
  );
  return {
    ...payload,
    source_type: 'manual_upload_overlay',
    count: sorted.length,
    table: sorted.map((row, index) => ({ ...row, global_rank: index + 1 }))
  };
}

export function sessionReferenceRates() {
  const store = readSessionStore();
  return (store.records?.reference_rates || []).filter((row) => row.dataset_scope === 'reference_rates');
}
