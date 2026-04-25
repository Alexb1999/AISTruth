from __future__ import annotations

from aistruth_core.msm import parse_msm_header


class BitWriter:
    def __init__(self) -> None:
        self.bits: list[int] = []

    def write(self, value: int, width: int) -> None:
        for shift in range(width - 1, -1, -1):
            self.bits.append((value >> shift) & 1)

    def to_bytes(self) -> bytes:
        while len(self.bits) % 8:
            self.bits.append(0)
        out = bytearray()
        for idx in range(0, len(self.bits), 8):
            byte = 0
            for bit in self.bits[idx : idx + 8]:
                byte = (byte << 1) | bit
            out.append(byte)
        return bytes(out)


def test_parse_msm7_header_counts_satellites_signals_and_cells() -> None:
    writer = BitWriter()
    writer.write(1077, 12)
    writer.write(42, 12)
    writer.write(123456, 30)
    writer.write(0, 1)
    writer.write(3, 3)
    writer.write(0, 7)
    writer.write(1, 2)
    writer.write(2, 2)
    writer.write(1, 1)
    writer.write(4, 3)
    writer.write((1 << 63) | (1 << 61), 64)
    writer.write((1 << 31) | (1 << 30), 32)
    writer.write(1, 1)
    writer.write(0, 1)
    writer.write(1, 1)
    writer.write(1, 1)

    header = parse_msm_header(writer.to_bytes())

    assert header.message_number == 1077
    assert header.station_id == 42
    assert header.epoch_time_ms == 123456
    assert header.satellite_count == 2
    assert header.signal_count == 2
    assert header.cell_count == 3
