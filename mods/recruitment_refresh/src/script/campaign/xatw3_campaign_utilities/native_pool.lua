-- Uses the engine's own candidate expiry cleanup, followed by its vector cleanup.
-- No object bytes, names, skill trees, or allocator-owned pointers are written by Lua.
-- The signatures and layouts below were verified on WH3 9.0.4/9.0.5, Windows x64.
local M = {}
local policy = require('script.campaign.xatw3_campaign_utilities.recruitment_policy')

local EXPIRY = '48 89 5C 24 18 88 54 24 10 55 56 57 41 54 41 55 41 56 41 57 '
    .. '48 83 EC 30 48 8B 01 0F 57 C0 48 8B F9 4C 8B 80 A8 03 00 00 '
    .. '4D 8B A8 90 00 00 00 F3 4D 0F 2C B5 D8 69 00 00'
local PURGE = '48 8B C4 48 89 58 08 48 89 68 10 48 89 70 18 48 89 78 20 '
    .. '41 54 41 56 41 57 48 83 EC 20 4C 8B F1 48 8B F2 48 8B 0A 48 85 C9'
local NULL = string.rep('\0', 8)
-- Exact PE timestamp + SizeOfImage bytes, read without float conversion.
-- A matching function signature alone does not qualify object layouts.
local BUILDS = {
    ['\244\198\206\106\0\144\2\14'] = '9.0.4.0',
    ['\11\160\226\106\0\160\83\14'] = '9.0.5.0'
}

-- Exact 9.0.5 skill initialization route; ordinary pool support is independent.
local BACKGROUND_SIGNATURE = '48 89 5C 24 08 48 89 6C 24 10 48 89 74 24 18 57 41 54 41 55 41 56 41 57 48 83 EC 50 45 8A E1 4D 8B F8 4C 8B F2 4C 8B E9'
local BACKGROUND_CODE = '\072\137\092\036\008\072\137\108\036\016\072\137\116\036\024\087\065\084\065\085\065\086\065\087\072\131\236\080\069\138\225\077\139\248\076\139\242\076\139\233\232\023\033\183\253\232\014\030\189\253\072\139\216\232\010\033\183\253\232\001\030\189\253\072\139\248\051\237\073\139\134\168\003\000\000\072\139\176\224\000\000\000\072\139\118\016\077\137\125\056\073\057\174\136\013\000\000\116\031\073\139\206\232\197\182\210\255\073\139\206\072\139\088\008\232\185\182\210\255\072\139\184\024\003\000\000\072\139\127\008\073\139\142\168\003\000\000\076\139\206\073\139\151\248\001\000\000\073\139\135\240\001\000\000\064\136\108\036\056\076\139\129\160\000\000\000\072\139\082\008\072\139\064\008\064\136\108\036\048\073\139\072\032\076\139\199\072\137\084\036\040\072\139\211\072\137\068\036\032\232\040\198\255\255\072\139\232\065\198\069\097\001\232\103\029\189\253\073\139\150\136\013\000\000\076\139\203\072\137\068\036\064\076\139\197\198\068\036\056\000\073\139\205\068\136\100\036\048\072\137\116\036\040\072\137\124\036\032\232\085\250\255\255\073\139\135\248\001\000\000\076\141\092\036\080\073\139\091\048\073\139\107\056\073\139\115\064\138\136\204\001\000\000\065\136\077\096\073\139\227\065\095\065\094\065\093\065\092\095\195'
local BACKGROUND_NESTED = '\072\139\196\076\137\072\032\076\137\064\024\072\137\080\016\072\137\072\008\085\083\086\087\065\084\065\085\065\086\065\087\072\141\104\185\072\129\236\184\000\000\000\069\051\228\073\139\249\077\139\240\072\139\241\068\056\101\127\116\024\232\131\192\253\255\072\141\078\024\232\102\096\228\253\076\137\102\064\068\137\102\076\235\014\068\056\165\135\000\000\000\116\005\232\098\192\253\255'
local BACKGROUND_CLEAR = '\072\137\092\036\008\072\137\116\036\016\087\072\131\236\032\139\121\004\072\139\241\072\139\089\008\072\193\231\004\072\003\251\235\012\072\139\203\232\182\072\054\255\072\131\195\016\072\059\223\117\239\131\102\004\000\072\139\116\036\056\072\139\092\036\048\072\131\196\032\095\195'

