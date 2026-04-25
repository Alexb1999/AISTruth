"""Minimal NMEA GGA builder for NTRIP clients (GEODNET expects periodic GGA)."""

from __future__ import annotations


def nmea_checksum(sentence_body: str) -> int:
    c = 0
    for ch in sentence_body.encode("ascii", errors="strict"):
        c ^= ch
    return c


def build_gpgga(lat: float, lon: float, utc_hhmmss: str = "120000.00") -> bytes:
    """Build a ``$GPGGA`` sentence with checksum (lat N/S, lon E/W)."""
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        raise ValueError("lat/lon out of range")
    lat_deg = int(abs(lat))
    lat_min = (abs(lat) - lat_deg) * 60.0
    ns = "N" if lat >= 0 else "S"
    lat_field = f"{lat_deg:02d}{lat_min:07.4f}"

    lon_abs = abs(lon)
    lon_deg = int(lon_abs)
    lon_min = (lon_abs - lon_deg) * 60.0
    ew = "E" if lon >= 0 else "W"
    lon_field = f"{lon_deg:03d}{lon_min:07.4f}"

    body = f"GPGGA,{utc_hhmmss},{lat_field},{ns},{lon_field},{ew},1,12,0.8,5.0,M,0.0,M,,"
    cs = nmea_checksum(body)
    return f"${body}*{cs:02X}\r\n".encode("ascii")
