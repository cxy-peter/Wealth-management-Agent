const API_BASE = import.meta.env.VITE_WEALTH_AGENT_API_BASE || 'http://127.0.0.1:8000';

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
  const response = await fetch(`${API_BASE}/api/weekly-report/dates`);
  if (!response.ok) throw new Error(`weekly dates returned ${response.status}`);
  return response.json();
}

export async function getWeeklySummary(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE}/api/weekly-report/summary${suffix}`);
  if (!response.ok) throw new Error(`weekly summary returned ${response.status}`);
  return response.json();
}

export async function getWeeklyProducts(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const suffix = params.toString() ? `?${params.toString()}` : '';
  const response = await fetch(`${API_BASE}/api/weekly-report/products${suffix}`);
  if (!response.ok) throw new Error(`weekly products returned ${response.status}`);
  return response.json();
}

export async function getWeeklyProduct(productCode, reportDate) {
  const suffix = reportDate ? `?report_date=${encodeURIComponent(reportDate)}` : '';
  const response = await fetch(`${API_BASE}/api/weekly-report/products/${productCode}${suffix}`);
  if (!response.ok) throw new Error(`weekly product returned ${response.status}`);
  return response.json();
}

export function generateWeeklyReport(payload = {}) {
  return postJson('/api/weekly-report/generate', payload);
}

export function runPeerBenchmark(payload = {}) {
  return postJson('/api/benchmark/peer', payload);
}

export function runChannelBenchmark(payload = {}) {
  return postJson('/api/benchmark/channel', payload);
}

export function runTopPeers(payload = {}) {
  return postJson('/api/benchmark/top-peers', payload);
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
