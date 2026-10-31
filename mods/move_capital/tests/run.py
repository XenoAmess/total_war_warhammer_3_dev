"""Run the independent Move Capital modules under Lua 5.1."""
from pathlib import Path
import hashlib
import json
import re
import sys
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / 'tools'))
from build import build
from pack import read_pack, read_translations
from project import load_project


def run():
    project = load_project(ROOT.name)
    lua = LuaRuntime(unpack_returned_tuples=True)
    compile_lua = lua.eval('function(s,n) assert(loadstring(s,n)); return true end')
    sources = sorted(project.source_dir.rglob('*.lua'))
    for path in sources:
        compile_lua(path.read_text(encoding='utf-8'), str(path))
    folder = project.source_dir / 'script/campaign/xatw3_move_capital'
    lua.globals().logic = lua.execute((folder / 'logic.lua').read_text(encoding='utf-8'))
    lua.globals().runtime_module = lua.execute((folder / 'runtime.lua').read_text(encoding='utf-8'))
    lua.globals().ui_module = lua.execute((folder / 'ui.lua').read_text(encoding='utf-8'))
    tests = {}
    for name in ('logic', 'runtime', 'ui'):
        tests[name] = list(lua.execute((ROOT / f'tests/test_{name}.lua').read_text(encoding='utf-8')).values())
    # Exercise the actual entry parser, including its exact channel prefix length.
    entry = LuaRuntime(unpack_returned_tuples=True)
    entry.globals().entry_source = (project.source_dir / 'script/campaign/mod/xatw3_move_capital.lua').read_text(encoding='utf-8')
    entry.execute('''
        local sent, listener = {}, nil
        local rt = {execute = function(r) sent[#sent+1] = r end}
        require = function(name)
            if name:match('runtime$') then return {new = function() return rt end} end
            if name:match('ui$') then return {new = function() return {} end} end
            return {}
        end
        core = {add_listener = function(_,n,e,condition,callback) listener = {condition,callback} end}
        cm = {add_first_tick_callback = function() end,
            get_local_faction_name = function() return 'player' end,
            get_local_faction = function() return {command_queue_index = function() return 17 end} end}
        assert(loadstring(entry_source))()
        local context = {trigger = function() return 'xatw3mc|1|capital|1|3|new_home|old_home' end,
            faction_cqi = function() return 17 end}
        assert(listener[1](context), 'New capital UI channel never reaches its listener')
        listener[2](context); assert(#sent == 1 and sent[1].target == 'new_home')
        context.trigger = function() return 'xatw3mc|1|refresh|2|3|new_home|old_home' end
        listener[2](context); assert(#sent == 1)
        context.trigger = function() return 'xatw3mc|1|capital|2|3|new_home|old_home' end
        context.faction_cqi = function() return 99 end
        listener[2](context); assert(#sent == 1)
    ''')
    tests['entry'] = ['new_channel_dispatches_capital', 'refresh_action_rejected', 'wrong_faction_rejected']
    first = build(project)
    assert build(project) == first
    raw = project.pack_path.read_bytes()
    files = read_pack(raw)
    assert len(files) == 5 and not project.required_items
    assert not any('xatw3_campaign_utilities' in path or 'acceptance' in path or 'test' in path for path in files)
    assert not any('native_pool' in content.decode('utf-8') or 'spawn_character_to_pool' in content.decode('utf-8') for path, content in files.items() if path.endswith('.lua'))
    rows = read_translations(ROOT / 'localisation/zh-CN.tsv')
    for key in re.findall(r"text\('([^']+)'\)", (folder / 'ui.lua').read_text(encoding='utf-8')) + ['capital', 'capital_tooltip']:
        assert 'xatw3mc_' + key in rows, key
    result = dict(status='PASS', mod_id=project.id, lua_version=lua.lua_version,
                  compiled_lua_files=len(sources), tests=tests, test_count=sum(map(len, tests.values())),
                  no_native_dependency=True, deterministic_build=True, pack_round_trip=True,
                  release_pack_sha256=hashlib.sha256(raw).hexdigest(), release_pack_bytes=len(raw), native_game_acceptance='NOT_RUN')
    (project.build_dir / 'offline-test-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
