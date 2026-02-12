const API_BASE = "/api";

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function runQuery(query, apiToken) {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, api_token: apiToken })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Query failed");
  return data;
}
