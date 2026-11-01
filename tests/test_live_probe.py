"""Scene-specific command channels prevent stale frontend command execution."""
import sys
import tempfile
import unittest
from pathlib import Path

from lupa.lua51 import LuaRuntime

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from live_probe import fixture
from pack import read_pack


class ProbeSceneTests(unittest.TestCase):
    def test_frontend_cannot_consume_campaign_commands_after_scene_transition(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            output = fixture(root / 'probe.pack', root / 'runtime', root / 'unused.pack', False)
            files = read_pack(output.read_bytes())
            lua = LuaRuntime()
            lua.execute('''
                core = {add_listener=function() end, add_ui_created_callback=function() end,
                    get_tm=function() return {real_callback=function() end} end}
                cm = {add_first_tick_callback=function() end}
                real_timer = {register_repeating=function() end}
            ''')
            load = lua.eval('''function(source)
                local env=setmetatable({}, {__index=_G})
                local chunk=assert(loadstring(source));setfenv(chunk,env);chunk();return env
            end''')
            frontend = load(files['script/frontend/mod/zz_xatw3_acceptance.lua'].decode())
            campaign = load(files['script/campaign/mod/zz_xatw3_acceptance.lua'].decode())
            front_tick = frontend['xatw3_test']['tick']
            campaign_tick = campaign['xatw3_test']['tick']
            # A new scene may replace the public namespace while an old timer
            # still holds its original callback. Its private channel must stay.
            frontend['xatw3_test'] = campaign['xatw3_test']
            command = root / 'runtime/command.lua'
            command.write_text("xatw3_test.record('CAMPAIGN_ONLY_EXECUTED')", encoding='utf-8')
            front_tick()
            self.assertTrue(command.exists())
            campaign_tick()
            self.assertFalse(command.exists())
            front_command = root / 'runtime/frontend-command.lua'
            front_command.write_text("xatw3_test.record('FRONTEND_ONLY_EXECUTED')", encoding='utf-8')
            campaign_tick()
            self.assertTrue(front_command.exists())
            front_tick()
            self.assertFalse(front_command.exists())
            log = (root / 'runtime/native.log').read_text(encoding='utf-8')
            self.assertEqual(log.count('CAMPAIGN_ONLY_EXECUTED'), 1)
            self.assertEqual(log.count('FRONTEND_ONLY_EXECUTED'), 1)


if __name__ == '__main__':
    unittest.main()
