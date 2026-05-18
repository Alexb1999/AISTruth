import type { FusionResult, ValidateResponse } from "@/lib/types";

export type OutcomeTier = "ok" | "review" | "alert";

/** Tier styling for console badges, outcome card borders, and integrity score block. */
export const tierPresentation: Record<
  OutcomeTier,
  {
    label: string;
    badgeClass: string;
    borderClass: string;
    scoreBlockClass: string;
    scoreNumberClass: string;
  }
> = {
  ok: {
    label: "AIS checks: all clear",
    badgeClass: "bg-emerald-500/20 text-emerald-100 ring-emerald-500/40",
    borderClass: "border-emerald-500/30",
    scoreBlockClass: "border-emerald-400/50 bg-emerald-900/30 ring-1 ring-emerald-400/30",
    scoreNumberClass: "text-emerald-50",
  },
  review: {
    label: "AIS checks: review",
    badgeClass: "bg-amber-500/20 text-amber-100 ring-amber-500/35",
    borderClass: "border-amber-500/30",
    scoreBlockClass: "border-amber-400/50 bg-amber-900/30 ring-1 ring-amber-400/30",
    scoreNumberClass: "text-amber-50",
  },
  alert: {
    label: "AIS checks: alert",
    badgeClass: "bg-rose-500/20 text-rose-100 ring-rose-500/40",
    borderClass: "border-rose-500/35",
    scoreBlockClass: "border-rose-400/50 bg-rose-900/30 ring-1 ring-rose-400/30",
    scoreNumberClass: "text-rose-50",
  },
};

const STATION_LOCAL_KM = 15;
const STATION_REGIONAL_KM = 50;

/** User-facing label for backend fusion/correction pipeline statuses. */
export function humanizeCorrectionStatus(status: string): string {
  const known: Record<string, string> = {
    telemetry_only_rover_observations_unavailable:
      "Caster responded, but there are no rover observations to compute a survey-grade fix.",
  };
  return known[status] ?? status.replace(/_/g, " ");
}

export function baselineContextPhrase(baselineM: number | null | undefined): string | null {
  if (baselineM == null || !Number.isFinite(baselineM)) return null;
  const km = baselineM / 1000;
  if (km >= STATION_REGIONAL_KM) {
    return `Nearest GEODNET station is about ${km.toFixed(0)} km away — useful for “is a caster alive?” context only, not local RTK geometry.`;
  }
  if (km >= STATION_LOCAL_KM) {
    return `Reference station is roughly ${km.toFixed(0)} km away — still far for tight RTK; treat correction data as regional context.`;
  }
  return `Reference station is within about ${Math.round(baselineM / 1000)} km — closer than many coastal cases, but AIS + caster bytes still do not yield a surveyed vessel position without a rover solution.`;
}

function worstSpoofingSeverity(findings: ValidateResponse["evidence"]["spoofing_findings"]): "high" | "medium" | "info" | null {
  let worst: "high" | "medium" | "info" | null = null;
  const rank = { high: 3, medium: 2, info: 1 };
  for (const f of findings) {
    const s = f.severity;
    if (s !== "high" && s !== "medium" && s !== "info") continue;
    if (!worst || rank[s] > rank[worst]) worst = s;
  }
  return worst;
}

export function outcomeTier(data: ValidateResponse): OutcomeTier {
  const flags = new Set(data.flags);
  const spoofWorst = worstSpoofingSeverity(data.evidence.spoofing_findings);

  if (flags.has("implausible_speed_over_60kt") || spoofWorst === "high") return "alert";
  if (
    flags.has("high_speed_over_45kt") ||
    flags.has("non_monotonic_or_zero_dt") ||
    spoofWorst === "medium"
  ) {
    return "review";
  }
  if (data.evidence.spoofing_findings.length > 0) return "review";
  if (flags.has("insufficient_samples")) return "review";
  return "ok";
}

export function outcomeHeadline(data: ValidateResponse): string {
  const tier = outcomeTier(data);
  const flags = new Set(data.flags);
  const nFind = data.evidence.spoofing_findings.length;
  const spoofWorst = worstSpoofingSeverity(data.evidence.spoofing_findings);

  if (tier === "alert") {
    if (flags.has("implausible_speed_over_60kt")) {
      return "Motion heuristics show implied speeds that are hard to reconcile with normal vessel movement — treat AIS as untrusted until verified.";
    }
    if (spoofWorst === "high") {
      return "Integrity checks raised high-severity concerns for this track — investigate before relying on AIS position.";
    }
  }
  if (tier === "review") {
    if (spoofWorst === "medium" && nFind > 0) {
      return "Integrity checks flagged possible anomalies (medium severity) — review findings below.";
    }
    if (nFind > 0) {
      return "Integrity checks reported findings — review details in the evidence section.";
    }
    if (flags.has("high_speed_over_45kt")) {
      return "Elevated implied speeds between fixes — can be legitimate (fast craft) or worth a closer look.";
    }
    if (flags.has("non_monotonic_or_zero_dt")) {
      return "Time gaps or repeated timestamps in AIS — track geometry may be less reliable.";
    }
    if (flags.has("insufficient_samples")) {
      return "Only a few AIS points in this window — confidence score is coarse, not a strong pass/fail.";
    }
  }
  return "No spoofing heuristics fired and motion checks look routine for this window — AIS is internally consistent at the checks we run today.";
}

export function correctionStreamBlurb(fusion: FusionResult, evidenceBaselineM: number | null | undefined): string {
  const basePhrase = baselineContextPhrase(
    fusion.baseline_m != null ? fusion.baseline_m : evidenceBaselineM ?? null,
  );
  const parts = [
    "We opened a short NTRIP session at the latest AIS fix. Bytes and timing are real; the orange map pin is just that sampling anchor — not a separate GNSS solution for the vessel.",
  ];
  if (basePhrase) parts.push(basePhrase);
  return parts.join(" ");
}
