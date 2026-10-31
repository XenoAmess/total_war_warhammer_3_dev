"""Inspect Wwise RIFF metadata without decoding audio (local-model candidate, reviewed)."""
import hashlib
import struct
from dataclasses import dataclass


@dataclass(frozen=True)
class WemInfo:
    codec: int
    channels: int
    sample_rate: int
    format_signature: str


def inspect_wem(raw: bytes) -> WemInfo:
    if len(raw) < 12 or raw[:4] != b'RIFF' or raw[8:12] != b'WAVE':
        raise ValueError('Expected little-endian RIFF WAVE')
    if struct.unpack_from('<I', raw, 4)[0] + 8 != len(raw):
        raise ValueError('RIFF size mismatch')
    position = 12
    fmt = None
    seen_data = False
    while position < len(raw):
        if position + 8 > len(raw):
            raise ValueError('Truncated chunk header')
        tag, size = struct.unpack_from('<4sI', raw, position)
        position += 8
        if position + size > len(raw):
            raise ValueError('Chunk payload outside file')
        if tag == b'fmt ':
            if fmt is not None or size < 16:
                raise ValueError('Duplicate or short fmt chunk')
            fmt = raw[position:position + size]
        elif tag == b'data':
            if seen_data or size == 0:
                raise ValueError('Duplicate or empty data chunk')
            seen_data = True
        position += size
        # Wwise files can omit the final odd payload's pad byte.
        if size % 2 and position < len(raw):
            position += 1
    if fmt is None or not seen_data:
        raise ValueError('Missing fmt or data chunk')
    codec, channels, rate = struct.unpack_from('<HHI', fmt)
    if not channels or not rate:
        raise ValueError('Zero channels or sample rate')
    return WemInfo(codec, channels, rate, hashlib.sha256(fmt).hexdigest())
