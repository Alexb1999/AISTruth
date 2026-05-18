"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import FusionEvidencePanel from "@/components/FusionEvidencePanel";
import IntegrityScoreCard from "@/components/IntegrityScoreCard";
import MetricCard from "@/components/MetricCard";
import NtripProbePanel from "@/components/NtripProbePanel";
import SectionHeader from "@/components/SectionHeader";
import ValidationOutcomeCard from "@/components/ValidationOutcomeCard";
import type { NorwayVesselSnippet, ValidateResponse } from "@/lib/types";
import { btnGhost, btnPrimary, btnSecondary, detailsSummary, input, labelText, panel, panelInset } from "@/lib/ui";

const TrackMap = dynamic(() => import("@/components/TrackMap"), { ssr: false });

function formatHttpError(status: number, body: string): string {
  let detail = body.trim() || "(empty body)";
  try {
    const j = JSON.parse(body) as { detail?: unknown };
    if (typeof j.detail === "string") {
      detail = j.detail;
    } else if (Array.isArray(j.detail)) {
      detail = j.detail.map((x) => (typeof x === "object" ? JSON.stringify(x) : String(x))).join("; ");
    }
  } catch {
    /* keep raw body */
  }
  switch (status) {
    case 401:
      return `Unauthorized (401). If the API enforces keys, set X-AIS-Key in Advanced. ${detail}`;
    case 403:
      return `Forbidden (403). ${detail}`;
    case 404:
      return `Not found (404). ${detail}`;
    case 502:
      return `Bad gateway (502) — upstream AIS or dependency failed. ${detail}`;
    case 503:
      return `Service unavailable (503). ${detail}`;
    default:
      return `${status}: ${detail}`;
  }
}

