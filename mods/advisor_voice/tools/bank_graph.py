"""A strict adapter over WWiser's parsed AST, limited to known playback edges.

WWiser is an external, explicitly supplied source checkout. Unknown object kinds
remain unresolved; parent, bus, attenuation and bank IDs are never child edges.
"""
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Iterator, Mapping, Protocol


@dataclass(frozen=True)
class AudioNode:
    object_id: int
    kind: str
    bank: str
    targets: tuple[int, ...] = ()
    media_id: int | None = None
    stream_type: int | None = None
    plugin_id: int | None = None


@dataclass(frozen=True)
class Resolution:
    media_ids: tuple[int, ...]
    missing_node_ids: tuple[int, ...]
    unsupported_kinds: tuple[str, ...]
    cycle_ids: tuple[int, ...]


class AstNode(Protocol):
    def get_attr(self, name: str) -> object: ...
    def get_name(self) -> str: ...
    def get_nodename(self) -> str: ...
    def get_children(self) -> list['AstNode'] | None: ...


def _fields(node: AstNode) -> Iterator[AstNode]:
    if node.get_nodename() == 'field':
        yield node
    for child in node.get_children() or []:
        yield from _fields(child)


def _numbers(node: AstNode, name: str) -> tuple[int, ...]:
    result = []
    for field in _fields(node):
        if field.get_name() == name:
            value = field.get_attr('value')
            if type(value) is not int:
                raise ValueError(f'Expected integer AST field: {name}')
            result.append(value)
    return tuple(sorted(set(result)))


def _one(node: AstNode, name: str) -> int:
    values = _numbers(node, name)
    if len(values) != 1:
        raise ValueError(f'Expected exactly one {name} field')
    return values[0]


def index_bank(path: Path, wwiser_root: Path) -> dict[int, AudioNode]:
    sys.path.insert(0, str(wwiser_root.resolve()))
    from wwiser.parser import wparser
    parser = wparser.Parser()
    parser.parse_bank(str(path))
    banks = parser.get_banks(mode=parser.MULTIBANK_MANUAL)
    if len(banks) != 1:
        raise ValueError(f'Expected one parsed bank: {path}')
    bank = banks[0]
    if bank.get_error_count() or bank.get_skip_count():
        raise ValueError(f'WWiser errors={bank.get_error_count()}, skips={bank.get_skip_count()}')
    objects = bank.find(name='listLoadedItem')
    if objects is None:
        raise ValueError(f'No HIRC object list: {path}')
    result = {}
    for obj in objects.get_children() or []:
        direct_ids = [child.get_attr('value') for child in obj.get_children() or []
                      if child.get_nodename() == 'field' and child.get_name() == 'ulID']
        if len(direct_ids) != 1 or type(direct_ids[0]) is not int:
            raise ValueError('Expected one direct object ID')
        object_id, kind = direct_ids[0], obj.get_name()
        if object_id in result:
            raise ValueError(f'Duplicate HIRC ID: {object_id}')
        field = {'CAkEvent': 'ulActionID', 'CAkActionPlay': 'idExt',
                 'CAkRanSeqCntr': 'ulChildID', 'CAkActorMixer': 'ulChildID'}.get(kind)
        targets = _numbers(obj, field) if field else ()
        sound = kind == 'CAkSound'
        result[object_id] = AudioNode(object_id, kind, str(path), targets,
                                      _one(obj, 'sourceID') if sound else None,
                                      _one(obj, 'StreamType') if sound else None,
                                      _one(obj, 'ulPluginID') if sound else None)
    return result


def resolve_event(event_id: int, nodes: Mapping[int, AudioNode]) -> Resolution:
    media: set[int] = set()
    missing: set[int] = set()
    unsupported: set[str] = set()
    cycles: set[int] = set()
    visited: set[int] = set()
    path: list[int] = []
    active: set[int] = set()

    def visit(key: int) -> None:
        if key in active:
            cycles.update(path[path.index(key):])
            return
        if key in visited:
            return
        if key not in nodes:
            missing.add(key)
            return
        node = nodes[key]
        active.add(key)
        path.append(key)
        if node.kind == 'CAkSound':
            if node.media_id is None:
                unsupported.add('CAkSound:missing_sourceID')
            else:
                media.add(node.media_id)
        elif node.kind == 'CAkActionStop':
            pass  # A known control action, with no playable media of its own.
        elif node.kind in ('CAkEvent', 'CAkActionPlay', 'CAkRanSeqCntr', 'CAkActorMixer'):
            for target in node.targets:
                visit(target)
        else:
            unsupported.add(node.kind)
        path.pop()
        active.remove(key)
        visited.add(key)

    visit(event_id)
    return Resolution(tuple(sorted(media)), tuple(sorted(missing)),
                      tuple(sorted(unsupported)), tuple(sorted(cycles)))
