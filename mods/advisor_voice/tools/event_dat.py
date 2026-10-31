from dataclasses import dataclass
from typing import Tuple
import struct
import io


@dataclass(frozen=True)
class DatEvent:
    name: str
    value: float


@dataclass(frozen=True)
class StateGroup:
    name: str
    states: Tuple[str, ...]


@dataclass(frozen=True)
class DialogueEvent:
    name: str
    groups: Tuple[int, ...]


@dataclass(frozen=True)
class Setting:
    name: str
    minimum: float
    maximum: float


@dataclass(frozen=True)
class SoundDat:
    events: Tuple[DatEvent, ...]
    state_groups_0: Tuple[StateGroup, ...]
    state_groups_1: Tuple[StateGroup, ...]
    dialogue_events: Tuple[DialogueEvent, ...]
    settings: Tuple[Setting, ...]
    unknown: Tuple[str, ...]


def _read_u32(chunk: io.BytesIO) -> int:
    data = chunk.read(4)
    if len(data) != 4:
        raise ValueError("Truncated data: expected u32")
    return struct.unpack('<I', data)[0]

def _read_i32(chunk: io.BytesIO) -> int:
    data = chunk.read(4)
    if len(data) != 4:
        raise ValueError("Truncated data: expected i32")
    return struct.unpack('<i', data)[0]

def _read_float(chunk: io.BytesIO) -> float:
    data = chunk.read(4)
    if len(data) != 4:
        raise ValueError("Truncated data: expected float")
    return struct.unpack('<f', data)[0]

def _read_str32(chunk: io.BytesIO) -> str:
    length = _read_i32(chunk)
    if length < 0:
        raise ValueError("Invalid string length: negative")
    if length == 0:
        return ""
    data = chunk.read(length)
    if len(data) != length:
        raise ValueError("Truncated data: expected string bytes")
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        raise ValueError("Invalid UTF-8 string")

def _read_state_group(chunk: io.BytesIO) -> StateGroup:
    name = _read_str32(chunk)
    count = _read_u32(chunk)
    states = []
    for _ in range(count):
        states.append(_read_str32(chunk))
    return StateGroup(name=name, states=tuple(states))

def _read_dialogue_event(chunk: io.BytesIO) -> DialogueEvent:
    name = _read_str32(chunk)
    count = _read_u32(chunk)
    groups = []
    for _ in range(count):
        groups.append(_read_u32(chunk))
    return DialogueEvent(name=name, groups=tuple(groups))

def _read_setting(chunk: io.BytesIO) -> Setting:
    name = _read_str32(chunk)
    min_val = _read_float(chunk)
    max_val = _read_float(chunk)
    return Setting(name=name, minimum=min_val, maximum=max_val)

def parse_dat(data: bytes) -> SoundDat:
    chunk = io.BytesIO(data)

    # Section 0: EventWithStateGroup
    section_zero_count = _read_u32(chunk)
    events = []
    for _ in range(section_zero_count):
        name = _read_str32(chunk)
        value = _read_float(chunk)
        events.append(DatEvent(name=name, value=value))

    # Section 1: StateGroupsWithStates0
    section_one_count = _read_i32(chunk)
    if section_one_count < 0:
        raise ValueError("Invalid count: negative")
    state_groups_0 = []
    for _ in range(section_one_count):
        state_groups_0.append(_read_state_group(chunk))

    # Section 2: StateGroupsWithStates1
    section_two_count = _read_i32(chunk)
    if section_two_count < 0:
        raise ValueError("Invalid count: negative")
    state_groups_1 = []
    for _ in range(section_two_count):
        state_groups_1.append(_read_state_group(chunk))

    # Section 3: DialogueEventsWithStateGroups
    section_three_count = _read_i32(chunk)
    if section_three_count < 0:
        raise ValueError("Invalid count: negative")
    dialogue_events = []
    for _ in range(section_three_count):
        dialogue_events.append(_read_dialogue_event(chunk))

    # Section 4: SettingValues (WH3 format, not Atilla)
    section_four_count = _read_i32(chunk)
    if section_four_count < 0:
        raise ValueError("Invalid count: negative")
    settings = []
    for _ in range(section_four_count):
        settings.append(_read_setting(chunk))

    # Section 5: Unknown
    section_five_count = _read_i32(chunk)
    if section_five_count < 0:
        raise ValueError("Invalid count: negative")
    unknown = []
    for _ in range(section_five_count):
        unknown.append(_read_str32(chunk))

    # Check for trailing bytes
    if chunk.read(1):
        raise ValueError("Trailing bytes found")

    return SoundDat(
        events=tuple(events),
        state_groups_0=tuple(state_groups_0),
        state_groups_1=tuple(state_groups_1),
        dialogue_events=tuple(dialogue_events),
        settings=tuple(settings),
        unknown=tuple(unknown)
    )
