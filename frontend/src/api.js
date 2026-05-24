const API_BASE = (import.meta.env.VITE_WEALTH_AGENT_API_BASE || '').replace(/\/$/, '');

import { applySessionProducts, applySessionSummary } from './sessionDataStore.js';

async function getJson(path) {
  if (!API_BASE) {
    throw new Error('API base is not configured');
  }
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`API ${path} returned ${response.status}`);
  }
  return response.json();
}

async function getDemoJson(name) {
  const response = await fetch(`/demo-data/${name}`);
  if (!response.ok) {
    throw new Error(`demo data ${name} returned ${response.status}`);
  }
  return response.json();
}

function dateKey(date) {
  return String(date || '').slice(0, 10);
}

async function getDatedDemoJson(prefix, filters = {}, latest = '2025-04-04') {
  const datesPayload = await getDemoJson('weekly_dates.json').catch(() => ({ latest }));
  const selected = dateKey(filters.report_date || datesPayload.latest || latest);
  const fallback = dateKey(datesPayload.latest || latest);
  const candidates = [`${prefix}_${selected}.json`, `${prefix}_${fallback}.json`, `${prefix}.json`];
  for (const candidate of candidates) {
    try {
      return await getDemoJson(candidate);
    } catch {
      // Try the next static fallback.
    }
  }
  throw new Error(`No demo data found for ${prefix}`);
}

async function postJson(path, payload = {}) {
  if (!API_BASE) {
    throw new Error('API base is not configured');
  }
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(`API ${path} returned ${response.status}`);
  }
  return response.json();
}

export function runAnalyze(payload) {
  return postJson('/api/analyze', payload);
}

export function runProductBenchmark(payload = {}) {
  return postJson('/api/product-benchmark', payload);
}

export function runEvaluation(payload = {}) {
  return postJson('/api/eval/run', payload);
}

export async function getWeeklyReportDates() {
  try {
    return await getJson('/api/weekly-report/dates');
  } catch {
    return getDemoJson('weekly_dates.json');
  }
}

export async function getWeeklySummary(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const suffix = params.toString() ? `?${params.toString()}` : '';
  try {
    return await getJson(`/api/weekly-report/summary${suffix}`);
  } catch {
    const [summary, products] = await Promise.all([
      getDatedDemoJson('weekly_summary', filters),
      getWeeklyProducts(filters)
    ]);
    return applySessionSummary(summary, products);
  }
}

export async function getWeeklyProducts(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const suffix = params.toString() ? `?${params.toString()}` : '';
  try {
    return await getJson(`/api/weekly-report/products${suffix}`);
  } catch {
    const payload = await getDatedDemoJson('weekly_products', filters);
    return applySessionProducts(payload, filters);
  }
}

export async function getWeeklyProduct(productCode, reportDate) {
  const suffix = reportDate ? `?report_date=${encodeURIComponent(reportDate)}` : '';
  try {
    return await getJson(`/api/weekly-report/products/${productCode}${suffix}`);
  } catch {
    const selectedDate = dateKey(reportDate || '2025-04-04');
    try {
      return await getDemoJson(`product_detail_${productCode}_${selectedDate}.json`);
    } catch {
      // Use the compact legacy fallback.
    }
    const details = await getDemoJson('product_details.json');
    const detail = details.by_product?.[productCode] || details.by_product?.[details.default_product_code];
    return { ...detail, report_date: dateKey(reportDate || detail?.report_date || '2025-04-04') };
  }
}

export function generateWeeklyReport(payload = {}) {
  return postJson('/api/weekly-report/generate', payload);
}

export function runPeerBenchmark(payload = {}) {
  return postJson('/api/benchmark/peer', payload).catch(async () => {
    const selectedDate = dateKey(payload.report_date || '2025-04-04');
    if (payload.product_code) {
      try {
        return await getDemoJson(`peer_summary_${payload.product_code}_${selectedDate}.json`);
      } catch {
        // Use the compact legacy fallback.
      }
    }
    const peers = await getDemoJson('peer_benchmark.json');
    return peers.by_product?.[payload.product_code] || peers.by_product?.[peers.default_product_code];
  });
}

export function runChannelBenchmark(payload = {}) {
  return postJson('/api/benchmark/channel', payload).catch(() => getDemoJson('channel_benchmark.json'));
}

export function runTopPeers(payload = {}) {
  return postJson('/api/benchmark/top-peers', payload).catch(() => getDemoJson('top_peers.json'));
}

export async function getProducts(filters = {}) {
  if (!API_BASE) {
    throw new Error('API base is not configured');
  }
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE}/api/products${suffix}`);
  if (!response.ok) throw new Error(`products returned ${response.status}`);
  return response.json();
}

export async function getProduct(productId) {
  if (!API_BASE) {
    throw new Error('API base is not configured');
  }
  const response = await fetch(`${API_BASE}/api/products/${productId}`);
  if (!response.ok) throw new Error(`product returned ${response.status}`);
  return response.json();
}

export async function getProductNav(productId) {
  if (!API_BASE) {
    throw new Error('API base is not configured');
  }
  const response = await fetch(`${API_BASE}/api/products/${productId}/nav`);
  if (!response.ok) throw new Error(`product nav returned ${response.status}`);
  return response.json();
}

export async function getProductRiskEvents(productId) {
  if (!API_BASE) {
    throw new Error('API base is not configured');
  }
  const response = await fetch(`${API_BASE}/api/products/${productId}/risk-events`);
  if (!response.ok) throw new Error(`risk events returned ${response.status}`);
  return response.json();
}

export async function getJobEvents(runId) {
  if (!API_BASE) {
    throw new Error('API base is not configured');
  }
  const response = await fetch(`${API_BASE}/api/analyze/jobs/${runId}/events`);
  if (!response.ok) throw new Error(`events returned ${response.status}`);
  return response.json();
}

export async function getDataFreshness() {
  try {
    return await getJson('/api/data/freshness');
  } catch {
    const summary = await getDatedDemoJson('weekly_summary', {});
    return {
      data_mode: 'static demo sample',
      sources: [
        {
          source_type: 'synthetic_weekly_snapshot',
          source_name: 'Vercel static demo data',
          record_count: summary.product_count || 0,
          latest_as_of_date: summary.report_date,
          staleness_days: 0,
          confidence_level: 'medium',
          adapter_status: 'available',
          missing_fields: []
        }
      ]
    };
  }
}

export async function getDataLineage(evidenceId) {
  if (!API_BASE) {
    throw new Error('API base is not configured');
  }
  const response = await fetch(`${API_BASE}/api/data/lineage/${encodeURIComponent(evidenceId)}`);
  if (!response.ok) throw new Error(`data lineage returned ${response.status}`);
  return response.json();
}

export async function getDpoEval() {
  return getDemoJson('dpo_eval.json');
}

export async function getReport(runId) {
  if (!API_BASE) {
    throw new Error('API base is not configured');
  }
  const response = await fetch(`${API_BASE}/api/reports/${runId}`);
  if (!response.ok) throw new Error(`report returned ${response.status}`);
  return response.json();
}

export function approveReview(runId, payload = {}) {
  return postJson(`/api/reviews/${runId}/approve`, payload);
}

export function editReview(runId, payload = {}) {
  return postJson(`/api/reviews/${runId}/edit`, payload);
}

export function rejectReview(runId, payload = {}) {
  return postJson(`/api/reviews/${runId}/reject`, payload);
}
