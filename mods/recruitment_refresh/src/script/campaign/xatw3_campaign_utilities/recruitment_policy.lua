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
    return key:match('^wh2_dlc11_vmp_bloodline_') ~= nil
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

-- Vanilla 9.0.5 background weights. Unknown backgrounds are protected.
local caravan_backgrounds = {
    wh3_main_cth_lord_caravan_master = {
        {'wh3_main_skill_innate_cth_caravan_master_Dragon-Blooded', 1},
        {'wh3_main_skill_innate_cth_caravan_master_Former-Artillery-Officer', 1},
        {'wh3_main_skill_innate_cth_caravan_master_Humble-Born', 2},
        {'wh3_main_skill_innate_cth_caravan_master_Longma-Whisperer', 1},
        {'wh3_main_skill_innate_cth_caravan_master_Nan-Gau', 1},
        {'wh3_main_skill_innate_cth_caravan_master_Ogre-Ally', 2},
        {'wh3_main_skill_innate_cth_caravan_master_Shang-Yang', 1},
        {'wh3_main_skill_innate_cth_caravan_master_Western-Idealist', 1},
        {'wh3_main_skill_innate_cth_caravan_master_cavalry', 1},
        {'wh3_main_skill_innate_cth_caravan_master_gunner', 1},
        {'wh3_main_skill_innate_cth_caravan_master_royalty', 1},
        {'wh3_main_skill_innate_cth_caravan_master_stealth', 2},
    },
    wh3_dlc23_chd_lord_convoy_overseer = {
        {'wh3_dlc23_skill_innate_chd_convoy_overseer_bull_centaur_master', 1},
        {'wh3_dlc23_skill_innate_chd_convoy_overseer_cannonry_experience', 1},
        {'wh3_dlc23_skill_innate_chd_convoy_overseer_connected', 1},
        {'wh3_dlc23_skill_innate_chd_convoy_overseer_covert', 1},
        {'wh3_dlc23_skill_innate_chd_convoy_overseer_hobgoblin_favour', 1},
        {'wh3_dlc23_skill_innate_chd_convoy_overseer_kdaai_domination', 1},
        {'wh3_dlc23_skill_innate_chd_convoy_overseer_metallic_resilience', 1},
        {'wh3_dlc23_skill_innate_chd_convoy_overseer_monster_commander', 1},
        {'wh3_dlc23_skill_innate_chd_convoy_overseer_ogre_controller', 1},
        {'wh3_dlc23_skill_innate_chd_convoy_overseer_retired_daemonsmither', 1},
        {'wh3_dlc23_skill_innate_chd_convoy_overseer_sharpshooter', 1},
        {'wh3_dlc23_skill_innate_chd_convoy_overseer_war_machinist', 1},
    },
    wh3_cp1_cth_sawai_caravan = {
        {'wh3_cp1_skill_innate_cth_caravan_sawai_alchemy', 1},
        {'wh3_cp1_skill_innate_cth_caravan_sawai_artillery', 1},
        {'wh3_cp1_skill_innate_cth_caravan_sawai_cavalry', 1},
        {'wh3_cp1_skill_innate_cth_caravan_sawai_celestial', 1},
        {'wh3_cp1_skill_innate_cth_caravan_sawai_clawspeaker', 1},
        {'wh3_cp1_skill_innate_cth_caravan_sawai_gunpowder', 1},
        {'wh3_cp1_skill_innate_cth_caravan_sawai_jade', 1},
        {'wh3_cp1_skill_innate_cth_caravan_sawai_peasants', 2},
        {'wh3_cp1_skill_innate_cth_caravan_sawai_ranged', 1},
        {'wh3_cp1_skill_innate_cth_caravan_sawai_sky', 1},
        {'wh3_cp1_skill_innate_cth_caravan_sawai_tigers', 2},
        {'wh3_cp1_skill_innate_cth_caravan_sawai_veteran', 2},
    },
}

function M.caravan_background_known(key, background)
    for _, item in ipairs(caravan_backgrounds[key] or {}) do
        if item[1] == background then return true end
    end
    return false
end

function M.choose_caravan_background(key, old, random)
    if not M.caravan_background_known(key, old) then return nil end
    local total = 0
    for _, item in ipairs(caravan_backgrounds[key]) do
        if item[1] ~= old then total = total + item[2] end
    end
    local roll = random(total)
    if type(roll) ~= 'number' or roll < 1 or roll > total or roll ~= math.floor(roll) then return nil end
    for _, item in ipairs(caravan_backgrounds[key]) do
        if item[1] ~= old then
            roll = roll - item[2]
            if roll <= 0 then return item[1] end
        end
    end
end

return M
