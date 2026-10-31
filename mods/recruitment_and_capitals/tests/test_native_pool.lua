local passed = {}
local function test(name, fn)
    local ok, problem = pcall(fn)
    if not ok then error(name .. ': ' .. tostring(problem)) end
    passed[#passed + 1] = name
end
local function check(value) assert(value, 'check failed') end

test('missing_extension_fails_without_engine_calls', function()
    local bridge = native_pool_module.new({_G = {}})
    check(not bridge.initialize() and bridge.reason == 'native_dependency_missing')
    check(not bridge.remove({}))
end)

test('ambiguous_signatures_never_call_engine', function()
    local calls = 0
    local bridge = native_pool_module.new({_G = {memreader_plus = {
        call = function() calls = calls + 1 end,
        ud_topointer = function() error('must not inspect objects') end,
        find_pattern = function() return 'ambiguous', 2 end
    }}})
    check(not bridge.initialize() and bridge.reason == 'native_signature_mismatch')
    check(not bridge.remove({}) and calls == 0)
end)

test('changed_expiry_call_site_never_calls_engine', function()
    local calls = 0
    local bridge = native_pool_module.new({_G = {memreader_plus = {
        call = function() calls = calls + 1 end,
        ud_topointer = function() error('must not inspect objects') end,
        find_pattern = function() return 100, 1 end,
        add = function(p, offset) return p + offset end,
        read_uint8 = function() return 0x90 end
    }}})
    check(not bridge.initialize() and bridge.reason == 'native_signature_mismatch')
    check(calls == 0)
end)

-- Native memory is not simulated as proof that removal works. The real-engine
-- probe covers removal/compaction. These tests only prove rejection behavior.
return passed
