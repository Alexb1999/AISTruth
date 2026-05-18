"use client";

import { useEffect } from "react";
import { Circle, CircleMarker, MapContainer, Polyline, TileLayer, useMap } from "react-leaflet";

/** Illustrative demo geometry — matches console map semantics, not live data. */
const GEODNET_NODE = { lat: 69.682, lon: 18.987, name: "GEODNET reference" };

const AIS_TRACK: [number, number][] = [
  [69.648, 18.912],
  [69.655, 18.928],
  [69.662, 18.945],
  [69.668, 18.962],
  [69.674, 18.978],
];

/** Illustrative “refined” path — smoother leg near the latest fix (demo only, not survey RTK). */
const REFINED_TRACK: [number, number][] = [
  [69.662, 18.945],
  [69.666, 18.954],
  [69.671, 18.968],
  [69.676, 18.981],
];

const LATEST_AIS = AIS_TRACK[AIS_TRACK.length - 1];
const NTRIP_SAMPLE: [number, number] = [69.676, 18.981];

const INNER_M = 22_000;
const OUTER_M = 55_000;

function FitDemo() {
  const map = useMap();
  useEffect(() => {
    map.fitBounds(
      [
        [69.635, 18.88],
        [69.695, 19.04],
      ],
      { padding: [24, 24], maxZoom: 11 },
    );
  }, [map]);
  return null;
}

export default function LandingMapDemo() {
  return (
    <div className="landing-map relative isolate z-0 h-[min(22rem,42vh)] min-h-[18rem] w-full overflow-hidden rounded-xl bg-slate-200 sm:h-[min(26rem,48vh)]">
      <MapContainer
        center={[69.665, 18.96]}
        zoom={11}
        className="h-full w-full"
        scrollWheelZoom={false}
        dragging={false}
        doubleClickZoom={false}
        zoomControl={false}
        attributionControl={false}
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <FitDemo />
        <Circle
          center={[GEODNET_NODE.lat, GEODNET_NODE.lon]}
          radius={OUTER_M}
          pathOptions={{
            color: "#22c55e",
            weight: 1,
            fillColor: "#4ade80",
            fillOpacity: 0.1,
            opacity: 0.45,
          }}
        />
        <Circle
          center={[GEODNET_NODE.lat, GEODNET_NODE.lon]}
          radius={INNER_M}
          pathOptions={{
            color: "#166534",
            weight: 1.5,
            fillColor: "#15803d",
            fillOpacity: 0.18,
            opacity: 0.5,
          }}
        />
        <CircleMarker
          center={[GEODNET_NODE.lat, GEODNET_NODE.lon]}
          radius={7}
          pathOptions={{
            color: "#ecfdf5",
            weight: 2,
            fillColor: "#22c55e",
            fillOpacity: 0.95,
          }}
        />
        <Polyline positions={AIS_TRACK} pathOptions={{ color: "#38bdf8", weight: 4, opacity: 0.9 }} />
        <Polyline
          positions={REFINED_TRACK}
          pathOptions={{
            color: "#fbbf24",
            weight: 3.5,
            opacity: 0.95,
            dashArray: "8 10",
          }}
        />
        <CircleMarker
          center={LATEST_AIS}
          radius={8}
          pathOptions={{
            color: "#f8fafc",
            weight: 3,
            fillColor: "#0369a1",
            fillOpacity: 0.95,
          }}
        />
        <CircleMarker
          center={NTRIP_SAMPLE}
          radius={6}
          pathOptions={{
            color: "#fbbf24",
            weight: 2,
            fillColor: "#f59e0b",
            fillOpacity: 0.85,
          }}
        />
      </MapContainer>

      <div className="pointer-events-none absolute bottom-2 left-2 right-2 z-10 flex flex-wrap items-end justify-between gap-2">
        <div className="rounded-lg border border-slate-600/80 bg-slate-950/95 px-2.5 py-2 text-[10px] text-slate-200 shadow-lg">
          <p className="mb-1 font-semibold uppercase tracking-wide text-slate-400">Legend</p>
          <ul className="space-y-0.5">
            <li className="flex items-center gap-1.5">
              <span className="h-1 w-3 rounded-sm bg-sky-400" />
              AIS track
            </li>
            <li className="flex items-center gap-1.5">
              <span className="h-0.5 w-3 border-t-2 border-dashed border-amber-400" />
              Refined leg (demo)
            </li>
            <li className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              GEODNET node
            </li>
            <li className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full border border-white bg-sky-700" />
              Latest AIS
            </li>
          </ul>
        </div>
        <div className="rounded-lg border border-amber-500/40 bg-slate-900/95 px-3 py-2 text-right shadow-lg">
          <p className="text-[9px] font-semibold uppercase tracking-wider text-slate-400">Integrity score</p>
          <p className="text-2xl font-bold tabular-nums text-amber-100">79</p>
          <p className="text-[9px] text-slate-500">~106 km to node</p>
        </div>
      </div>
    </div>
  );
}
