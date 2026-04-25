export type SpoofingFinding = {
  kind: string;
  severity: string;
  evidence: Record<string, unknown>;
};

export type FusionResult = {
  ok: boolean;
  method: string;
  refined_lat?: number | null;
  refined_lon?: number | null;
  baseline_m?: number | null;
  correction_age_s?: number | null;
  pdop?: number | null;
  status: string;
};

export type ValidateResponse = {
  mmsi: number;
  window: { from: string; to: string };
  confidence_score: number;
  flags: string[];
  evidence: {
    track_points: number;
    source: string;
    rules_version: string;
    nearest_node_id?: string | null;
    baseline_m?: number | null;
    max_implied_speed_knots?: number | null;
    time_align_method: string;
    spoofing_findings: SpoofingFinding[];
    fusion_result?: FusionResult | null;
  };
};
