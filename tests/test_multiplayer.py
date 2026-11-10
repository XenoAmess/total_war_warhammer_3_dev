"""Ordered broadcast simulations, not native multiplayer acceptance."""
from collections import deque
from pathlib import Path
import unittest

from lupa.lua51 import LuaRuntime

SOURCE = (Path(__file__).resolve().parents[1] / 'tools/lua/multiplayer.lua').read_text(encoding='utf-8')


class World:
    def __init__(self, count=2):
        self.queue, self.events = deque(), []
        self.peers = []
        self.members = ['player_' + str(i) for i in range(count)]
        for name in self.members:
            lua = LuaRuntime(unpack_returned_tuples=True)
            lua.globals().transport = lua.execute(SOURCE)
            lua.globals().emit = lambda packet, sender=name: self.queue.append((sender, packet))
            lua.globals().player = name
            lua.globals().roster = lua.table_from(self.members)
            lua.execute('''
                persisted = {}; mutations = 0; results = {}; deferred = false
                snapshot = 'same'; after_snapshot = 'after'; allowed = true
                bus = transport.new({local_faction = function() return player end,
                    members = function() return roster end,
                    persist = function(s) persisted = s end,
                    send = function(p) emit(p) end})
                handler = {check = function()
                        if check_error then error('check failed') end
                        return allowed, snapshot
                    end,
                    prepare = function(_, done)
                        if prepare_error then error('prepare failed') end
                        if deferred then ready = done else done(allowed, snapshot) end
                    end,
                    execute = function()
                        assert(persisted.pending, 'No journal before mutation')
                        mutations = mutations + 1
                        if execute_error then error('native failed') end
                        return {status = 'SUCCEEDED'}
                    end,
                    after = function() return after_snapshot end,
                    release = function() releases = (releases or 0) + 1 end,
                    result = function(r) results[#results + 1] = r end}
                bus.handlers.refresh = handler; bus.handlers.capital = handler
                function submit(owner)
                    return bus.submit(owner or 'refresh', {action = 'refresh', faction = player,
                        turn = 3, target = 'general', expected = expected or 'before'})
                end
            ''')
            self.peers.append(lua)

    def deliver(self, event=None):
        sender, packet = event or self.queue.popleft()
        # Observed native SP UITrigger ceiling on game 9.0.5. This harness must
        # not silently allow packets the actual engine would truncate.
        packet = packet[:256]
        self.events.append((sender, packet))
        for peer in self.peers:
            peer.globals().bus.receive(sender, packet)

    def drain(self):
        for _ in range(10000):
            if not self.queue:
                return
            self.deliver()
        raise AssertionError('Unbounded broadcast')

    def values(self, expression):
        return [peer.eval(expression) for peer in self.peers]


