local passed = {}
local function test(name, fn)
    local ok, problem = pcall(fn)
    if not ok then error(name .. ': ' .. tostring(problem)) end
    passed[#passed + 1] = name
end
local function check(value) assert(value, 'check failed') end
local function known_build(mr)
    mr.base = 0x1000
    local original = mr.read_uint32
    mr.read_uint32 = function(p, o)
        if p == mr.base and o == 0x3c then return 0x100 end
        if original then return original(p, o) end
        error('unexpected read')
    end
    mr.read = function(p, o, n)
        assert(p == mr.base)
        if o == 0 and n == 2 then return 'MZ' end
        if o == 0x100 and n == 4 then return 'PE\0\0' end
        if o == 0x108 then return '\244\198\206\106' end
        if o == 0x150 then return '\0\144\2\14' end
        error('unexpected header read')
    end
    return mr
end

test('missing_extension_fails_without_engine_calls', function()
    local bridge = native_pool_module.new({_G = {}})
    check(not bridge.initialize() and bridge.reason == 'native_dependency_missing')
    check(not bridge.remove({}))
end)

test('ambiguous_signatures_never_call_engine', function()
    local calls = 0
    local bridge = native_pool_module.new({_G = {memreader_plus = known_build({
        call = function() calls = calls + 1 end,
        ud_topointer = function() error('must not inspect objects') end,
        find_pattern = function() return 'ambiguous', 2 end
    })}})
    check(not bridge.initialize() and bridge.reason == 'native_signature_mismatch')
    check(not bridge.remove({}) and calls == 0)
end)

test('changed_expiry_call_site_never_calls_engine', function()
    local calls = 0
    local bridge = native_pool_module.new({_G = {memreader_plus = known_build({
        call = function() calls = calls + 1 end,
        ud_topointer = function() error('must not inspect objects') end,
        find_pattern = function() return 100, 1 end,
        add = function(p, offset) return p + offset end,
        read_uint8 = function() return 0x90 end
    })}})
    check(not bridge.initialize() and bridge.reason == 'native_signature_mismatch')
    check(calls == 0)
end)

test('unknown_build_never_scans_functions_or_reads_objects', function()
    local scans, calls = 0, 0
    local mr = known_build({call = function() calls = calls + 1 end,
        ud_topointer = function() error('must not inspect objects') end,
        find_pattern = function() scans = scans + 1 end})
    local read = mr.read
    mr.read = function(p,o,n) if o == 0x108 then return '\245\198\206\106' end;return read(p,o,n) end
    local bridge = native_pool_module.new({_G = {memreader_plus = mr}})
    check(not bridge.initialize() and bridge.reason == 'native_build_unverified')
    check(not bridge.remove({}) and scans == 0 and calls == 0)
end)

test('missing_or_malformed_image_identity_never_scans', function()
    for _, mode in ipairs({'missing_base','bad_dos','bad_pe_offset','bad_signature','bad_image_size'}) do
        local mr=known_build({call=function() error('must not call') end,
            ud_topointer=function() error('must not inspect objects') end,
            find_pattern=function() error('must not scan unverified image') end})
        local read=mr.read
        if mode=='missing_base' then mr.base=nil
        elseif mode=='bad_pe_offset' then mr.read_uint32=function() return 16777216 end
        else mr.read=function(p,o,n)
            if mode=='bad_dos' and o==0 then return 'ZZ' end
            if mode=='bad_signature' and o==0x100 then return 'NOPE' end
            if mode=='bad_image_size' and o==0x150 then return '\0\144\3\14' end
            return read(p,o,n)
        end end
        local bridge=native_pool_module.new({_G={memreader_plus=mr}})
        check(not bridge.initialize() and bridge.reason=='native_build_unverified')
    end
end)

test('special_details_rejected_before_native_object_dereference', function()
    local mr={call=function() error('must not call') end,
        ud_topointer=function() error('must not dereference special recruitment') end}
    local bridge=native_pool_module.new({_G={memreader_plus=mr}})
    bridge.ready=true -- Exercise the locator's independent guard after admission.
    for _,key in ipairs({'wh3_main_cth_lord_caravan_master','wh3_cp1_cth_sawai_caravan','mod_convoy_leader'}) do
        local details={is_null_interface=function() return false end,character_subtype_key=function() return key end}
        local allowed,why=bridge.can_remove(details)
        check(not allowed and why:match('special recruitment is unsupported'))
        local removed,reason=bridge.remove(details)
        check(not removed and reason:match('special recruitment is unsupported'))
    end
end)

-- Native memory is not simulated as proof that removal works. The real-engine
-- probe covers removal/compaction. These tests only prove rejection behavior.
return passed
