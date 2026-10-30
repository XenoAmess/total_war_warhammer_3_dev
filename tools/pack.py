"""Deterministic, uncompressed PFH5 mod packs and UTF-16 Total War loc files."""
from __future__ import annotations

import struct
from pathlib import Path


def write_pack(files: dict[str, bytes], pack_type: int = 3) -> bytes:
    index = bytearray()
    data = bytearray()
    for path, content in sorted(files.items()):
        if path.startswith('/') or '..' in path.split('/') or '\\' in path:
            raise ValueError(f'Unsafe pack path: {path}')
        index += struct.pack('<IB', len(content), 0)
        index += path.replace('/', '\\').encode('utf-8') + b'\0'
        data += content
    return struct.pack('<4s6I', b'PFH5', pack_type, 0, 0, len(files), len(index), 0) + index + data


def read_pack(raw: bytes) -> dict[str, bytes]:
    magic, kind, dependencies, dependency_size, count, index_size, stamp = struct.unpack_from('<4s6I', raw)
    if magic != b'PFH5' or dependencies or dependency_size or kind not in (3, 4):
        raise ValueError('Unsupported pack header')
    position, offset = 28, 28 + index_size
    result = {}
    for _ in range(count):
        size, compressed = struct.unpack_from('<IB', raw, position)
        position += 5
        end = raw.index(0, position)
        path = raw[position:end].decode('utf-8').replace('\\', '/')
        position = end + 1
        if compressed or path in result or offset + size > len(raw):
            raise ValueError('Invalid pack entry')
        result[path] = raw[offset:offset + size]
        offset += size
    if position != 28 + index_size or offset != len(raw):
        raise ValueError('Pack size mismatch')
    return result


def read_translations(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if not line or line.startswith('#'):
            continue
        key, value = line.split('\t', 1)
        if key in result:
            raise ValueError(f'Duplicate localisation key: {key}')
        result[key] = value.replace('\\n', '\n')
    return result


def write_loc(rows: dict[str, str]) -> bytes:
    result = bytearray(b'\xff\xfeLOC\0' + struct.pack('<II', 1, len(rows)))
    for key, value in sorted(rows.items()):
        for text in (key, value):
            encoded = text.encode('utf-16-le')
            result += struct.pack('<H', len(encoded) // 2) + encoded
        result += b'\0'
    return bytes(result)