function formatWindow(from: string, to: string): string {
  const f = new Date(from);
  const t = new Date(to);
  const opts: Intl.DateTimeFormatOptions = { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" };
  return `${f.toLocaleString(undefined, opts)} – ${t.toLocaleString(undefined, opts)}`;
}

export default function ConsolePage() {
  const apiBase = useMemo(() => process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000", []);
  const [mmsi, setMmsi] = useState("");
  const [timeFrom, setTimeFrom] = useState("");
  const [timeTo, setTimeTo] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [fusion, setFusion] = useState(false);
  const [geodnetProbe, setGeodnetProbe] = useState(false);
  const [showRaw, setShowRaw] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ValidateResponse | null>(null);
  const [vesselPick, setVesselPick] = useState<NorwayVesselSnippet[]>([]);
  const [vesselsLoading, setVesselsLoading] = useState(false);
  const [vesselsError, setVesselsError] = useState<string | null>(null);
  const [integrityScoreDetailOpen, setIntegrityScoreDetailOpen] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setApiKey(localStorage.getItem("aistruth_api_key") ?? "");
  }, []);

  useEffect(() => {
    if (apiKey) localStorage.setItem("aistruth_api_key", apiKey);
    else localStorage.removeItem("aistruth_api_key");
  }, [apiKey]);

  async function loadNorwayVesselSuggestions() {
    setVesselsLoading(true);
    setVesselsError(null);
    try {
      const res = await fetch(`${apiBase}/v1/ais/norway/vessels?limit=60`, {
        headers: apiKey ? { "X-AIS-Key": apiKey } : undefined,
      });
      const text = await res.text();
      if (!res.ok) throw new Error(formatHttpError(res.status, text));
      setVesselPick(JSON.parse(text) as NorwayVesselSnippet[]);
    } catch (e) {
      setVesselsError(e instanceof Error ? e.message : String(e));
      setVesselPick([]);
    } finally {
      setVesselsLoading(false);
    }
  }

  async function run() {
    if (!/^\d{7,9}$/.test(mmsi.trim())) {
      setError("MMSI must be 7–9 digits.");
      return;
    }
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (timeFrom) params.set("from", new Date(timeFrom).toISOString());
      if (timeTo) params.set("to", new Date(timeTo).toISOString());
      if (fusion) params.set("fusion", "true");
      if (geodnetProbe || fusion) params.set("geodnet_probe", "true");
      const query = params.toString() ? `?${params.toString()}` : "";
      const res = await fetch(`${apiBase}/v1/validate/${encodeURIComponent(mmsi.trim())}${query}`, {
        headers: apiKey ? { "X-AIS-Key": apiKey } : undefined,
        signal: controller.signal,
      });
      const text = await res.text();
      if (!res.ok) throw new Error(formatHttpError(res.status, text));
      setData(JSON.parse(text) as ValidateResponse);
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  function clearResults() {
    setData(null);
    setError(null);
    setShowRaw(false);
    setCopyFeedback(null);
    setIntegrityScoreDetailOpen(false);
  }

  async function copyRawJson() {
    if (!data) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
      setCopyFeedback("Copied");
    } catch {
      setCopyFeedback("Copy failed");
    }
    window.setTimeout(() => setCopyFeedback(null), 2500);
  }

  const mapPoints = data?.evidence.map_track_points?.length ?? 0;
  const vesselSelectValue = useMemo(() => {
    const trimmed = mmsi.trim();
    if (!trimmed || vesselPick.length === 0) return "";
    return vesselPick.some((v) => String(v.mmsi) === trimmed) ? trimmed : "";
  }, [mmsi, vesselPick]);

  const isLocalApi =
    apiBase.includes("127.0.0.1") || apiBase.includes("localhost") || apiBase.includes("0.0.0.0");

  const baselineKm =
    data?.evidence.baseline_m != null && Number.isFinite(data.evidence.baseline_m)
      ? (data.evidence.baseline_m / 1000).toFixed(0)
      : null;

  const hasTelemetry = Boolean(data?.evidence.fusion_result || data?.evidence.geodnet_ntrip_probe);
  const flagCount =
    (data?.flags.length ?? 0) + (data?.evidence.spoofing_findings.length ?? 0);

  return (
    <main className="mx-auto max-w-7xl px-5 pb-16 pt-6 sm:px-6 lg:pt-8">
      {/* Hero */}
      <section
        className={`relative ${integrityScoreDetailOpen ? "z-[120]" : ""} overflow-visible ${panel} px-5 py-6 sm:px-7 sm:py-7`}
      >
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              {isLocalApi ? (
                <span className="rounded-md bg-amber-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-300/90 ring-1 ring-amber-500/20">
                  Local API
                </span>
              ) : null}
            </div>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
              AIS integrity validation
            </h1>
            <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-300">
              Cross-check vessel tracks against motion heuristics and nearby GEODNET reference geometry — with
              plain-language findings your ops team can act on.
            </p>
          </div>
          {data ? (
            <IntegrityScoreCard data={data} onHoverDetailChange={setIntegrityScoreDetailOpen} />
          ) : null}
        </div>
      </section>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(280px,340px)_1fr] lg:items-start">
        {/* Sidebar */}
        <aside className={`${panel} flex flex-col overflow-hidden lg:sticky lg:top-[4.25rem]`}>
          <div className="p-5">
            <SectionHeader
              title="Check a vessel"
              description="Norwegian AIS feed · last 24 h unless you set a window"
            />

            <div className="mt-5 grid gap-4">
            <label className="grid gap-1.5">
              <span className={labelText}>MMSI</span>
              <input
                className={input}
                value={mmsi}
                onChange={(e) => setMmsi(e.target.value)}
                inputMode="numeric"
                placeholder="9-digit vessel ID"
              />
            </label>

            <div className="grid gap-2">
              <button
                className={btnSecondary}
                type="button"
                disabled={vesselsLoading}
                onClick={() => void loadNorwayVesselSuggestions()}
              >
                {vesselsLoading ? "Loading…" : "Browse Norway feed"}
              </button>
              {vesselPick.length > 0 ? (
                <label className="grid gap-1.5">
                  <span className={labelText}>Live vessel list</span>
                  <select
                    className={input}
                    value={vesselSelectValue}
                    onChange={(e) => setMmsi(e.target.value)}
                  >
                    <option value="">Select vessel…</option>
                    {vesselPick.map((v) => (
                      <option key={v.mmsi} value={String(v.mmsi)}>
                        {v.mmsi}
                        {v.name ? ` · ${v.name}` : ""}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
              {vesselsError ? <p className="text-xs text-rose-300">{vesselsError}</p> : null}
            </div>

            <details className={`group ${panelInset}`}>
              <summary className={detailsSummary}>
                Analysis options
                <Chevron />
              </summary>
              <div className="space-y-3 border-t border-slate-600/60 px-4 py-3">
                <CheckboxOption
                  checked={geodnetProbe}
                  onChange={setGeodnetProbe}
                  title="GEODNET NTRIP probe"
                  description="Live caster sample at the latest AIS fix. Adds a few seconds."
                />
                <CheckboxOption
                  checked={fusion}
                  onChange={setFusion}
                  title="Correction-stream evidence"
                  description="Caster telemetry and a map sampling pin. Enables NTRIP probe automatically."
                />
              </div>
            </details>

            <details className={`group ${panelInset}`}>
              <summary className={detailsSummary}>
                Advanced
                <Chevron />
              </summary>
              <div className="space-y-3 border-t border-slate-600/60 px-4 py-3">
                <label className="grid gap-1.5">
                  <span className={labelText}>From</span>
                  <input className={input} type="datetime-local" value={timeFrom} onChange={(e) => setTimeFrom(e.target.value)} />
                </label>
                <label className="grid gap-1.5">
                  <span className={labelText}>To</span>
                  <input className={input} type="datetime-local" value={timeTo} onChange={(e) => setTimeTo(e.target.value)} />
                </label>
                <label className="grid gap-1.5">
                  <span className={labelText}>API key</span>
                  <input
                    className={input}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="X-AIS-Key (if required)"
                    type="password"
                  />
                </label>
              </div>
            </details>

            </div>
          </div>

          <div className="border-t border-slate-600/70 bg-slate-800/40 p-5">
            <button
              className={`${btnPrimary} w-full`}
              type="button"
              onClick={() => void run()}
              disabled={loading || !mmsi.trim()}
            >
              {loading ? "Running validation…" : "Validate track"}
            </button>
            {data ? (
              <button className={`${btnGhost} mt-2 w-full`} type="button" onClick={clearResults}>
                Clear results
              </button>
            ) : null}
          </div>

          {error ? (
            <div className="border-t border-slate-600/70 px-5 py-4">
              <div className="rounded-lg border border-rose-400/40 bg-rose-500/15 px-3 py-2.5 text-xs leading-relaxed text-rose-100">
                {error}
              </div>
            </div>
          ) : null}
        </aside>

        {/* Results */}
        <div className="flex min-w-0 flex-col gap-5">
          {data ? (
            <>
              <ValidationOutcomeCard data={data} />

              <div className={`flex flex-wrap items-center gap-x-5 gap-y-2 ${panelInset} px-4 py-3 text-xs text-slate-300`}>
                <span>
                  <span className="text-slate-400">MMSI </span>
                  <span className="font-medium tabular-nums text-slate-100">{data.mmsi}</span>
                </span>
                <span className="hidden h-3 w-px bg-slate-600 sm:inline" aria-hidden />
                <span>
                  <span className="text-slate-400">Window </span>
                  <span className="text-slate-200">{formatWindow(data.window.from, data.window.to)}</span>
                </span>
                {baselineKm ? (
                  <>
                    <span className="hidden h-3 w-px bg-slate-600 sm:inline" aria-hidden />
                    <span>
                      <span className="text-slate-400">Nearest GEODNET </span>
                      <span className="text-slate-200">~{baselineKm} km</span>
                    </span>
                  </>
                ) : null}
              </div>

              <section className={`${panel} overflow-hidden p-1`}>
                <div className="px-4 pb-3 pt-4">
                  <SectionHeader
                    title="Track & reference network"
                    description="AIS positions with nearest GEODNET stations and optional correction sampling"
                  />
                </div>
                <TrackMap data={data} loading={loading} embedded />
              </section>

              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <MetricCard label="AIS fixes" value={String(data.evidence.track_points)} hint="In selected window" />
                <MetricCard label="Map overlay" value={String(mapPoints)} hint="Points drawn" />
                <MetricCard
                  label="Reference station"
                  value={data.evidence.nearest_node?.name ?? data.evidence.nearest_node_id ?? "—"}
                  hint={baselineKm ? `${baselineKm} km from vessel` : undefined}
                />
                <MetricCard
                  label="Integrity flags"
                  value={flagCount === 0 ? "None" : String(flagCount)}
                  hint={flagCount === 0 ? "No anomalies detected" : "See technical details"}
                />
              </div>

              {hasTelemetry ? (
                <details className={`group ${panel}`}>
                  <summary className={`${detailsSummary} px-5`}>
                    <span>Correction & NTRIP telemetry</span>
                    <Chevron />
                  </summary>
                  <div className="space-y-4 border-t border-slate-600/60 px-5 py-4">
                    {data.evidence.fusion_result ? (
                      <FusionEvidencePanel fusion={data.evidence.fusion_result} />
                    ) : null}
                    <NtripProbePanel data={data} />
                  </div>
                </details>
              ) : null}

              <details className={`group ${panel}`}>
                <summary className={`${detailsSummary} px-5`}>
                  <span>
                    Technical evidence
                    {flagCount > 0 ? (
                      <span className="ml-2 rounded-md bg-slate-800 px-1.5 py-0.5 text-[10px] font-medium text-slate-400">
                        {flagCount}
                      </span>
                    ) : null}
                  </span>
                  <Chevron />
                </summary>
                <div className="border-t border-slate-600/60 px-5 py-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-xs text-slate-500">Raw flags and API response for engineers</p>
                    <div className="flex items-center gap-2">
                      {copyFeedback ? (
                        <span className="text-xs text-emerald-400">{copyFeedback}</span>
                      ) : null}
                      <button className={btnGhost} type="button" onClick={() => void copyRawJson()}>
                        Copy JSON
                      </button>
                      <button className={btnGhost} type="button" onClick={() => setShowRaw(!showRaw)}>
                        {showRaw ? "Hide JSON" : "Show JSON"}
                      </button>
                    </div>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {data.flags.length ? (
                      data.flags.map((flag) => <FlagPill key={flag}>{flag}</FlagPill>)
                    ) : (
                      <FlagPill tone="ok">No motion flags</FlagPill>
                    )}
                    {data.evidence.spoofing_findings.map((finding) => (
                      <FlagPill key={`${finding.kind}-${finding.severity}`} tone={finding.severity}>
                        {finding.severity}: {finding.kind}
                      </FlagPill>
                    ))}
                  </div>
                  {showRaw ? (
                    <pre className="mt-4 max-h-80 overflow-auto rounded-lg bg-slate-900 p-4 text-xs leading-relaxed text-slate-200 ring-1 ring-slate-600/60">
                      {JSON.stringify(data, null, 2)}
                    </pre>
                  ) : null}
                </div>
              </details>
            </>
          ) : (
            <EmptyState loading={loading} />
          )}
        </div>
      </div>
    </main>
  );
}

function Chevron() {
  return (
    <span className="text-[10px] text-slate-600 transition-transform duration-200 group-open:rotate-180">▼</span>
  );
}

function CheckboxOption({
  checked,
  onChange,
  title,
  description,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  title: string;
  description: string;
}) {
  return (
    <label className="flex cursor-pointer gap-2.5">
      <input
        className="mt-0.5 rounded border-slate-600 bg-slate-900 text-cyan-500 focus:ring-cyan-500/30"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        type="checkbox"
      />
      <span className="min-w-0">
        <span className="block text-sm font-medium text-slate-200">{title}</span>
        <span className="mt-0.5 block text-xs leading-relaxed text-slate-500">{description}</span>
      </span>
    </label>
  );
}

function EmptyState({ loading }: { loading: boolean }) {
  return (
    <div className={`flex min-h-[28rem] flex-col items-center justify-center ${panel} px-6 py-12 text-center`}>
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 ring-1 ring-cyan-400/25">
        <svg className="h-6 w-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l5.447 2.724A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
          />
        </svg>
      </div>
      <p className="mt-5 text-base font-medium text-slate-100">
        {loading ? "Fetching AIS track…" : "Ready to validate"}
      </p>
      <p className="mt-2 max-w-sm text-sm leading-relaxed text-slate-400">
        {loading
          ? "Pulling positions from the Norwegian feed and running integrity checks."
          : "Enter an MMSI and run Validate track to see the integrity summary, map, and reference-station context."}
      </p>
      {!loading ? (
        <ol className="mt-8 max-w-xs space-y-2 text-left text-xs text-slate-400">
          <li className="flex gap-2">
            <span className="font-semibold tabular-nums text-cyan-400">1</span>
            Enter a vessel MMSI or pick from the Norway feed
          </li>
          <li className="flex gap-2">
            <span className="font-semibold tabular-nums text-cyan-400">2</span>
            Optionally enable correction-stream evidence for live demos
          </li>
          <li className="flex gap-2">
            <span className="font-semibold tabular-nums text-cyan-400">3</span>
            Review the score, findings, and map overlay
          </li>
        </ol>
      ) : null}
    </div>
  );
}

function FlagPill({ children, tone = "neutral" }: { children: ReactNode; tone?: "ok" | "neutral" | string }) {
  const colors =
    tone === "ok"
      ? "bg-emerald-500/10 text-emerald-300 ring-emerald-500/20"
      : tone === "high"
        ? "bg-rose-500/10 text-rose-300 ring-rose-500/20"
        : tone === "medium"
          ? "bg-amber-500/10 text-amber-300 ring-amber-500/20"
          : "bg-slate-700/80 text-slate-200 ring-slate-600/50";
  return (
    <span className={`inline-flex rounded-md px-2 py-1 text-xs font-medium ring-1 ${colors}`}>{children}</span>
  );
}
