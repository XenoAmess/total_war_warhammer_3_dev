"""Build a separate native-engine test fixture. Never included in release packs.

Install its movie pack explicitly, launch a disposable single-player campaign,
and write a trusted Lua command to the runtime directory. The fixture records
the actual engine result. Use dispatcher-only when loading the frozen release
pack separately; remove all test fixtures before normal play or publication.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pack import read_pack, write_pack
from project import add_mod_argument, selected_project
LUA = r'''
local root = __RUNTIME__
xatw3_test = {}
function xatw3_test.record(value)
    local f = io.open(root .. '/native.log', 'a')
    if f then f:write(tostring(value) .. '\n'); f:close() end
end
function xatw3_test.dump(value, prefix, depth)
    prefix, depth = prefix or '', depth or 0
    if type(value) ~= 'table' or depth > 5 then xatw3_test.record(prefix .. tostring(value)); return end
    for k,v in pairs(value) do xatw3_test.dump(v, prefix .. tostring(k) .. '.', depth + 1) end
end
function xatw3_test.tick()
    local f = io.open(root .. '/command.lua', 'r')
    if f then
        local code = f:read('*a'); f:close(); os.remove(root .. '/command.lua')
        local chunk, err = loadstring(code, 'xatw3_acceptance_command')
        if chunk then
            setfenv(chunk, getfenv(1))
            local ok, result = pcall(chunk)
            xatw3_test.record('COMMAND_RESULT ok=' .. tostring(ok) .. ' result=' .. tostring(result))
        else xatw3_test.record('COMMAND_COMPILE_ERROR ' .. tostring(err)) end
    end
end
'''


def fixture(output: Path, runtime: Path, production_pack: Path, include_production: bool = True) -> Path:
    runtime.mkdir(parents=True, exist_ok=True)
    script = LUA.replace('__RUNTIME__', json.dumps(runtime.resolve().as_posix()))
    campaign = script + '''
xatw3_test.record('CAMPAIGN_SCRIPTS_LOADED')
-- campaign mods load before WorldCreated constructs the timer manager.
core:add_listener('xatw3_acceptance_real', 'RealTimeTrigger',
    function(context) return context.string == 'xatw3_acceptance_campaign' end,
    xatw3_test.tick, true)
real_timer.register_repeating('xatw3_acceptance_campaign', 500)
core:add_ui_created_callback(function()
    xatw3_test.record('CAMPAIGN_UI_CREATED')
end)
cm:add_first_tick_callback(function()
    xatw3_test.record('CAMPAIGN_READY ' .. cm:get_campaign_name())
    cm:repeat_callback(xatw3_test.tick, 0.5, 'xatw3_acceptance_model')
end)
'''
    # The frontend timer can survive scene transitions. It must never consume
    # campaign commands using its stale frontend cm/core environment.
    frontend = script.replace('/command.lua', '/frontend-command.lua') + '''
_G.suppress_intro_movie = true
local function poll()
    xatw3_test.tick()
    core:get_tm():real_callback(poll, 500, 'xatw3_acceptance_frontend')
end
xatw3_test.record('FRONTEND_READY')
core:get_tm():real_callback(poll, 1000, 'xatw3_acceptance_frontend')
'''
    files = read_pack(production_pack.read_bytes()) if include_production else {}
    files.update({
        'script/campaign/mod/zz_xatw3_acceptance.lua': campaign.encode(),
        'script/frontend/mod/zz_xatw3_acceptance.lua': frontend.encode()
    })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(write_pack(files, pack_type=4))
    return output


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    add_mod_argument(p)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--output', type=Path)
    p.add_argument('--production-pack', type=Path)
    p.add_argument('--dispatcher-only', action='store_true', help='Load production through the real mod pack separately')
    args = p.parse_args()
    project = selected_project(p, args.mod)
    print(fixture(args.output or project.build_dir / 'zz_xatw3_acceptance.pack', args.runtime,
                  args.production_pack or project.pack_path, not args.dispatcher_only))
