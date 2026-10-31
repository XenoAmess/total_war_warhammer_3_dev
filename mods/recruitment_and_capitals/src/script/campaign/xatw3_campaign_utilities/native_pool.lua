-- Uses the engine's own candidate expiry cleanup, followed by its vector cleanup.
-- No object bytes, names, skill trees, or allocator-owned pointers are written by Lua.
-- The signatures and layouts below were verified on WH3 9.0.4, Windows x64.
local M = {}

local EXPIRY = '48 89 5C 24 18 88 54 24 10 55 56 57 41 54 41 55 41 56 41 57 '
    .. '48 83 EC 30 48 8B 01 0F 57 C0 48 8B F9 4C 8B 80 A8 03 00 00 '
    .. '4D 8B A8 90 00 00 00 F3 4D 0F 2C B5 D8 69 00 00'
local PURGE = '48 8B C4 48 89 58 08 48 89 68 10 48 89 70 18 48 89 78 20 '
    .. '41 54 41 56 41 57 48 83 EC 20 4C 8B F1 48 8B F2 48 8B 0A 48 85 C9'
local NULL = string.rep('\0', 8)

function M.new(environment)
    environment = environment or getfenv(2)
    local globals = environment._G or _G
    local mr = globals.memreader_plus
    local self = {ready = false, reason = 'native_dependency_missing'}
    local functions

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
    local function locate(details)
        assert(details and not details:is_null_interface(), 'missing character details')
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
        return found, slot, array, count
    end

    function self.can_remove(details)
        if not self.ready then return false, self.reason end
        local ok, result = pcall(locate, details)
        if ok then return true end
        return false, tostring(result)
    end

    function self.remove(details)
        if not self.ready then return false, self.reason end
        local ok, pool, slot, array, count = pcall(locate, details)
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
