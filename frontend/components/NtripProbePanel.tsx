"use client";

import type { NtripProbeSummary, ValidateResponse } from "@/lib/types";
import { panelInset } from "@/lib/ui";

function asProbe(raw: ValidateResponse["evidence"]["geodnet_ntrip_probe"]): NtripProbeSummary | null {
  if (!raw || typeof raw !== "object" || !("ok" in raw)) return null;
  return raw as NtripProbeSummary;
}

export default function NtripProbePanel({ data }: { data: ValidateResponse }) {
  const probe = asProbe(data.evidence.geodnet_ntrip_probe);
  if (!probe) return null;

  const durationLabel = probe.seconds ?? probe.duration_s;
  const counts = probe.rtcm_message_counts;
  const topRtcm =
    counts && Object.keys(counts).length > 0
      ? Object.entries(counts)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 5)
          .map(([k, v]) => `${k}: ${v}`)
          .join(" · ")
      : null;

  const stallHint =
    typeof probe.error === "string" &&
    (probe.error.includes("timeout") ||
      probe.error.includes("no_rtcm") ||
      probe.error.includes("stall") ||
      probe.error.includes("header") ||
      probe.error.includes("connection_closed"));

  return (
    <div className={`${panelInset} p-4`}>
      <h3 className="text-sm font-semibold text-slate-100">NTRIP probe</h3>
      <p className="mt-1 text-xs leading-relaxed text-slate-500">
        Stream health at the latest AIS position — confirms the caster is reachable, not vessel RTK accuracy.
      </p>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <Fact
          label="Collection"
          value={probe.ok ? "OK" : "Failed or partial"}
          valueClass={probe.ok ? "text-emerald-300" : "text-rose-300"}
        />
        {probe.host ? (
          <Fact
            label="Caster"
            value={`${probe.host}${probe.port != null ? `:${probe.port}` : ""}${probe.mount ? ` / ${probe.mount}` : ""}`}
            mono
          />
        ) : null}
        <Fact
          label="Data received"
          value={`${probe.bytes_total ?? "—"} B · ${probe.rtcm_frame_count ?? "—"} RTCM frames`}
          mono
        />
        {durationLabel != null ? <Fact label="Duration" value={`${durationLabel.toFixed(1)} s`} /> : null}
      </dl>
      {topRtcm ? <p className="mt-3 font-mono text-[11px] text-slate-600">Top RTCM: {topRtcm}</p> : null}
      {probe.error ? <p className="mt-3 text-xs text-rose-300/90">{probe.error}</p> : null}
      {stallHint ? (
        <p className="mt-2 text-[11px] leading-relaxed text-slate-600">
          Check NTRIP credentials on the API and that outbound port 2101 is allowed on your network.
        </p>
      ) : null}
    </div>
  );
}

function Fact({
  label,
  value,
  mono,
  valueClass = "text-slate-200",
}: {
  label: string;
  value: string;
  mono?: boolean;
  valueClass?: string;
}) {
  return (
    <div>
      <dt className="text-[11px] font-medium uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className={`mt-0.5 truncate text-sm ${mono ? "font-mono" : "font-medium"} ${valueClass}`} title={value}>
        {value}
      </dd>
    </div>
  );
}
