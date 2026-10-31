"""Prepare and stage Workshop gallery screenshots offline.

This module validates the source-controlled screenshot manifest and the
Mod's description.bbcode inline embeds, then stages the confirmed gallery
records through the Steamworks UGC preview APIs. It never submits an update,
writes state, or touches the filesystem beyond reading project files.
"""
from __future__ import annotations

import ctypes as C
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from project import ModProject

MAX_IMAGE_BYTES = 1048576  # strictly less than 1 MiB
ALLOWED_SUFFIXES = ('.png', '.jpg', '.jpeg', '.gif')
SHA256_RE = re.compile(r'^[0-9a-f]{64}$')
HTTPS_URL_RE = re.compile(r'^https://')


def _read_manifest(project: ModProject) -> list[dict[str, Any]]:
    manifest_path = project.root / 'workshop' / 'screenshots.json'
    if not manifest_path.is_file():
        return []
    try:
        data = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise RuntimeError(f'Invalid screenshots.json: {exc}') from exc
    if not isinstance(data, dict):
        raise RuntimeError('screenshots.json must be an object')
    screenshots = data.get('screenshots')
    if not isinstance(screenshots, list):
        raise RuntimeError('screenshots must be a list')
    return screenshots


def _validate_path(project: ModProject, rel: str) -> Path:
    if not isinstance(rel, str) or not rel:
        raise RuntimeError('screenshot file must be a non-empty string')
    if rel.startswith('/') or '..' in rel.split('/') or '\\' in rel:
        raise RuntimeError(f'unsafe screenshot path: {rel}')
    if not rel.lower().endswith(ALLOWED_SUFFIXES):
        raise RuntimeError(f'disallowed screenshot suffix: {rel}')
    base = (project.root / 'workshop' / 'screenshots').resolve()
    candidate = (base / rel).resolve()
    if not candidate.is_relative_to(base):
        raise RuntimeError(f'screenshot path escapes workshop/screenshots: {rel}')
    if candidate.is_symlink():
        raise RuntimeError(f'symlink not allowed: {rel}')
    if not candidate.is_file():
        raise RuntimeError(f'screenshot file missing: {rel}')
    return candidate


def _validate_sha(path: Path, expected: str) -> None:
    if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
        raise RuntimeError(f'malformed sha256: {expected!r}')
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise RuntimeError(f'sha256 mismatch for {path.name}: expected {expected}, got {actual}')


def _validate_size(path: Path) -> None:
    size = path.stat().st_size
    if size == 0:
        raise RuntimeError(f'empty screenshot file: {path.name}')
    if size >= MAX_IMAGE_BYTES:
        raise RuntimeError(f'screenshot too large ({size} bytes): {path.name}')


def _validate_caption(caption: Any) -> str:
    if not isinstance(caption, str) or not caption.strip():
        raise RuntimeError('caption must be a non-empty string')
    return caption


def _validate_url(url: Any) -> str:
    if not isinstance(url, str) or not HTTPS_URL_RE.match(url) or not urlsplit(url).hostname or any(c in url for c in '[]\r\n'):
        raise RuntimeError(f'url must be an HTTPS string: {url!r}')
    return url


def _check_embeds(project: ModProject, entries: list[dict[str, Any]]) -> None:
    desc_path = project.root / 'workshop' / 'description.bbcode'
    if not desc_path.is_file():
        raise RuntimeError('description.bbcode is required for inline embeds')
    text = desc_path.read_text(encoding='utf-8')
    for entry in entries:
        url = entry.get('url')
        if url is None:
            raise RuntimeError(f'screenshot {entry.get("file")!r} missing url for inline embed')
        token = f'[img]{url}[/img]'
        if text.count(token) != 1:
            raise RuntimeError(f'inline embed mismatch for {url!r} in description.bbcode')


def prepare_gallery(project: ModProject, state: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate the manifest and return ordered gallery operation records.

    Returns [] when no screenshots.json exists (backwards compatibility).
    Raises RuntimeError on any validation failure or unresolved pending state.
    """
    if state.get('gallery_pending'):
        raise RuntimeError('gallery_pending must be resolved by owner before preparing new gallery records')

    entries = _read_manifest(project)

    # Validate schema fields and collect records
    records: list[dict[str, Any]] = []
    seen_files: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise RuntimeError('each screenshot entry must be an object')
        rel = entry.get('file')
        path = _validate_path(project, rel)
        if str(path).casefold() in seen_files:
            raise RuntimeError(f'duplicate screenshot file: {rel}')
        seen_files.add(str(path).casefold())
        _validate_sha(path, entry.get('sha256', ''))
        _validate_size(path)
        caption = _validate_caption(entry.get('caption'))
        url = _validate_url(entry.get('url'))
        records.append({
            'file': rel,
            'absolute_path': str(path),
            'sha256': entry['sha256'],
            'caption': caption,
            'url': url,
        })

    if records:
        _check_embeds(project, records)

    # Determine operations against confirmed gallery
    confirmed = state.get('gallery', [])
    if not isinstance(confirmed, list):
        raise RuntimeError('state.gallery must be a list')

    # Reject removal/reordering of previous slots
    if len(confirmed) > len(records):
        raise RuntimeError('cannot remove previously confirmed gallery slots')
    for i, prev in enumerate(confirmed):
        if not isinstance(prev, dict):
            raise RuntimeError('confirmed gallery entry must be an object')
        if prev.get('index') != i:
            raise RuntimeError('confirmed gallery index does not match its slot')
        if prev.get('file') != records[i]['file']:
            raise RuntimeError(f'gallery slot {i} reordered: expected {prev.get("file")!r}, got {records[i]["file"]!r}')

    operations: list[dict[str, Any]] = []
    for i, rec in enumerate(records):
        if i < len(confirmed):
            prev = confirmed[i]
            if prev.get('sha256') == rec['sha256']:
                op = 'skip'
            else:
                op = 'update'
        else:
            op = 'add'
        operations.append({
            'file': rec['file'],
            'absolute_path': rec['absolute_path'],
            'sha256': rec['sha256'],
            'caption': rec['caption'],
            'url': rec['url'],
            'index': i,
            'operation': op,
        })

    return operations


def apply_gallery(steam: Any, update: int, records: list[dict[str, Any]]) -> None:
    """Stage gallery records via Steamworks UGC preview APIs.

    Calls AddItemPreviewFile for 'add', UpdateItemPreviewFile for 'update',
    and skips 'skip'. Raises RuntimeError if any native call returns False.
    Never calls SubmitItemUpdate or writes state.
    """
    add_fn = update_fn = None

    for rec in records:
        op = rec['operation']
        if op == 'skip':
            continue
        path_bytes = rec['absolute_path'].encode('utf-8')
        if op == 'add':
            if add_fn is None:
                add_fn = steam.bind('SteamAPI_ISteamUGC_AddItemPreviewFile', C.c_bool, C.c_void_p, C.c_uint64, C.c_char_p, C.c_int32)
            if not add_fn(steam.ugc, update, path_bytes, 0):
                raise RuntimeError(f'AddItemPreviewFile rejected: {rec["file"]}')
        elif op == 'update':
            if update_fn is None:
                update_fn = steam.bind('SteamAPI_ISteamUGC_UpdateItemPreviewFile', C.c_bool, C.c_void_p, C.c_uint64, C.c_uint32, C.c_char_p)
            if not update_fn(steam.ugc, update, rec['index'], path_bytes):
                raise RuntimeError(f'UpdateItemPreviewFile rejected: {rec["file"]}')
        else:
            raise RuntimeError(f'unknown operation: {op}')