function M.new(environment)
    environment = environment or getfenv(2)
    local globals = environment._G or _G
    local mr = globals.memreader_plus
    local self = {ready = false, reason = 'native_dependency_missing'}
    local functions
    local background_initializer

    local function nonnull(pointer)
        return pointer and not mr.eq(pointer, NULL)
    end

    local function checked_call_target(caller, offset)
        local site = mr.add(caller, offset)
        assert(mr.read_uint8(site, 0) == 0xe8, 'native call layout changed')
        local displacement = mr.read_int32(site, 1)
        -- Lua numbers in WH3 are single precision. These calls are nearby;
        -- reject a displacement that cannot be represented exactly.
        assert(math.abs(displacement) < 16777210, 'native call out of range')
        return mr.add(site, displacement + 5)
    end

    function self.initialize()
        if functions then return self.ready end
        if type(mr) ~= 'table' or type(mr.call) ~= 'function' or type(mr.find_pattern) ~= 'function'
            or type(mr.ud_topointer) ~= 'function' then return false end
        local identified, build = pcall(function()
            assert(mr.base and mr.read(mr.base, 0, 2) == 'MZ')
            local pe = mr.read_uint32(mr.base, 0x3c)
            assert(type(pe) == 'number' and pe >= 64 and pe <= 4096 and pe == math.floor(pe))
            assert(mr.read(mr.base, pe, 4) == 'PE\0\0')
            return BUILDS[mr.read(mr.base, pe + 8, 4) .. mr.read(mr.base, pe + 80, 4)]
        end)
        if not identified or not build then self.reason = 'native_build_unverified'; return false end
        self.build = build
        local ok, result = pcall(function()
            local expiry, expiry_count = mr.find_pattern(EXPIRY)
            local purge, purge_count = mr.find_pattern(PURGE)
            assert(expiry_count == 1 and purge_count == 1, 'native signatures changed')
            assert(mr.eq(checked_call_target(expiry, 0xf9), purge), 'native expiry route changed')
            -- Validate the caller as well as each call instruction before using its targets.
            assert(mr.read(expiry, 0x116, 6) == '\72\139\206\72\139\211', 'native compact route changed')
            assert(mr.read(expiry, 0x121, 10) == '\72\141\79\8\76\139\195\72\139\208',
                'native erase route changed')
            return {purge = purge, compact = checked_call_target(expiry, 0x11c),
                erase = checked_call_target(expiry, 0x12b)}
        end)
        if not ok then self.reason = 'native_signature_mismatch'; return false end
        functions, self.ready, self.reason = result, true, nil
        return true
    end

    -- Return the exact owning pool and slot for a still-unrecruited ordinary character.
    -- Reacquire these after every creation/removal: native vectors can be reallocated.
    local function locate(details, preserve_identity)
        assert(details and not details:is_null_interface(), 'missing character details')
        local subtype_key = details:character_subtype_key()
        assert(type(subtype_key) == 'string' and (policy.caravan(subtype_key)
            or not (subtype_key:match('caravan') or subtype_key:match('convoy'))), 'special recruitment is unsupported')
        if policy.caravan(subtype_key) then
            assert(preserve_identity, 'caravan_identity_is_preserved')
            assert(environment.cm, 'caravan candidate unavailable')
            local ids = policy.caravan_candidates(environment.cm, details:faction(), subtype_key)
            assert(ids and ids[details:family_member():command_queue_index()], 'caravan candidate unavailable')
        end
        assert(not details:is_unique() and not details:is_immortal(), 'protected character')
        local actor = details:character()
        assert(not actor or actor:is_null_interface(), 'character was already recruited')
        local start = details:start_pos_key()
        assert(start == nil or start == '' or tostring(start) == '0', 'starting character')
        local faction = details:faction()
        assert(faction and not faction:is_null_interface() and faction:is_human(), 'invalid owner')
        local fp = mr.read_pointer(mr.ud_topointer(faction), 0x10)
        local dp = mr.read_pointer(mr.ud_topointer(details), 8)
        assert(nonnull(fp) and nonnull(dp), 'missing native objects')
        local manager = mr.read_pointer(fp, 0x1578)
        assert(nonnull(manager) and mr.eq(mr.read_pointer(manager, 8), fp), 'pool owner mismatch')
        local subtype = mr.read_pointer(dp, 0x1f0)
        assert(nonnull(subtype), 'missing subtype record')
        local map_size = mr.read_uint32(manager, 0x10)
        assert(map_size > 0 and map_size <= 1024, 'invalid pool map')
        local sentinel = mr.add(manager, 0x18)
        local node = mr.read_pointer(manager, 0x20)
        local visited, found = {}, nil
        for _ = 1, map_size do
            assert(nonnull(node) and not mr.eq(node, sentinel), 'truncated pool map')
            local address = mr.tostring(node)
            assert(not visited[address], 'cyclic pool map')
            visited[address] = true
            if mr.eq(mr.read_pointer(node, 0x10), subtype) then
                assert(not found, 'duplicate subtype pool')
                found = mr.read_pointer(node, 0x18)
            end
            node = mr.read_pointer(node, 8)
        end
        assert(mr.eq(node, sentinel), 'pool map size mismatch')
        assert(nonnull(found) and mr.eq(mr.read_pointer(found, 0), fp)
            and mr.eq(mr.read_pointer(found, 0x18), subtype), 'subtype pool mismatch')
        local capacity, count = mr.read_uint32(found, 8), mr.read_uint32(found, 0xc)
        assert(count > 0 and count <= capacity and capacity <= 10000, 'invalid candidate vector')
        local array = mr.read_pointer(found, 0x10)
        assert(nonnull(array), 'missing candidate vector')
        local slot
        for i = 0, count - 1 do
            local entry = mr.read_pointer(array, i * 8)
            assert(nonnull(entry), 'candidate vector contains a hole')
            if mr.eq(mr.read_pointer(entry, 0x18), dp) then
                assert(not slot, 'duplicate candidate identity')
                slot = mr.add(array, i * 8)
            end
        end
        assert(slot, 'candidate is not in this pool')
        return found, slot, array, count, dp, fp
    end

    local function pristine_skills(details, dp)
        local skills = mr.add(dp, 0x200)
        assert(mr.eq(mr.read_pointer(skills, 0x38), dp), 'skill owner mismatch')
        assert(mr.read_uint8(skills, 0x61) == 1, 'not character skills')
        assert(mr.read_uint32(skills, 0x40) == 0 and mr.read_uint32(skills, 0x44) == 0
            and mr.read_uint32(skills, 0x4c) == 0, 'candidate progression is protected')
        local count, capacity = mr.read_uint32(skills, 4), mr.read_uint32(skills, 0)
        assert(count > 0 and count <= capacity and capacity <= 128, 'invalid skill rows')
        local rows, allocated = mr.read_pointer(skills, 8), 0
        assert(nonnull(rows), 'missing skill rows')
        for i = 0, count - 1 do
            local row = mr.add(rows, i * 16)
            local n, cap = mr.read_uint32(row, 4), mr.read_uint32(row, 0)
            assert(n <= cap and cap <= 1024, 'invalid skill nodes')
            local nodes = mr.read_pointer(row, 8)
            assert(n == 0 or nonnull(nodes), 'missing skill nodes')
            for j = 0, n - 1 do
                local node = mr.add(nodes, j * 48)
                assert(mr.eq(mr.read_pointer(node, 0x28), skills), 'skill node owner mismatch')
                local node_record = mr.read_pointer(node, 0)
                assert(nonnull(node_record), 'missing skill record')
                local record = mr.read_pointer(node_record, 8)
                assert(nonnull(record), 'missing skill record')
                local level = mr.read_uint8(node, 0x10)
                if mr.read_uint8(record, 0x4c) == 1 then
                    if level > 0 then
                        assert(level == 1, 'candidate progression is protected')
                        allocated = allocated + 1
                    end
                else
                    -- Default spells/skills are recreated by the subtype's
                    -- initializer. Extra allocated points are never discarded.
                    assert(level == mr.read_uint8(node_record, 0x60), 'candidate progression is protected')
                end
            end
        end
        assert(allocated == 1 and details:background_skill() ~= '', 'nonstandard candidate background')
        return skills
    end

    -- Caravan entries created by spawn_character_to_pool cannot be hired safely
    -- on 9.0.5. Keep their engine-owned recruitment identity and reset only a
    -- pristine, unhired character's skills through the original initializer.
    local function background_context(details)
        assert(self.ready and self.build == '9.0.5.0', 'caravan background build unverified')
        assert(policy.caravan(details:character_subtype_key()), 'not a caravan')
        local _, _, _, _, dp, fp = locate(details, true)
        local skills = pristine_skills(details, dp)
        if not background_initializer then
            local address, matches = mr.find_pattern(BACKGROUND_SIGNATURE)
            assert(matches == 1 and mr.read(address, 0, #BACKGROUND_CODE) == BACKGROUND_CODE,
                'caravan skill initializer changed')
            local nested = checked_call_target(address, 0x102)
            assert(mr.read(nested, 0, #BACKGROUND_NESTED) == BACKGROUND_NESTED,
                'caravan skill reset route changed')
            assert(mr.read(checked_call_target(nested, 0x3c), 0, #BACKGROUND_CLEAR) == BACKGROUND_CLEAR,
                'caravan skill cleanup changed')
            background_initializer = address
        end
        return skills, fp, dp
    end

    function self.can_reset_background(details)
        local ok, reason = pcall(background_context, details)
        if ok then return true end
        return false, tostring(reason)
    end

    function self.reset_background(details)
        local ok, skills, faction, character = pcall(background_context, details)
        if not ok then return false, tostring(skills) end
        local changed, reason = pcall(function()
            mr.call(background_initializer, 'void(pointer,pointer,pointer,uint8)', skills, faction, character, 1)
            assert(details:background_skill() == '', 'caravan background reset failed')
        end)
        if not changed then self.ready, self.reason = false, 'native_background_failed' end
        return changed, not changed and tostring(reason) or nil
    end

    local function removable(details)
        if details and policy.finite(details:character_subtype_key()) then
            assert(self.build == '9.0.5.0', 'special skill build unverified')
        end
        local pool, slot, array, count, dp = locate(details)
        if policy.finite(details:character_subtype_key()) then pristine_skills(details, dp) end
        return pool, slot, array, count
    end

    function self.can_remove(details)
        if not self.ready then return false, self.reason end
        local ok, result = pcall(removable, details)
        if ok then return true end
        return false, tostring(result)
    end

    function self.remove(details)
        if not self.ready then return false, self.reason end
        local ok, pool, slot, array, count = pcall(removable, details)
        if not ok then return false, tostring(pool) end
        local changed, problem = pcall(function()
            mr.call(functions.purge, 'void(pointer,pointer)', pool, slot)
            assert(mr.eq(mr.read_pointer(slot, 0), NULL), 'native purge did not clear candidate')
            local finish = mr.add(array, count * 8)
            local compacted = mr.call(functions.compact, 'pointer(pointer,pointer)', array, finish)
            mr.call(functions.erase, 'pointer(pointer,pointer,pointer)', mr.add(pool, 8), compacted, finish)
            assert(mr.read_uint32(pool, 0xc) == count - 1, 'native candidate count mismatch')
        end)
        if not changed then
            -- An interrupted engine cleanup cannot be rolled back safely. The business
            -- layer locks the request and stops; do not attempt further native calls.
            self.ready, self.reason = false, 'native_cleanup_failed'
            return false, tostring(problem)
        end
        return true
    end

    return self
end

return M
