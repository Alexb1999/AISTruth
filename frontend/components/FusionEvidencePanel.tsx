"use client";

import type { FusionResult } from "@/lib/types";
import { humanizeCorrectionStatus } from "@/lib/validationOutcome";
import { panelInset } from "@/lib/ui";

export default function FusionEvidencePanel({ fusion }: { fusion: FusionResult }) {
  const hasRefined = fusion.refined_lat != null && fusion.refined_lon != null;

  return (
    <div className={`${panelInset} p-4`}>
      <h3 className="text-sm font-semibold text-slate-100">Correction stream</h3>
      <p className="mt-1 text-xs leading-relaxed text-slate-500">
        RTCM telemetry from a short NTRIP session at the latest AIS fix — not a surveyed vessel position.
      </p>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <Fact label="Pipeline" value={fusion.method} mono />
        <Fact
          label="Status"
          value={humanizeCorrectionStatus(fusion.status)}
          valueClass={fusion.ok ? "text-emerald-300" : "text-amber-200"}
        />
        {fusion.baseline_m != null ? (
          <Fact label="Baseline" value={`${Math.round(fusion.baseline_m / 1000)} km`} />
        ) : null}
        {fusion.correction_age_s != null ? (
          <Fact label="Correction age" value={`${fusion.correction_age_s.toFixed(1)} s`} />
        ) : null}
        {fusion.pdop != null ? <Fact label="PDOP" value={String(fusion.pdop)} /> : null}
      </dl>
      {hasRefined ? (
        <p className="mt-3 font-mono text-[11px] text-slate-500">
          Sampling anchor: {fusion.refined_lat?.toFixed(5)}, {fusion.refined_lon?.toFixed(5)}
        </p>
      ) : (
        <p className="mt-3 text-xs text-slate-600">No sampling coordinates in this response.</p>
      )}
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
      <dd className={`mt-0.5 text-sm ${mono ? "font-mono" : "font-medium"} ${valueClass}`}>{value}</dd>
    </div>
  );
}
