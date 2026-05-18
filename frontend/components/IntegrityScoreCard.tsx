"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import {
  baselineContextPhrase,
  correctionStreamBlurb,
  humanizeCorrectionStatus,
  outcomeTier,
  tierPresentation,
} from "@/lib/validationOutcome";
import type { ValidateResponse } from "@/lib/types";

function InfoIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="currentColor" aria-hidden>
      <path
        fillRule="evenodd"
        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z"
        clipRule="evenodd"
      />
    </svg>
  );
}

const HOVER_LEAVE_MS = 200;
const PANEL_WIDTH = "w-[19rem] sm:w-[21rem]";

function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-1.5">
      <dt className="shrink-0 text-xs text-slate-500">{label}</dt>
      <dd className="text-right text-xs font-medium text-slate-200">{value}</dd>
    </div>
  );
}

export default function IntegrityScoreCard({
  data,
  onHoverDetailChange,
}: {
  data: ValidateResponse;
  onHoverDetailChange?: (open: boolean) => void;
}) {
  const tier = outcomeTier(data);
  const pres = tierPresentation[tier];
  const fusion = data.evidence.fusion_result;

  const correctionSummary = useMemo(() => {
    if (!fusion) return null;
    return correctionStreamBlurb(fusion, data.evidence.baseline_m);
  }, [fusion, data.evidence.baseline_m]);

  const baselineOnly = useMemo(() => baselineContextPhrase(data.evidence.baseline_m), [data.evidence.baseline_m]);

  const hasFusionDetail = Boolean(fusion && correctionSummary);
  const hasBaselineDetail = Boolean(data.evidence.baseline_m != null && baselineOnly);
  const hasScoreDetail = hasFusionDetail || hasBaselineDetail;

  const baselineKm = useMemo(() => {
    const m = data.evidence.baseline_m;
    if (m == null || !Number.isFinite(m)) return null;
    return m / 1000;
  }, [data.evidence.baseline_m]);

  const scoreCaption = useMemo(() => {
    if (baselineKm != null) return `~${baselineKm.toFixed(0)} km to GEODNET`;
    return "AIS motion only";
  }, [baselineKm]);

  const nearestLabel = useMemo(() => {
    const node = data.evidence.nearest_node;
    if (node?.name) return node.name;
    if (data.evidence.nearest_node_id) return data.evidence.nearest_node_id;
    return "Mapped node";
  }, [data.evidence.nearest_node, data.evidence.nearest_node_id]);

  const [detailOpen, setDetailOpen] = useState(false);
  const leaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const setPopoverOpen = useCallback(
    (open: boolean) => {
      setDetailOpen(open);
      onHoverDetailChange?.(open);
    },
    [onHoverDetailChange],
  );

  const cancelLeaveTimer = useCallback(() => {
    if (leaveTimerRef.current != null) {
      clearTimeout(leaveTimerRef.current);
      leaveTimerRef.current = null;
    }
  }, []);

  const scheduleClose = useCallback(() => {
    cancelLeaveTimer();
    leaveTimerRef.current = setTimeout(() => setPopoverOpen(false), HOVER_LEAVE_MS);
  }, [cancelLeaveTimer, setPopoverOpen]);

  useEffect(() => {
    return () => cancelLeaveTimer();
  }, [cancelLeaveTimer]);

  useEffect(() => {
    if (!detailOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setPopoverOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [detailOpen, setPopoverOpen]);

  return (
    <div className="relative inline-flex max-w-full flex-col items-end">
      <div
        className={`relative flex w-full shrink-0 flex-col items-center justify-center rounded-2xl border px-5 py-4 pt-5 text-center sm:w-auto sm:min-w-[6.75rem] ${pres.scoreBlockClass}`}
      >
        {hasScoreDetail ? (
          <div
            className="absolute right-1.5 top-1.5 z-10"
            onMouseEnter={() => {
              cancelLeaveTimer();
              setPopoverOpen(true);
            }}
            onMouseLeave={scheduleClose}
          >
            <button
              type="button"
              className={`flex items-center justify-center rounded-full p-1 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400/40 ${
                detailOpen
                  ? "bg-slate-800 text-cyan-200 ring-1 ring-cyan-500/40"
                  : "text-slate-500 hover:bg-slate-800/80 hover:text-slate-300"
              }`}
              aria-expanded={detailOpen}
              aria-controls="integrity-score-hover-detail"
              aria-label="How this score is calculated"
              tabIndex={0}
              onFocus={() => {
                cancelLeaveTimer();
                setPopoverOpen(true);
              }}
              onBlur={scheduleClose}
            >
              <InfoIcon className="h-4 w-4" />
            </button>

            {detailOpen ? (
              <div
                id="integrity-score-hover-detail"
                className={`absolute right-0 top-full z-[200] pt-2 ${PANEL_WIDTH}`}
                role="region"
                aria-label="Score breakdown"
              >
                <div className="relative rounded-xl border border-slate-600/80 bg-slate-800 shadow-2xl shadow-black/40 ring-1 ring-white/[0.06]">
                  <div
                    className="absolute -top-[5px] right-3 h-2.5 w-2.5 rotate-45 border-l border-t border-slate-600 bg-slate-800"
                    aria-hidden
                  />

                  <div className="border-b border-slate-600/70 px-4 py-3">
                    <p className="text-[11px] font-semibold text-slate-100">How this score is calculated</p>
                    <p className="mt-1 text-xs leading-relaxed text-slate-400">
                      AIS implied-speed checks set the base. Distance to the nearest GEODNET station adds a small
                      bonus or penalty.
                    </p>
                  </div>

                  <dl className="border-b border-slate-600/70 px-4 py-2">
                    {baselineKm != null ? (
                      <>
                        <DetailRow label="Nearest station" value={nearestLabel} />
                        <DetailRow label="Baseline" value={`~${baselineKm.toFixed(0)} km`} />
                      </>
                    ) : (
                      <DetailRow label="GEODNET context" value="No mapped node" />
                    )}
                  </dl>

                  {hasFusionDetail ? (
                    <div className="space-y-2 px-4 py-3">
                      <p className="text-[11px] font-medium text-cyan-300/90">Correction stream</p>
                      <p className="text-xs leading-relaxed text-slate-300">{correctionSummary}</p>
                      {fusion ? (
                        <p className="rounded-lg bg-slate-900/80 px-3 py-2 text-[11px] leading-relaxed text-slate-400">
                          <span className="text-slate-500">Status · </span>
                          <span className="text-slate-400">{humanizeCorrectionStatus(fusion.status)}</span>
                          {fusion.correction_age_s != null ? (
                            <span className="text-slate-500"> · {fusion.correction_age_s.toFixed(1)} s old</span>
                          ) : null}
                        </p>
                      ) : null}
                    </div>
                  ) : hasBaselineDetail ? (
                    <div className="px-4 py-3">
                      <p className="text-[11px] font-medium text-slate-400">Station context</p>
                      <p className="mt-1.5 text-xs leading-relaxed text-slate-300">{baselineOnly}</p>
                    </div>
                  ) : null}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}

        <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-slate-400">Score</span>
        <span
          className={`mt-0.5 text-4xl font-bold tabular-nums leading-none tracking-tight sm:text-5xl ${pres.scoreNumberClass}`}
        >
          {data.confidence_score}
        </span>
        <span className="mt-1.5 text-[10px] text-slate-500">{scoreCaption}</span>
      </div>
    </div>
  );
}
