"""Run the production business module with Lua 5.1, then check packaged resources."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lupa.lua51 import LuaRuntime

from build import ROOT, build
from pack import read_pack, read_translations


def run() -> dict:
    lua = LuaRuntime(unpack_returned_tuples=True)
    compile_lua = lua.eval('function(source, name) local f,e=loadstring(source,name); if not f then error(e) end; return true end')
    sources = sorted((ROOT / 'mod').rglob('*.lua'))
    for path in sources:
        compile_lua(path.read_text(encoding='utf-8'), path.relative_to(ROOT).as_posix())
    lua.globals().logic = lua.execute((ROOT / 'mod/script/campaign/xatw3_campaign_utilities/logic.lua').read_text(encoding='utf-8'))
    tests = list(lua.execute((ROOT / 'tests/test_logic.lua').read_text(encoding='utf-8')).values())
    first = build()
    raw = (ROOT / 'build' / first['pack']).read_bytes()
    second = build()
    if first != second:
        raise RuntimeError('Build is not deterministic')
    files = read_pack(raw)
    if any('test' in key or 'acceptance' in key for key in files):
        raise RuntimeError('Test fixture included in release')
    rows = read_translations(ROOT / 'localisation/zh-CN.tsv')
    import re
    ui = (ROOT / 'mod/script/campaign/xatw3_campaign_utilities/ui.lua').read_text(encoding='utf-8')
    for key in re.findall(r"text\('([^']+)'\)", ui):
        if 'xatw3_' + key not in rows:
            raise RuntimeError('Missing localisation: ' + key)
    result = {'status': 'PASS', 'lua_version': lua.lua_version, 'compiled_lua_files': len(sources),
              'production_logic_tests': tests, 'test_count': len(tests),
              'deterministic_build': True, 'pack_round_trip': True,
              'release_pack_sha256': hashlib.sha256(raw).hexdigest(), 'release_pack_bytes': len(raw),
              'native_game_acceptance': 'NOT_RUN'}
    (ROOT / 'build/offline-test-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
