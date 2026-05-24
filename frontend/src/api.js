const API_BASE = import.meta.env.VITE_WEALTH_AGENT_API_BASE || 'http://127.0.0.1:8000';

async function getJson(path) {
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

async function postJson(path, payload = {}) {
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
    const summary = await getDemoJson('weekly_summary.json');
    return { dates: [summary.report_date], latest: summary.report_date };
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
    return getDemoJson('weekly_summary.json');
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
    return getDemoJson('weekly_products.json');
  }
}

export async function getWeeklyProduct(productCode, reportDate) {
  const suffix = reportDate ? `?report_date=${encodeURIComponent(reportDate)}` : '';
  try {
    return await getJson(`/api/weekly-report/products/${productCode}${suffix}`);
  } catch {
    const details = await getDemoJson('product_details.json');
    return details.by_product?.[productCode] || details.by_product?.[details.default_product_code];
  }
}

export function generateWeeklyReport(payload = {}) {
  return postJson('/api/weekly-report/generate', payload);
}

export function runPeerBenchmark(payload = {}) {
  return postJson('/api/benchmark/peer', payload).catch(async () => {
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
  const response = await fetch(`${API_BASE}/api/products/${productId}`);
  if (!response.ok) throw new Error(`product returned ${response.status}`);
  return response.json();
}

export async function getProductNav(productId) {
  const response = await fetch(`${API_BASE}/api/products/${productId}/nav`);
  if (!response.ok) throw new Error(`product nav returned ${response.status}`);
  return response.json();
}

export async function getProductRiskEvents(productId) {
  const response = await fetch(`${API_BASE}/api/products/${productId}/risk-events`);
  if (!response.ok) throw new Error(`risk events returned ${response.status}`);
  return response.json();
}

export async function getJobEvents(runId) {
  const response = await fetch(`${API_BASE}/api/analyze/jobs/${runId}/events`);
  if (!response.ok) throw new Error(`events returned ${response.status}`);
  return response.json();
}

export async function getDataFreshness() {
  try {
    return await getJson('/api/data/freshness');
  } catch {
    const summary = await getDemoJson('weekly_summary.json');
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
  const response = await fetch(`${API_BASE}/api/data/lineage/${encodeURIComponent(evidenceId)}`);
  if (!response.ok) throw new Error(`data lineage returned ${response.status}`);
  return response.json();
}

export async function getDpoEval() {
  return getDemoJson('dpo_eval.json');
}

export async function getReport(runId) {
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