class MultiplayerTests(unittest.TestCase):
    def test_real_refresh_runtime_waits_for_both_panels_then_replaces_and_grows(self):
        w = World()
        folder = Path(__file__).resolve().parents[1] / 'mods/recruitment_refresh/src/script/campaign/xatw3_campaign_utilities'
        for peer in w.peers:
            peer.globals().logic = peer.execute((folder / 'logic.lua').read_text(encoding='utf-8'))
            peer.globals().runtime_module = peer.execute((folder / 'runtime.lua').read_text(encoding='utf-8'))
            peer.execute('''
                package.loaded['script.xatw3_multiplayer'] = transport
                package.loaded['script.xatw3_transport_identity'] = 'transport-digest'
                package.loaded['script.xatw3_release_recruitment_refresh'] = 'same-release'
                package.loaded['script.campaign.xatw3_campaign_utilities.native_pool'] = {
                    new=function() return {initialize=function() return true end, build='verified'} end}
                local values, timers = {}, {}
                panel_visible=true; close_calls=0
                local faction = {is_human=function() return true end,
                    is_factions_turn=function() return true end}
                local cm = {get_saved_value=function(_,k) return values[k] end,
                    set_saved_value=function(_,k,v) values[k]=v end,
                    get_campaign_name=function() return 'main_warhammer' end,
                    is_multiplayer=function() return true end,
                    get_local_faction_name=function() return player end,
                    get_faction=function(_,k) if k=='player_0' then return faction end end,
                    callback=function(_,fn) timers[#timers+1]=fn end,
                    model=function() return {turn_number=function() return 3 end,
                        pending_battle=function() return {is_active=function() return false end} end} end}
                local ui = {ClosePanel=function() close_calls=close_calls+1 end,
                    CloseCurrentHUDPanel=function() end}
                local core = {get_ui_root=function() return {} end, add_listener=function() end}
                local env = {cm=cm, core=core, CampaignUI=ui, out=function() end,
                    find_uicomponent=function() return {Visible=function() return panel_visible end} end}
                rt=runtime_module.new(logic,env); rt.initialize()
                local function candidate(id)
                    return {id=id, faction='player_0', subtype='general', in_pool=true,
                        provenance='ordinary_generated', male=true, recruited=false, wounded=false}
                end
                pool={candidate(1)}
                rt.supported=function(subtype, faction_key)
                    assert(subtype=='general' and faction_key=='player_0')
                    rt.subtypes.general='general'; return true
                end
                rt.read_pool=function()
                    local copy={}; for i,c in ipairs(pool) do copy[i]=c end; return copy
                end
                rt.can_remove_candidate=function() return not panel_visible end
                rt.spawn_candidate=function()
                    assert(rt.multiplayer_executing and persisted.pending and not panel_visible)
                    assert(rt.state.last.status=='EXECUTING')
                    mutations=mutations+1; local c=candidate(100+mutations)
                    pool[#pool+1]=c; return c
                end
                rt.verify_candidate=function() return true end
                rt.remove_candidate=function(id)
                    local copy={}; for _,c in ipairs(pool) do if c.id~=id then copy[#copy+1]=c end end
                    pool=copy; return true
                end
                transport.bus=bus; transport.manager=cm; rt.install_multiplayer()
                rt.on_result=function(r) results[#results+1]=r end
                function tick()
                    local todo=timers; timers={}; for _,fn in ipairs(todo) do fn() end
                end
                function submit_refresh()
                    return bus.submit('xatw3_campaign_utilities', {action='refresh', faction=player,
                        turn=3, target='general', expected=logic.fingerprint(pool)})
                end
            ''')
        self.assertTrue(w.peers[0].globals().submit_refresh()); w.drain()
        self.assertEqual(w.values('mutations'), [0, 0])
        w.peers[0].execute('panel_visible=false; tick()'); w.drain()
        self.assertEqual(w.values('mutations'), [0, 0])
        w.peers[1].execute('tick(); panel_visible=false; tick()'); w.drain()
        self.assertEqual(w.values('mutations'), [3, 3])
        self.assertEqual(w.values('#pool'), [3, 3])
        self.assertEqual(w.values('rt.state.last.status'), ['SUCCEEDED', 'SUCCEEDED'])
        self.assertEqual(w.values('rt.state.last.added'), [2, 2])
        self.assertEqual(w.values('#results'), [1, 0])

    def test_real_capital_runtime_executes_on_remote_peer_via_engine_adapter(self):
        w = World()
        folder = Path(__file__).resolve().parents[1] / 'mods/move_capital/src/script/campaign/xatw3_move_capital'
        for peer in w.peers:
            peer.globals().logic = peer.execute((folder / 'logic.lua').read_text(encoding='utf-8'))
            peer.globals().runtime_module = peer.execute((folder / 'runtime.lua').read_text(encoding='utf-8'))
            peer.execute('''
                package.loaded['script.xatw3_multiplayer'] = transport
                package.loaded['script.xatw3_transport_identity'] = 'transport-digest'
                package.loaded['script.xatw3_release_move_capital'] = 'same-release-digest'
                local home = 'old_home'
                local faction = {is_human=function() return true end,
                    is_factions_turn=function() return true end,
                    has_home_region=function() return true end,
                    home_region=function() return {name=function() return home end} end}
                local region = {is_null_interface=function() return false end,
                    owning_faction=function() return {name=function() return 'player_0' end} end,
                    settlement=function() return {is_null_interface=function() return false end,
                        primary_slot=function() return {building=function() return {
                            building_level=function() return 2 end} end} end} end,
                    is_abandoned=function() return false end,
                    is_province_capital=function() return false end,
                    garrison_residence=function() return {is_under_siege=function() return false end} end}
                local values = {}
                local cm = {get_saved_value=function(_, k) return values[k] end,
                    set_saved_value=function(_,k,v) values[k]=v end,
                    get_campaign_name=function() return 'main_warhammer' end,
                    is_multiplayer=function() return true end,
                    get_local_faction_name=function() return player end,
                    get_faction=function(_, k) if k=='player_0' then return faction end end,
                    get_region=function() return region end,
                    model=function() return {turn_number=function() return 3 end,
                        pending_battle=function() return {is_active=function() return false end} end} end,
                    change_home_region_of_faction=function()
                        assert(persisted.pending)
                        assert(values.xatw3_move_capital_state.last.status=='EXECUTING')
                        mutations=mutations+1; home='new_home'
                    end}
                local env={cm=cm, core={}, CampaignUI={}, out=function() end}
                rt=runtime_module.new(logic,env); rt.initialize()
                transport.bus=bus; transport.manager=cm
                rt.install_multiplayer()
                rt.on_result=function(r) results[#results+1]=r end
            ''')
        self.assertTrue(w.peers[0].execute("return bus.submit('xatw3_move_capital', {action='capital', faction=player, turn=3, target='new_home', expected='old_home'})"))
        w.drain()
        self.assertEqual(w.values('mutations'), [1, 1])
        self.assertEqual(w.values('rt.state.next_sequence'), [2, 2])
        self.assertEqual(w.values('#results'), [1, 0])
        self.assertEqual(w.values('rt.capital("player_0")'), ['new_home', 'new_home'])

    def test_every_peer_executes_once_and_replay_is_ignored(self):
        w = World(3)
        self.assertTrue(w.peers[0].globals().submit())
        w.drain()
        self.assertEqual(w.values('mutations'), [1, 1, 1])
        for event in list(w.events):
            w.deliver(event)
        w.drain()
        self.assertEqual(w.values('mutations'), [1, 1, 1])
        self.assertEqual(w.values('bus.available()'), [True] * 3)

    def test_no_model_write_until_slowest_ready(self):
        w = World()
        w.peers[1].execute('deferred = true')
        w.peers[0].globals().submit(); w.drain()
        self.assertEqual(w.values('mutations'), [0, 0])
        w.peers[1].execute('ready(true, snapshot)'); w.drain()
        self.assertEqual(w.values('mutations'), [1, 1])

    def test_different_snapshot_or_negative_vote_aborts_all(self):
        for change in ("snapshot='different-pack-or-pool'", 'allowed=false', 'prepare_error=true', 'check_error=true'):
            with self.subTest(change=change):
                w = World(); w.peers[1].execute(change)
                w.peers[0].globals().submit(); w.drain()
                self.assertEqual(w.values('mutations'), [0, 0])
                self.assertEqual(w.values('results[1].status'), ['REJECTED'] * 2)

    def test_simultaneous_different_mod_requests_serialize(self):
        w = World()
        w.peers[0].globals().submit('refresh'); w.peers[1].globals().submit('capital')
        w.drain()
        self.assertEqual(w.values('mutations'), [1, 1])
        self.assertEqual(w.values("persisted.counters['capital:player_1']"), [1, 1])
        self.assertTrue(w.peers[1].globals().submit('capital')); w.drain()
        self.assertEqual(w.values('mutations'), [2, 2])

    def test_result_mismatch_or_native_error_locks_every_peer(self):
        for change in ("after_snapshot='different'", 'execute_error=true'):
            with self.subTest(change=change):
                w = World(); w.peers[1].execute(change)
                w.peers[0].globals().submit(); w.drain()
                self.assertEqual(w.values('persisted.blocked'), [True, True])
                self.assertEqual(w.values('bus.available()'), [False, False])
                self.assertFalse(w.peers[0].globals().submit())

    def test_missing_mod_never_commits(self):
        w = World(); w.peers[1].execute('bus.handlers.refresh=nil')
        w.peers[0].globals().submit(); w.drain()
        self.assertEqual(w.values('mutations'), [0, 0])
        self.assertFalse(w.peers[0].eval('bus.available()'))

    def test_cancel_before_commit_is_broadcast(self):
        w = World(); w.peers[1].execute('deferred=true')
        w.peers[0].globals().submit(); w.drain()
        w.peers[0].execute('bus.cancel()'); w.drain()
        self.assertEqual(w.values('mutations'), [0, 0])
        self.assertEqual(w.values('bus.available()'), [True, True])
        w.peers[1].execute('ready(true, snapshot)'); w.drain()
        self.assertEqual(w.values('mutations'), [0, 0])

    def test_roster_changes_fail_closed(self):
        w = World(); w.peers[1].execute('deferred=true')
        w.peers[0].globals().submit(); w.drain()
        for p in w.peers:
            p.execute("roster={'player_0','replacement'}")
        w.peers[1].execute('ready(true, snapshot)'); w.drain()
        self.assertEqual(w.values('mutations'), [0, 0])
        self.assertEqual(w.values('persisted.blocked'), [True, True])

    def test_large_exact_snapshots_are_fragmented_and_reassembled(self):
        w = World()
        for p in w.peers:
            p.execute("snapshot=string.rep('state|', 1800); after_snapshot=snapshot; expected=snapshot")
        self.assertTrue(w.peers[0].globals().submit()); w.drain()
        self.assertEqual(w.values('mutations'), [1, 1])
        self.assertTrue(any(p.startswith('xatw3frag|1|') for _, p in w.events))
        self.assertTrue(all(len(p) <= 240 for _, p in w.events))

    def test_missing_fragment_and_foreign_sender_cannot_commit(self):
        w = World()
        for p in w.peers:
            p.execute("snapshot=string.rep('pool', 2000); expected=snapshot")
        w.peers[0].globals().submit()
        dropped = w.queue.popleft()
        w.drain()
        self.assertEqual(w.values('mutations'), [0, 0])
        w.deliver(('outsider', dropped[1])); w.drain()
        self.assertEqual(w.values('mutations'), [0, 0])
        w.deliver(dropped); w.drain()
        self.assertEqual(w.values('mutations'), [1, 1])

    def test_interrupted_load_and_old_epoch_do_not_replay(self):
        w = World(); w.peers[1].execute('deferred=true')
        w.peers[0].globals().submit(); w.drain()
        for p in w.peers:
            p.execute('''bus = transport.new({persist=function(s) persisted=s end,
                members=function() return roster end, local_faction=function() return player end,
                send=function(p) emit(p) end}, persisted); bus.handlers.refresh=handler''')
        for event in list(w.events):
            w.deliver(event)
        w.drain()
        self.assertEqual(w.values('mutations'), [0, 0])
        self.assertEqual(w.values('persisted.blocked'), [True, True])


if __name__ == '__main__':
    unittest.main()
