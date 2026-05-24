const STORE_KEY = 'wealth_agent_session_uploads_v1';

const REQUIRED_FIELDS = {
  product_weekly_snapshot: ['product_code', 'product_name', 'report_date'],
  product_nav_weekly: ['product_code', 'nav_date', 'nav'],
  peer_product_metrics: ['peer_product_code', 'report_date', 'return_3m'],
  market_issuance_weekly: ['report_date'],
  channel_peer_universe: ['channel']
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
  const normalized = text.replace(/\//g, '-');
  const match = normalized.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (!match) return text;
  return `${match[1]}-${match[2].padStart(2, '0')}-${match[3].padStart(2, '0')}`;
}

export function normalizeNumber(value) {
  if (value === null || value === undefined || value === '') return null;
  if (typeof value === 'number') return Number.isFinite(value) ? value : null;
  const raw = String(value).trim();
  if (!raw) return null;
  const isPercent = raw.includes('%');
  const isBp = /\bbp\b|BP|基点/.test(raw);
  const cleaned = raw.replace(/[,，]/g, '').replace(/%|亿元|亿|bp|BP|基点/g, '');
  const number = Number(cleaned);
  if (!Number.isFinite(number)) return null;
  if (isBp) return number / 10000;
  if (isPercent) return number / 100;
  return number;
}

export function inferSchema(columns = []) {
  const normalized = columns.map((column) => String(column).toLowerCase());
  const has = (needles) => needles.some((needle) => normalized.some((column) => column.includes(needle)));
  if (has(['nav_date', '净值日期']) || (has(['nav']) && !has(['latest_nav']))) return 'product_nav_weekly';
  if (has(['peer_product_code', '同业产品'])) return 'peer_product_metrics';
  if (has(['market', 'new_product', '新发'])) return 'market_issuance_weekly';
  if (has(['channel']) && has(['peer']) && !has(['product_scale'])) return 'channel_peer_universe';
  return 'product_weekly_snapshot';
}

export function autoMapColumns(columns = []) {
  const dictionary = [
    ['product_name', ['product_name', '产品名称', '产品名', '名称']],
    ['product_code', ['product_code', '产品代码', '产品编号', '登记编码']],
    ['peer_product_code', ['peer_product_code', '竞品代码', '同业产品代码']],
    ['report_date', ['report_date', '周报日期', '报告日期', '日期']],
    ['nav_date', ['nav_date', '净值日期']],
    ['channel', ['channel', '渠道']],
    ['risk_level', ['risk_level', '风险等级']],
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
    ['benchmark_status', ['benchmark_status', '达标状态', '基准状态']]
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

export function normalizeRecords(rows, schema, mapping, uploadId) {
  const evidencePrefix = `ev_upload_${uploadId}`;
  return rows
    .filter((row) => Object.values(row || {}).some((value) => value !== null && value !== undefined && String(value).trim() !== ''))
    .map((row, index) => {
      const next = {};
      for (const [target, source] of Object.entries(mapping || {})) {
        next[target] = row[source];
      }
      for (const field of ['report_date', 'nav_date']) {
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
        'benchmark_upper'
      ]) {
        if (field in next) next[field] = normalizeNumber(next[field]);
      }
      const code = next.product_code || next.peer_product_code || `UPLOAD_${String(index + 1).padStart(3, '0')}`;
      const asOfDate = next.report_date || next.nav_date || new Date().toISOString().slice(0, 10);
      return {
        ...next,
        source_type: 'manual_upload',
        source_name: schema,
        source_url_or_file: `browser_upload:${uploadId}`,
        fetched_at: new Date().toISOString(),
        as_of_date: asOfDate,
        staleness_days: 0,
        confidence_level: 'user_uploaded',
        evidence_id: `${evidencePrefix}_${code}_${index + 1}`,
        parser_version: 'frontend_upload_parser.v1'
      };
    });
}

export function qualityReport(rows, schema, mapping) {
  const required = REQUIRED_FIELDS[schema] || [];
  const mappedFields = new Set(Object.keys(mapping || {}));
  const missingRequiredFields = required.filter((field) => !mappedFields.has(field));
  const normalizedRows = normalizeRecords(rows, schema, mapping, 'preview');
  const duplicateKeys = new Set();
  const seen = new Set();
  let badDateCount = 0;
  for (const row of normalizedRows) {
    const date = row.report_date || row.nav_date;
    if (date && !/^\d{4}-\d{2}-\d{2}$/.test(String(date))) badDateCount += 1;
    const key = `${row.product_code || row.peer_product_code || ''}_${date || ''}`;
    if (seen.has(key)) duplicateKeys.add(key);
    seen.add(key);
  }
  const numericFields = ['product_scale_bn', 'latest_nav', 'nav', 'return_3m', 'max_drawdown', 'volatility', 'sharpe'];
  const missingRate = {};
  for (const field of numericFields) {
    if (!mappedFields.has(field)) continue;
    const missing = normalizedRows.filter((row) => row[field] === null || row[field] === undefined || row[field] === '').length;
    missingRate[field] = normalizedRows.length ? Number((missing / normalizedRows.length).toFixed(3)) : 0;
  }
  return {
    schema,
    row_count: normalizedRows.length,
    missing_required_fields: missingRequiredFields,
    bad_date_count: badDateCount,
    duplicate_key_count: duplicateKeys.size,
    numeric_missing_rate: missingRate,
    parser_status: missingRequiredFields.length ? 'needs_mapping' : 'parsed'
  };
}

export function saveUpload({ fileName, schema, rows, mapping }) {
  const uploadId = `upload_${Date.now().toString(36)}`;
  const normalized = normalizeRecords(rows, schema, mapping, uploadId);
  const report = qualityReport(rows, schema, mapping);
  const store = readSessionStore();
  const upload = {
    upload_id: uploadId,
    file_name: fileName,
    schema,
    mapping,
    quality_report: report,
    created_at: new Date().toISOString(),
    row_count: normalized.length
  };
  store.uploads = [upload, ...(store.uploads || [])].slice(0, 20);
  store.records = store.records || {};
  store.records[schema] = [...normalized, ...(store.records[schema] || [])].slice(0, 5000);
  writeSessionStore(store);
  return { upload, records: normalized };
}

export function applySessionProducts(payload, filters = {}) {
  const store = readSessionStore();
  const uploaded = store.records?.product_weekly_snapshot || [];
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
  const rows = store.records?.product_nav_weekly || [];
  const codeSet = new Set(productCodes);
  return rows.filter((row) => !codeSet.size || codeSet.has(row.product_code));
}
