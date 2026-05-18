'use client';

import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Circle,
  CircleMarker,
  MapContainer,
  Marker,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';

import type { GeodnetMapNode, ValidateResponse } from "@/lib/types";
import { humanizeCorrectionStatus } from "@/lib/validationOutcome";

/** Great-circle distance in meters (WGS84 sphere approx). */
function haversineMeters(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6_371_000;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const φ1 = toRad(lat1);
  const φ2 = toRad(lat2);
  const Δφ = toRad(lat2 - lat1);
  const Δλ = toRad(lon2 - lon1);
  const a =
    Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(a)));
}

const markerIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

/** Illustrative dual-radius footprints around reference stations (map UX only—not cm-class guarantees). */
const GEODNET_INNER_RADIUS_M = 22_000;
const GEODNET_OUTER_RADIUS_M = 55_000;

function padBoundsForGeodnetZones(b: L.LatLngBounds, nodes: GeodnetMapNode[]) {
  if (nodes.length === 0) return;
  const padLat = GEODNET_OUTER_RADIUS_M / 111_000;
  for (const node of nodes) {
    const padLon = GEODNET_OUTER_RADIUS_M / (111_000 * Math.max(Math.cos((node.lat * Math.PI) / 180), 0.15));
    b.extend([node.lat, node.lon]);
    b.extend([node.lat + padLat, node.lon + padLon]);
    b.extend([node.lat - padLat, node.lon - padLon]);
  }
}

