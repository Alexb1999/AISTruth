"use client";

import { useMemo, useState } from "react";

export default function Home() {
  const apiBase = useMemo(() => process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000", []);
  const [mmsi, setMmsi] = useState("259139000");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<unknown>(null);

  async function run() {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const res = await fetch(`${apiBase}/v1/validate/${encodeURIComponent(mmsi.trim())}`);
      const text = await res.text();
      if (!res.ok) {
        throw new Error(`${res.status} ${text}`);
      }
      setData(JSON.parse(text) as unknown);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>AISTruth (dev)</h1>
      <p>
        Calls <code>GET /v1/validate/&lt;mmsi&gt;</code> on the FastAPI service. Set{" "}
        <code>BARENTSWATCH_CLIENT_ID</code> / <code>BARENTSWATCH_CLIENT_SECRET</code> on the API process.
      </p>
      <p>
        API base: <code>{apiBase}</code> (override with <code>NEXT_PUBLIC_API_URL</code>).
      </p>

      <div className="controls">
        <label>
          MMSI{" "}
          <input value={mmsi} onChange={(e) => setMmsi(e.target.value)} inputMode="numeric" />
        </label>
        <button type="button" onClick={() => void run()} disabled={loading || !mmsi.trim()}>
          {loading ? "Loading…" : "Validate"}
        </button>
      </div>

      {error ? (
        <p className="error">
          <strong>Error:</strong> {error}
        </p>
      ) : null}

      {data ? <pre>{JSON.stringify(data, null, 2)}</pre> : null}
    </main>
  );
}
