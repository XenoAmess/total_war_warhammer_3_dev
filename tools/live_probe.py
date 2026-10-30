"""Build a separate native-engine test fixture. Never included in release packs.

Install its movie pack explicitly, launch a disposable single-player campaign,
and write a trusted Lua command to the runtime directory. The fixture records
the actual engine result. Remove the fixture before testing the release pack.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pack import read_pack, write_pack

ROOT = Path(__file__).resolve().parents[1]
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
            local ok, result = pcall(chunk)
            xatw3_test.record('COMMAND_RESULT ok=' .. tostring(ok) .. ' result=' .. tostring(result))
        else xatw3_test.record('COMMAND_COMPILE_ERROR ' .. tostring(err)) end
    end
end
'''


def fixture(output: Path, runtime: Path, production_pack: Path) -> Path:
    runtime.mkdir(parents=True, exist_ok=True)
    script = LUA.replace('__RUNTIME__', json.dumps(runtime.resolve().as_posix()))
    campaign = script + '''
cm:add_first_tick_callback(function()
    xatw3_test.record('CAMPAIGN_READY ' .. cm:get_campaign_name())
    cm:repeat_callback(xatw3_test.tick, 0.5, 'xatw3_acceptance_poll')
end)
'''
    frontend = script + '''
local function poll()
    xatw3_test.tick()
    core:get_tm():real_callback(poll, 500, 'xatw3_acceptance_frontend')
end
xatw3_test.record('FRONTEND_READY')
core:get_tm():real_callback(poll, 1000, 'xatw3_acceptance_frontend')
'''
    files = read_pack(production_pack.read_bytes())
    files.update({
        'script/campaign/mod/zz_xatw3_acceptance.lua': campaign.encode(),
        'script/frontend/mod/zz_xatw3_acceptance.lua': frontend.encode()
    })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(write_pack(files, pack_type=4))
    return output


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--output', type=Path, default=ROOT / 'build/zz_xatw3_acceptance.pack')
    p.add_argument('--production-pack', type=Path, default=ROOT / 'build/xatw3_campaign_utilities.pack')
    args = p.parse_args()
    print(fixture(args.output, args.runtime, args.production_pack))