/** Corner-bracket “enter fullscreen” icon (rounded stroke caps). */
function IconFullscreenEnter({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <polyline
        points="10 4 4 4 4 10"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <polyline
        points="14 4 20 4 20 10"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <polyline
        points="14 20 20 20 20 14"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <polyline
        points="10 20 4 20 4 14"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Matching “exit fullscreen” compress icon. */
function IconFullscreenExit({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" aria-hidden>
      <polyline
        points="4 14 4 20 10 20"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <polyline
        points="20 14 20 20 14 20"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <polyline
        points="20 10 20 4 14 4"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <polyline
        points="4 10 4 4 10 4"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function FitBounds({ bounds }: { bounds: L.LatLngBounds | null }) {
  const map = useMap();
  useEffect(() => {
    if (bounds != null && bounds.isValid()) {
      map.fitBounds(bounds, { padding: [28, 28], maxZoom: 12 });
    }
  }, [map, bounds]);
  return null;
}

function getFullscreenElement(): Element | null {
  const doc = document as Document & {
    webkitFullscreenElement?: Element | null;
    mozFullScreenElement?: Element | null;
  };
  return document.fullscreenElement ?? doc.webkitFullscreenElement ?? doc.mozFullScreenElement ?? null;
}

/** Leaflet tiles/layers break if the map size changes (e.g. fullscreen); force a layout pass. */
function InvalidateSizeOnContainerChange() {
  const map = useMap();
  useEffect(() => {
    const fix = () => {
      requestAnimationFrame(() => {
        map.invalidateSize({ animate: false });
      });
    };
    document.addEventListener('fullscreenchange', fix);
    window.addEventListener('resize', fix);
    return () => {
      document.removeEventListener('fullscreenchange', fix);
      window.removeEventListener('resize', fix);
    };
  }, [map]);
  return null;
}

export default function TrackMap({
  data,
  loading = false,
  embedded = false,
}: {
  data: ValidateResponse | null;
  loading?: boolean;
  embedded?: boolean;
}) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [fullscreen, setFullscreen] = useState(false);

  useEffect(() => {
    const sync = () => {
      setFullscreen(getFullscreenElement() === rootRef.current);
    };
    document.addEventListener('fullscreenchange', sync);
    return () => document.removeEventListener('fullscreenchange', sync);
  }, []);

  const toggleFullscreen = useCallback(async () => {
    const el = rootRef.current;
    if (!el) return;
    try {
      if (!getFullscreenElement()) {
        if (el.requestFullscreen) {
          await el.requestFullscreen();
        } else {
          const legacy = el as HTMLDivElement & { webkitRequestFullscreen?: () => void };
          legacy.webkitRequestFullscreen?.();
        }
      } else if (getFullscreenElement() === el) {
        const doc = document as Document & {
          webkitExitFullscreen?: () => Promise<void>;
          mozCancelFullScreen?: () => Promise<void>;
        };
        if (document.exitFullscreen) await document.exitFullscreen();
        else if (doc.webkitExitFullscreen) await doc.webkitExitFullscreen();
        else doc.mozCancelFullScreen?.();
      }
    } catch {
      /* user gesture / permission */
    }
  }, []);

  const evidence = data?.evidence;
  const refined = evidence?.fusion_result;
  const mapTrack = evidence?.map_track_points;
  const nearest = evidence?.nearest_node;

  const zoneNodes = useMemo((): GeodnetMapNode[] => {
    const raw = evidence?.geodnet_map_nodes;
    if (raw && raw.length > 0) return raw;
    if (nearest) {
      return [{ id: nearest.id, name: nearest.name, lat: nearest.lat, lon: nearest.lon }];
    }
    return [];
  }, [evidence?.geodnet_map_nodes, nearest]);

  const showGeodnetZones = zoneNodes.length > 0;

  const positions = useMemo(() => {
    const track = mapTrack ?? [];
    return track.map((p) => [p.lat, p.lon] as [number, number]);
  }, [mapTrack]);

  const lastAis: [number, number] | null =
    positions.length > 0 ? positions[positions.length - 1] : null;

  const refinedPos: [number, number] | null =
    refined?.refined_lat != null && refined.refined_lon != null
      ? [refined.refined_lat, refined.refined_lon]
      : null;

  const deltaFusionM =
    lastAis && refinedPos != null
      ? haversineMeters(lastAis[0], lastAis[1], refinedPos[0], refinedPos[1])
      : null;

  /** Backend rtk_v1 uses latest AIS as the refined anchor — expect ~0 m until a solver exists. */
  const fusionCoincident = deltaFusionM != null && deltaFusionM <= 3;
  const showFusionOffset = deltaFusionM != null && deltaFusionM > 3;

  const bounds = useMemo(() => {
    if (positions.length === 0 && !nearest && refined?.refined_lat == null) {
      return null;
    }
    const b = L.latLngBounds([]);
    for (const [lat, lon] of positions) {
      b.extend([lat, lon]);
    }
    if (nearest) {
      b.extend([nearest.lat, nearest.lon]);
    }
    if (refined?.refined_lat != null && refined.refined_lon != null) {
      b.extend([refined.refined_lat, refined.refined_lon]);
    }
    padBoundsForGeodnetZones(b, zoneNodes);
    return b.isValid() ? b : null;
  }, [positions, nearest, refined, zoneNodes]);

  const fallbackCenter: [number, number] = [59.6667, 10.6333];
  const centerPos: [number, number] =
    positions.length > 0
      ? positions[positions.length - 1]
      : nearest
        ? [nearest.lat, nearest.lon]
        : refined?.refined_lat != null && refined?.refined_lon != null
          ? [refined.refined_lat, refined.refined_lon]
          : fallbackCenter;

  const zoom =
    data == null || (positions.length === 0 && !nearest && refined?.refined_lat == null)
      ? 5
      : 10;

  const showLegend =
    data != null && (positions.length > 0 || nearest || refined?.refined_lat != null);

  const showLatestAisInLegend = positions.length > 0;

  const shellClass = embedded
    ? "relative flex h-[min(34rem,68vh)] min-h-[20rem] flex-col overflow-hidden rounded-xl bg-slate-900 fullscreen:h-screen fullscreen:max-h-none fullscreen:min-h-0 fullscreen:rounded-none"
    : "relative flex h-[min(36rem,72vh)] min-h-[22rem] flex-col overflow-hidden rounded-2xl border border-slate-700 bg-slate-800 fullscreen:h-screen fullscreen:max-h-none fullscreen:min-h-0 fullscreen:rounded-none fullscreen:border-slate-700";

  return (
    <div ref={rootRef} className={shellClass}>
      {loading ? (
        <div className="pointer-events-none absolute inset-0 z-[1001] flex items-center justify-center bg-slate-950/40 backdrop-blur-[2px]">
          <div className="rounded-xl border border-cyan-500/30 bg-slate-900/95 px-4 py-3 text-sm font-medium text-cyan-100 shadow-lg">
            Loading validation…
          </div>
        </div>
      ) : null}
      <div className="pointer-events-none absolute right-1.5 top-1.5 z-[1001] flex justify-end">
        <button
          type="button"
          onClick={() => void toggleFullscreen()}
          title={fullscreen ? 'Exit full screen (Esc)' : 'Full screen map'}
          aria-label={fullscreen ? 'Exit full screen' : 'Enter full screen'}
          className="pointer-events-auto flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded border-2 border-black/20 bg-white text-neutral-900 shadow-[0_1px_5px_rgba(0,0,0,0.4)] transition hover:bg-neutral-50"
        >
          {fullscreen ? (
            <IconFullscreenExit className="h-4 w-4" />
          ) : (
            <IconFullscreenEnter className="h-4 w-4" />
          )}
        </button>
      </div>
      {showLegend ? (
        <div className="pointer-events-none absolute bottom-2 right-2 z-[1002] w-[11rem] max-w-[calc(100%-0.75rem)] rounded-lg border border-slate-600/80 bg-slate-800 px-2.5 py-2 text-[10px] leading-snug text-slate-200 shadow-lg sm:w-[12rem]">
          <div className="mb-1 text-[9px] font-semibold uppercase tracking-wide text-slate-500">Legend</div>
          <ul className="space-y-0.5">
            {positions.length >= 2 ? (
              <li className="flex items-center gap-1.5">
                <span className="h-1.5 w-4 shrink-0 rounded-sm bg-sky-400" />
                AIS track
              </li>
            ) : positions.length === 1 ? (
              <li className="flex items-center gap-1.5">
                <span className="h-2 w-2 shrink-0 rounded-full border border-sky-300 bg-sky-500" />
                AIS fix
              </li>
            ) : null}
            {showLatestAisInLegend && positions.length >= 2 ? (
              <li className="flex items-center gap-1.5">
                <span className="h-2 w-2 shrink-0 rounded-full border border-white/70 bg-sky-600" />
                Latest AIS
              </li>
            ) : null}
            {showFusionOffset ? (
              <li className="flex items-center gap-1.5 text-amber-200/95">
                <span className="h-px w-4 shrink-0 border-t border-dashed border-amber-400" />
                AIS ↔ pin Δ {deltaFusionM!.toFixed(0)} m
              </li>
            ) : null}
            {fusionCoincident && refinedPos ? (
              <li className="text-[9px] text-amber-200/80 sm:text-[10px]">NTRIP pin matches AIS (no rover fix yet)</li>
            ) : null}
            {nearest ? (
              <li className="flex items-center gap-1.5">
                <span className="h-2 w-2 shrink-0 rounded-full bg-emerald-400" />
                Nearest base
              </li>
            ) : null}
            {refined?.refined_lat != null && refined?.refined_lon != null ? (
              <li className="flex items-center gap-1.5">
                <span className="h-2 w-2 shrink-0 rotate-45 border border-amber-400 bg-amber-500/50" />
                NTRIP sample
              </li>
            ) : null}
          </ul>
        </div>
      ) : null}
      {showGeodnetZones && showLegend ? (
        <div
          className="pointer-events-none absolute bottom-2 left-2 z-[1000] rounded-lg border border-slate-600/80 bg-slate-800 px-2.5 py-2 text-[10px] shadow-lg"
          title="Indicative station footprints (~22 km / ~55 km). Not a certified accuracy claim."
        >
          <div className="mb-1 text-[9px] font-semibold uppercase tracking-wide text-slate-500">RTK precision zones</div>
          <div className="inline-flex items-center gap-1 font-medium text-slate-200">
            <span className="inline-flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full border border-emerald-900 bg-emerald-700" />
              2 cm
            </span>
            <span className="text-slate-600">·</span>
            <span className="inline-flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full border border-emerald-600 bg-emerald-400" />
              10 cm
            </span>
          </div>
        </div>
      ) : null}
      <MapContainer center={centerPos} zoom={zoom} className="z-0 min-h-0 flex-1">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <InvalidateSizeOnContainerChange />
        <FitBounds bounds={bounds} />
        {zoneNodes.map((node) => (
          <Fragment key={node.id}>
            <Circle
              center={[node.lat, node.lon]}
              radius={GEODNET_OUTER_RADIUS_M}
              pathOptions={{
                color: '#22c55e',
                weight: 1,
                fillColor: '#4ade80',
                fillOpacity: 0.12,
                opacity: 0.42,
              }}
            />
            <Circle
              center={[node.lat, node.lon]}
              radius={GEODNET_INNER_RADIUS_M}
              pathOptions={{
                color: '#166534',
                weight: 1.5,
                fillColor: '#15803d',
                fillOpacity: 0.22,
                opacity: 0.48,
              }}
            />
            <CircleMarker
              center={[node.lat, node.lon]}
              radius={nearest?.id === node.id ? 6 : 4}
              pathOptions={{
                color: nearest?.id === node.id ? '#ecfdf5' : '#15803d',
                weight: nearest?.id === node.id ? 2 : 1,
                fillColor: '#22c55e',
                fillOpacity: 0.95,
              }}
            >
              <Popup>
                GEODNET: {node.name}
                {nearest?.id === node.id ? (
                  <>
                    <br />
                    <strong>Nearest to latest AIS</strong>
                    <br />
                    Baseline ≈ {Math.round(nearest.distance_m)} m
                  </>
                ) : null}
                <br />
                <span className="text-[11px] text-neutral-600">
                  Shaded rings are indicative service-style footprints, not certified margins.
                </span>
              </Popup>
            </CircleMarker>
          </Fragment>
        ))}
        {positions.length >= 2 ? (
          <Polyline
            positions={positions}
            pathOptions={{ color: '#38bdf8', weight: 3, opacity: 0.9 }}
          />
        ) : positions.length === 1 ? (
          <CircleMarker
            center={positions[0]}
            radius={6}
            pathOptions={{
              color: '#38bdf8',
              fillColor: '#38bdf8',
              fillOpacity: 0.85,
            }}
          >
            <Popup>
              AIS-derived position (single fix in window)
              {refinedPos && deltaFusionM != null ? (
                <>
                  <br />
                  Δ to sampling pin: {deltaFusionM.toFixed(1)} m
                </>
              ) : null}
            </Popup>
          </CircleMarker>
        ) : null}
        {showFusionOffset && lastAis && refinedPos ? (
          <Polyline
            positions={[lastAis, refinedPos]}
            pathOptions={{
              color: '#fbbf24',
              weight: 3,
              opacity: 0.92,
              dashArray: '10 12',
            }}
          />
        ) : null}
        {!showGeodnetZones && nearest ? (
          <CircleMarker
            center={[nearest.lat, nearest.lon]}
            radius={8}
            pathOptions={{
              color: '#34d399',
              fillColor: '#34d399',
              fillOpacity: 0.85,
            }}
          >
            <Popup>
              Nearest GEODNET node: {nearest.name}
              <br />
              Baseline ≈ {Math.round(nearest.distance_m)} m (context, not rover RTK)
            </Popup>
          </CircleMarker>
        ) : null}
        {positions.length >= 2 && lastAis ? (
          <CircleMarker
            center={lastAis}
            radius={9}
            pathOptions={{
              color: '#f8fafc',
              weight: 3,
              fillColor: '#0369a1',
              fillOpacity: 0.95,
            }}
          >
            <Popup>
              Latest AIS (end of window)
              {refinedPos && deltaFusionM != null ? (
                <>
                  <br />
                  Δ to sampling pin: {deltaFusionM.toFixed(1)} m
                </>
              ) : null}
            </Popup>
          </CircleMarker>
        ) : null}
        {refined?.refined_lat != null && refined.refined_lon != null ? (
          <Marker position={[refined.refined_lat, refined.refined_lon]} icon={markerIcon}>
            <Popup>
              NTRIP / correction telemetry (sampling anchor)
              <br />
              {humanizeCorrectionStatus(refined.status)}
              {lastAis && deltaFusionM != null ? (
                <>
                  <br />
                  Δ vs latest AIS: {deltaFusionM.toFixed(1)} m
                </>
              ) : null}
              <br />
              <span className="text-xs">Not claimed as survey-grade vessel position.</span>
            </Popup>
          </Marker>
        ) : null}
      </MapContainer>
    </div>
  );
}
