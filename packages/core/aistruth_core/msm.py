from __future__ import annotations

from dataclasses import dataclass

MSM7_MESSAGE_TYPES = {1077, 1087, 1097, 1117}


@dataclass(frozen=True)
class MsmHeader:
    message_number: int
    station_id: int
    epoch_time_ms: int
    multiple_message: bool
    issue_of_data_station: int
    clock_steering_indicator: int
    external_clock_indicator: int
    smoothing_indicator: bool
    smoothing_interval: int
    satellite_count: int
    signal_count: int
    cell_count: int


class BitReader:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.bit_pos = 0

    def read(self, width: int) -> int:
        value = 0
        for _ in range(width):
            byte_index = self.bit_pos // 8
            if byte_index >= len(self.payload):
                raise ValueError("MSM payload ended before header was complete")
            bit_index = 7 - (self.bit_pos % 8)
            value = (value << 1) | ((self.payload[byte_index] >> bit_index) & 1)
            self.bit_pos += 1
        return value


def parse_msm_header(payload: bytes) -> MsmHeader:
    reader = BitReader(payload)
    message_number = reader.read(12)
    if message_number not in MSM7_MESSAGE_TYPES:
        raise ValueError(f"RTCM message {message_number} is not an MSM7 message")
    station_id = reader.read(12)
    epoch_time_ms = reader.read(30)
    multiple_message = bool(reader.read(1))
    issue_of_data_station = reader.read(3)
    reader.read(7)  # reserved
    clock_steering_indicator = reader.read(2)
    external_clock_indicator = reader.read(2)
    smoothing_indicator = bool(reader.read(1))
    smoothing_interval = reader.read(3)
    satellite_mask = reader.read(64)
    signal_mask = reader.read(32)
    satellite_count = satellite_mask.bit_count()
    signal_count = signal_mask.bit_count()
    cell_count = sum(reader.read(1) for _ in range(satellite_count * signal_count))
    return MsmHeader(
        message_number=message_number,
        station_id=station_id,
        epoch_time_ms=epoch_time_ms,
        multiple_message=multiple_message,
        issue_of_data_station=issue_of_data_station,
        clock_steering_indicator=clock_steering_indicator,
        external_clock_indicator=external_clock_indicator,
        smoothing_indicator=smoothing_indicator,
        smoothing_interval=smoothing_interval,
        satellite_count=satellite_count,
        signal_count=signal_count,
        cell_count=cell_count,
    )
