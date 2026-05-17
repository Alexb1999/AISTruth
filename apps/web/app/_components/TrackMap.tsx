'use client';

import { useEffect, useMemo } from 'react';
import {
  CircleMarker,
  MapContainer,
  Marker,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';

import type { ValidateResponse } from '../types';

const markerIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

function FitBounds({ bounds }: { bounds: L.LatLngBounds | null }) {
  const map = useMap();
  useEffect(() => {
    if (bounds != null && bounds.isValid()) {
      map.fitBounds(bounds, { padding: [28, 28], maxZoom: 12 });
    }
  }, [map, bounds]);
  return null;
}

export default function TrackMap({ data }: { data: ValidateResponse | null }) {
  const evidence = data?.evidence;
  const refined = evidence?.fusion_result;
  const mapTrack = evidence?.map_track_points;
  const nearest = evidence?.nearest_node;

  const positions = useMemo(() => {
    const track = mapTrack ?? [];
    return track.map((p) => [p.lat, p.lon] as [number, number]);
  }, [mapTrack]);

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
    return b.isValid() ? b : null;
  }, [positions, nearest, refined]);

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

  return (
    <div className="h-80 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
      <MapContainer center={centerPos} zoom={zoom} className="h-full w-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds bounds={bounds} />
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
            <Popup>AIS fix (single point in window)</Popup>
          </CircleMarker>
        ) : null}
        {nearest ? (
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
              GEODNET: {nearest.name}
              <br />
              Baseline ~{Math.round(nearest.distance_m)} m
            </Popup>
          </CircleMarker>
        ) : null}
        {refined?.refined_lat != null && refined.refined_lon != null ? (
          <Marker position={[refined.refined_lat, refined.refined_lon]} icon={markerIcon}>
            <Popup>
              Refined position (fusion evidence)
              <br />
              {refined.status}
            </Popup>
          </Marker>
        ) : null}
      </MapContainer>
    </div>
  );
}
