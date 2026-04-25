"use client";

import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";

import type { ValidateResponse } from "../types";

const markerIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

export default function TrackMap({ data }: { data: ValidateResponse | null }) {
  const refined = data?.evidence.fusion_result;
  const lat = refined?.refined_lat ?? 59.6667;
  const lon = refined?.refined_lon ?? 10.6333;

  return (
    <div className="h-80 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900">
      <MapContainer
        center={[lat, lon]}
        zoom={refined?.refined_lat ? 10 : 5}
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {refined?.refined_lat && refined.refined_lon ? (
          <Marker position={[refined.refined_lat, refined.refined_lon]} icon={markerIcon}>
            <Popup>
              Refined position evidence
              <br />
              {refined.status}
            </Popup>
          </Marker>
        ) : null}
      </MapContainer>
    </div>
  );
}
