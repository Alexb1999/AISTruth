export type MeResponse = {
  authenticated: boolean;
  auth_mode: string;
  tenant: {
    slug: string;
    name: string;
    ais_source: string;
  } | null;
};

export type NorwayVesselSnippet = {
  mmsi: number;
  lat: number;
  lon: number;
  time: string;
  name?: string | null;
};

export type MapTrackPoint = {
  lat: number;
  lon: number;
  time: string;
};

export type NearestNodeMapInfo = {
  id: string;
  name: string;
  lat: number;
  lon: number;
  distance_m: number;
};

export type GeodnetMapNode = {
  id: string;
  name: string;
  lat: number;
  lon: number;
  distance_m?: number | null;
  is_nearest?: boolean;
};

export type GeodnetCatalogInfo = {
  mode: "fixture" | "hybrid" | "synced" | string;
  active_node_count: number;
  synced_node_count: number;
  fixture_node_count: number;
  last_synced_at?: string | null;
  demo_warning: boolean;
};

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

/** Short NTRIP collection summary from `geodnet_probe=true`; telemetry, not rover position truth. */
export type NtripProbeSummary = {
  ok: boolean;
  host?: string | null;
  port?: number | null;
  mount?: string | null;
  /** API / pydantic may use `seconds`; core probe uses `duration_s`. */
  seconds?: number | null;
  duration_s?: number | null;
  gga_lat?: number | null;
  gga_lon?: number | null;
  http_status?: string | null;
  first_header_line?: string | null;
  bytes_total?: number | null;
  rtcm_frame_count?: number | null;
  rtcm_invalid_frame_count?: number | null;
  rtcm_message_counts?: Record<string, number> | null;
  error?: string | null;
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
    nearest_node?: NearestNodeMapInfo | null;
    map_track_points?: MapTrackPoint[];
    geodnet_map_nodes?: GeodnetMapNode[];
    geodnet_catalog?: GeodnetCatalogInfo | null;
    max_implied_speed_knots?: number | null;
    time_align_method: string;
    spoofing_findings: SpoofingFinding[];
    fusion_result?: FusionResult | null;
    geodnet_ntrip_probe?: NtripProbeSummary | Record<string, unknown> | null;
  };
};
