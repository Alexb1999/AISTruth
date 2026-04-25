"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";

import type { ValidateResponse } from "./types";

const TrackMap = dynamic(() => import("./_components/TrackMap"), { ssr: false });

export default function Home() {
  const apiBase = useMemo(() => process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000", []);
  const [mmsi, setMmsi] = useState("259139000");
  const [timeFrom, setTimeFrom] = useState("");
  const [timeTo, setTimeTo] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [fusion, setFusion] = useState(false);
  const [showRaw, setShowRaw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ValidateResponse | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setApiKey(localStorage.getItem("aistruth_api_key") ?? "");
  }, []);

  useEffect(() => {
    if (apiKey) {
      localStorage.setItem("aistruth_api_key", apiKey);
    } else {
      localStorage.removeItem("aistruth_api_key");
    }
  }, [apiKey]);

  async function run() {
    if (!/^\d{7,9}$/.test(mmsi.trim())) {
      setError("MMSI must be 7-9 digits.");
      return;
    }
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const params = new URLSearchParams();
      if (timeFrom) params.set("from", new Date(timeFrom).toISOString());
      if (timeTo) params.set("to", new Date(timeTo).toISOString());
      if (fusion) params.set("fusion", "true");
      const query = params.toString() ? `?${params.toString()}` : "";
      const res = await fetch(`${apiBase}/v1/validate/${encodeURIComponent(mmsi.trim())}${query}`, {
        headers: apiKey ? { "X-AIS-Key": apiKey } : undefined,
        signal: controller.signal,
      });
      const text = await res.text();
      if (!res.ok) {
        throw new Error(`${res.status} ${text}`);
      }
      setData(JSON.parse(text) as ValidateResponse);
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const scoreTone =
    data && data.confidence_score >= 80
      ? "bg-emerald-500/15 text-emerald-200"
      : data && data.confidence_score >= 50
        ? "bg-amber-500/15 text-amber-200"
        : "bg-rose-500/15 text-rose-200";

  return (
    <main className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-8">
      <section className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl">
        <p className="text-sm uppercase tracking-[0.3em] text-cyan-300">AISTruth dev console</p>
        <div className="mt-3 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-4xl font-semibold tracking-tight">Maritime integrity validation</h1>
            <p className="mt-2 max-w-3xl text-slate-300">
              Calls <code>GET /v1/validate/&lt;mmsi&gt;</code> on <code>{apiBase}</code>. Add an API
              key when `AISTRUTH_API_KEYS` is enabled on the FastAPI service.
            </p>
          </div>
          {data ? (
            <div className={`rounded-2xl px-5 py-4 text-center ${scoreTone}`}>
              <div className="text-sm">Confidence</div>
              <div className="text-4xl font-bold">{data.confidence_score}</div>
            </div>
          ) : null}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-[420px_1fr]">
        <div className="rounded-3xl border border-slate-800 bg-slate-900 p-5">
          <div className="grid gap-4">
            <label className="grid gap-1 text-sm text-slate-300">
              MMSI
              <input
                className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
                value={mmsi}
                onChange={(e) => setMmsi(e.target.value)}
                inputMode="numeric"
              />
            </label>
            <label className="grid gap-1 text-sm text-slate-300">
              From
              <input
                className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
                type="datetime-local"
                value={timeFrom}
                onChange={(e) => setTimeFrom(e.target.value)}
              />
            </label>
            <label className="grid gap-1 text-sm text-slate-300">
              To
              <input
                className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
                type="datetime-local"
                value={timeTo}
                onChange={(e) => setTimeTo(e.target.value)}
              />
            </label>
            <label className="grid gap-1 text-sm text-slate-300">
              API key
              <input
                className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="X-AIS-Key"
                type="password"
              />
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-300">
              <input
                checked={fusion}
                onChange={(e) => setFusion(e.target.checked)}
                type="checkbox"
              />
              Request RTK fusion evidence
            </label>
            <button
              className="rounded-xl bg-cyan-400 px-4 py-2 font-semibold text-slate-950 disabled:opacity-50"
              type="button"
              onClick={() => void run()}
              disabled={loading || !mmsi.trim()}
            >
              {loading ? "Validating..." : "Validate"}
            </button>
          </div>
          {error ? (
            <p className="mt-4 rounded-xl border border-rose-500/40 bg-rose-500/10 p-3 text-sm text-rose-200">
              <strong>Error:</strong> {error}
            </p>
          ) : null}
        </div>

        <div className="grid gap-6">
          <TrackMap data={data} />
          {data ? (
            <div className="grid gap-4 rounded-3xl border border-slate-800 bg-slate-900 p-5 md:grid-cols-3">
              <Metric label="Track points" value={String(data.evidence.track_points)} />
              <Metric label="Nearest node" value={data.evidence.nearest_node_id ?? "none"} />
              <Metric label="Time align" value={data.evidence.time_align_method} />
            </div>
          ) : null}
        </div>
      </section>

      {data ? (
        <section className="rounded-3xl border border-slate-800 bg-slate-900 p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-semibold">Evidence</h2>
            <button
              className="text-sm text-cyan-300"
              type="button"
              onClick={() => setShowRaw(!showRaw)}
            >
              {showRaw ? "Hide raw JSON" : "View raw JSON"}
            </button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {data.flags.length ? (
              data.flags.map((flag) => <Pill key={flag}>{flag}</Pill>)
            ) : (
              <Pill>no flags</Pill>
            )}
            {data.evidence.spoofing_findings.map((finding) => (
              <Pill
                key={`${finding.kind}-${finding.severity}`}
              >{`${finding.severity}: ${finding.kind}`}</Pill>
            ))}
          </div>
          {showRaw ? (
            <pre className="mt-4 max-h-[32rem] overflow-auto rounded-2xl bg-slate-950 p-4 text-sm text-slate-200">
              {JSON.stringify(data, null, 2)}
            </pre>
          ) : null}
        </section>
      ) : null}
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-sm text-slate-400">{label}</div>
      <div className="mt-1 truncate text-lg font-semibold text-slate-100">{value}</div>
    </div>
  );
}

function Pill({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full bg-slate-800 px-3 py-1 text-sm text-slate-200">{children}</span>
  );
}
