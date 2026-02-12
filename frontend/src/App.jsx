import { useEffect, useState } from "react";
import { healthCheck, runQuery } from "./api";

export default function App() {
  const [apiToken, setApiToken] = useState("");
  const [connected, setConnected] = useState(false);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    healthCheck()
      .then((res) => setConnected(res.monday_connected))
      .catch(() => setConnected(false));
  }, []);

  const submitQuery = async (q) => {
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const data = await runQuery(q, apiToken);
      setResponse(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Monday.com BI Agent</h1>
      <p>Status: {connected ? "Connected" : "Not Connected"}</p>

      <input
        type="password"
        placeholder="Monday API Token"
        value={apiToken}
        onChange={(e) => setApiToken(e.target.value)}
      />

      <textarea
        placeholder="Ask a business question"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      <button onClick={() => submitQuery(query)} disabled={!query || loading}>
        {loading ? "Analyzing..." : "Run Query"}
      </button>

      {error && <pre>{error}</pre>}
      {response && <pre>{JSON.stringify(response, null, 2)}</pre>}
    </div>
  );
}
