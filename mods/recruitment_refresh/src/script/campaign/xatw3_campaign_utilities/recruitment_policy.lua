local M = {}
local caravans = {
    wh3_main_cth_lord_caravan_master = true,
    wh3_dlc23_chd_lord_convoy_overseer = true,
    wh3_cp1_cth_sawai_caravan = true
}

function M.caravan(key) return caravans[key] == true end

-- Existing, unlocked candidates only. Fixed named/dynasty/ship characters are
-- deliberately absent: their innate skills are part of their unique identity.
function M.finite(key)
    if type(key) ~= 'string' then return false end
    return key:match('^wh3_main_ksl_ice_witch_') ~= nil
        or key:match('^wh3_main_ksl_frost_maiden_') ~= nil
        or key:match('^wh2_dlc11_vmp_bloodline_') ~= nil
        or key:match('^wh2_dlc13_lzd_slann_mage_priest_') ~= nil
        or key == 'wh2_main_lzd_slann_mage_priest' or key == 'wh2_main_lzd_slann_mage_priest_horde'
        or key:match('^wh3_dlc20_chs_daemon_prince_') ~= nil
        or key:match('^wh3_main_kho_exalted_bloodthirster') ~= nil
        or key:match('^wh3_main_nur_exalted_great_unclean_one_') ~= nil
        or key:match('^wh3_main_sla_exalted_keeper_of_secrets_') ~= nil
        or key:match('^wh3_main_tze_exalted_lord_of_change_') ~= nil
        or key:match('^wh3_dlc29_skv_verminlord_') ~= nil
end

function M.minimum(key)
    if M.caravan(key) or M.finite(key) then return 0 end
    return 3
end

-- A currently offered recruitment item is authoritative for an unhired caravan.
-- Owned caravans, including idle/returning ones, can never be refresh candidates.
function M.caravan_candidates(cm, faction, subtype)
    local ok, result = pcall(function()
        assert(M.caravan(subtype) and cm and faction)
        local fc = cm:model():world():caravans_system():faction_caravans(faction)
        assert(fc and not fc:is_null_interface() and fc:faction():name() == faction:name())
        local owned = {}
        for _, list in ipairs({fc:active_caravans(), fc:idle_caravans()}) do
            local n = list:num_items(); assert(n >= 0 and n <= 1000)
            for i = 0, n - 1 do owned[list:item_at(i):caravan_master():command_queue_index()] = true end
        end
        local offered = fc:available_caravan_recruitment_items()
        local n = offered:num_items(); assert(n >= 0 and n <= 100)
        local ids, seen = {}, {}
        for i = 0, n - 1 do
            local fm = offered:item_at(i):caravan_master()
            local details, id = fm:character_details(), fm:command_queue_index()
            assert(type(id) == 'number' and id > 0 and id == math.floor(id) and not seen[id])
            seen[id] = true
            assert(details:faction():name() == faction:name())
            if details:character_subtype_key() == subtype and not owned[id] then ids[id] = true end
        end
        return ids
    end)
    if ok then return result end
    return nil, tostring(result)
end

return M
