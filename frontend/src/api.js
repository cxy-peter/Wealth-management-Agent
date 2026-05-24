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
