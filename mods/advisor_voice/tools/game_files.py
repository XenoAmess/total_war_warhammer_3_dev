"""Read the observed PFH5 archives and advisor tables without modifying them.

Requires Python 3.14+ for the standard-library Zstandard decoder.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
import struct
from compression import zstd


@dataclass(frozen=True)
class Entry:
    offset: int
    size: int
    compressed: bool


class Pack:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.size = path.stat().st_size
        self.mtime_ns = path.stat().st_mtime_ns
        with path.open('rb') as stream:
            header = stream.read(28)
            if len(header) != 28:
                raise ValueError(f'Truncated pack: {path}')
            magic, flags, dependencies, dependency_bytes, count, size, _ = struct.unpack('<4s6I', header)
            if magic != b'PFH5' or flags not in (1, 3, 4) or dependencies or dependency_bytes:
                raise ValueError(f'Unsupported pack header: {path}')
            if size > self.size - 28 or count > size // 6:
                raise ValueError(f'Invalid pack index size: {path}')
            index = stream.read(size)
        self.index_sha256 = hashlib.sha256(header + index).hexdigest()
        self.entries: dict[str, Entry] = {}
        position, offset = 0, 28 + size
        for _ in range(count):
            if position + 5 > len(index):
                raise ValueError('Truncated pack entry')
            length, compressed = struct.unpack_from('<IB', index, position)
            position += 5
            end = index.find(b'\0', position)
            if end < 0 or compressed not in (0, 1):
                raise ValueError('Invalid pack entry')
            name = index[position:end].decode('utf-8').replace('\\', '/')
            parts = PurePosixPath(name)
            if not name or name in ('.', '/') or parts.is_absolute() or '..' in parts.parts or ':' in name or name in self.entries:
                raise ValueError(f'Unsafe or duplicate member: {name}')
            position = end + 1
            if length > self.size - offset:
                raise ValueError(f'Member outside pack: {name}')
            self.entries[name] = Entry(offset, length, bool(compressed))
            offset += length
        if position != size or offset != self.size:
            raise ValueError(f'Pack index or data boundary mismatch: {path}')

    def read(self, name: str) -> bytes:
        entry = self.entries[name]
        with self.path.open('rb') as stream:
            stream.seek(entry.offset)
            data = stream.read(entry.size)
        if len(data) != entry.size:
            raise ValueError(f'Truncated member: {name}')
        if entry.compressed:
            if len(data) < 8 or data[4:8] != bytes.fromhex('28b52ffd'):
                raise ValueError(f'Unsupported compression: {name}')
            expected = struct.unpack_from('<I', data)[0]
            data = zstd.decompress(data[4:])
            if len(data) != expected:
                raise ValueError(f'Decoded size mismatch: {name}')
        return data

    def fingerprint(self) -> dict[str, str | int]:
        return {'path': str(self.path), 'bytes': self.size, 'entries': len(self.entries),
                'header_and_index_sha256': self.index_sha256}

    def verify_unchanged(self) -> None:
        stat = self.path.stat()
        if (stat.st_size, stat.st_mtime_ns) != (self.size, self.mtime_ns):
            raise ValueError(f'Input changed during inspection: {self.path}')


class Reader:
    def __init__(self, data: bytes) -> None:
        self.data, self.position = data, 0

    def take(self, count: int) -> bytes:
        if count < 0 or count > len(self.data) - self.position:
            raise ValueError('Truncated data')
        value = self.data[self.position:self.position + count]
        self.position += count
        return value

    def number(self, fmt: str) -> int:
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def string(self, utf16: bool = False) -> str:
        length = self.number('<H')
        return self.take(length * (2 if utf16 else 1)).decode('utf-16-le' if utf16 else 'utf-8')

    def end(self) -> None:
        if self.position != len(self.data):
            raise ValueError('Trailing data')


@dataclass(frozen=True)
class Advice:
    key: str
    thread: str
    level: int
    advisor: str
    audio_clip: str
    movie_link: str | None
    hidden: bool


def read_advice(data: bytes) -> list[Advice]:
    reader = Reader(data)
    if reader.take(4) != bytes.fromhex('fd fe fc ff'):
        raise ValueError('Unsupported DB GUID header')
    reader.string(utf16=True)
    if reader.take(4) != bytes.fromhex('fc fd fe ff') or reader.number('<I') != 5:
        raise ValueError('Expected advice_levels version 5')
    if reader.number('<B') != 1:
        raise ValueError('Unsupported DB header flag')
    count = reader.number('<I')
    types = 'ssii sssii boib soob bssbo bb'.replace(' ', '')
    rows = []
    for _ in range(count):
        values: list[str | int | None] = []
        for kind in types:
            if kind == 's':
                value: str | int | None = reader.string()
            elif kind == 'o':
                flag = reader.number('<B')
                if flag not in (0, 1):
                    raise ValueError('Invalid optional string flag')
                value = reader.string() if flag else None
            elif kind == 'i':
                value = reader.number('<i')
            else:
                value = reader.number('<B')
                if value not in (0, 1):
                    raise ValueError('Invalid boolean flag')
            values.append(value)
        if not all(isinstance(values[i], str) for i in (0, 1, 18, 19)):
            raise ValueError('Invalid advice strings')
        rows.append(Advice(str(values[0]), str(values[1]), int(values[2]), str(values[19]), str(values[18]),
                           None if values[21] is None else str(values[21]), bool(values[23])))
    reader.end()
    return rows


def read_loc(data: bytes) -> dict[str, str]:
    reader = Reader(data)
    if reader.take(6) != b'\xff\xfeLOC\0' or reader.number('<I') != 1:
        raise ValueError('Unsupported LOC header')
    count = reader.number('<I')
    result = {}
    for _ in range(count):
        key, value = reader.string(utf16=True), reader.string(utf16=True)
        if reader.number('<B') not in (0, 1):
            raise ValueError('Invalid LOC flag')
        if key in result:
            raise ValueError(f'Duplicate LOC key: {key}')
        result[key] = value
    reader.end()
    return result


def read_advice_text(data: bytes) -> dict[str, str]:
    return {key: value for key, value in read_loc(data).items()
            if key.startswith('advice_levels_onscreen_text_')}


def fnv1(name: str) -> int:
    value = 2166136261
    for byte in name.lower().encode('utf-8'):
        value = ((value * 16777619) ^ byte) & 0xffffffff
    return value
