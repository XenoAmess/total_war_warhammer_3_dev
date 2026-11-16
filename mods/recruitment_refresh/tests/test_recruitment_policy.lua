local passed={}
local function test(name,fn) fn();passed[#passed+1]=name end
local policy=policy_module
local function list(items)
    return {num_items=function() return #items end,item_at=function(_,i) return items[i+1] end}
end
local function fixture(options)
    options=options or {}
    local faction={name=function() return 'cathay' end}
    local function master(id,foreign)
        return {command_queue_index=function() return id end,character_details=function()
            return {faction=function() return foreign and {name=function() return 'other' end} or faction end,
                character_subtype_key=function() return 'wh3_main_cth_lord_caravan_master' end}
        end}
    end
    local function item(id,foreign) return {caravan_master=function() return master(id,foreign) end} end
    local fc={is_null_interface=function() return false end,faction=function() return faction end,
        active_caravans=function() return list({item(2)}) end,
        idle_caravans=function() return list({item(3)}) end,
        available_caravan_recruitment_items=function()
            if options.unreadable then error('unavailable') end
            return list(options.duplicate and {item(1),item(1)}
                or {item(1,options.foreign),item(2),item(3)})
        end}
    local cm={model=function() return {world=function() return {caravans_system=function()
        return {faction_caravans=function() return fc end}
    end} end} end}
    return cm,faction
end

test('caravan_offers_exclude_active_and_idle_owned_generals',function()
    local cm,faction=fixture()
    local ids=assert(policy.caravan_candidates(cm,faction,'wh3_main_cth_lord_caravan_master'))
    assert(ids[1] and not ids[2] and not ids[3])
end)
test('unreadable_duplicate_or_foreign_caravan_offers_fail_closed',function()
    for _,options in ipairs({{unreadable=true},{duplicate=true},{foreign=true}}) do
        local cm,faction=fixture(options)
        assert(policy.caravan_candidates(cm,faction,'wh3_main_cth_lord_caravan_master')==nil)
    end
end)
test('special_pool_count_does_not_create_additional_unlocks',function()
    assert(policy.minimum('wh3_main_cth_lord_caravan_master')==0)
    assert(policy.minimum('wh2_dlc11_vmp_bloodline_blood_dragon')==0)
    assert(policy.minimum('wh3_main_ksl_boyar')==3)
    assert(not policy.finite('wh3_main_ksl_ice_witch_ice') and not policy.finite('wh3_main_ksl_frost_maiden_ice'))
    assert(not policy.finite('wh2_dlc09_tmb_tomb_king_alkhazzar_ii'))
    assert(not policy.finite('wh3_dlc27_hef_dragonship_captain_01'))
    assert(not policy.caravan('other_mod_caravan_master'))
end)
test('only_authoritative_unhired_caravans_can_replace_unknown_old_history',function()
    local key='wh3_main_cth_lord_caravan_master'
    local offered={id=1,faction='cathay',subtype=key,in_pool=true,male=true,
        provenance='caravan_available',caravan_available=true}
    local owned={id=2,faction='cathay',subtype=key,in_pool=true,male=true,
        provenance='unknown',caravan_available=false}
    local plan=logic.plan({offered,owned},'cathay',key)
    assert(#plan.replace==1 and plan.replace[1].id==1 and #plan.protected==1 and plan.add==0)
    owned.provenance='ordinary_generated';assert(not logic.eligible(owned,'cathay',key))
    offered.recruited=true;assert(not logic.eligible(offered,'cathay',key))
end)
test('finite_pool_preserves_count_and_unknown_history_protection',function()
    local key='wh2_main_lzd_slann_mage_priest'
    local c={id=1,faction='kislev',subtype=key,in_pool=true,male=false,provenance='ordinary_generated'}
    local plan=logic.plan({c},'kislev',key);assert(#plan.replace==1 and plan.add==0)
    c.provenance='unknown';plan=logic.plan({c},'kislev',key)
    assert(#plan.replace==0 and plan.add==0 and #plan.protected==1)
end)
test('training_traits_and_caravan_ownership_participate_in_stale_snapshot',function()
    local c={id=1,trait_signature='training_a:1',caravan_available=true}
    local before=logic.fingerprint({c});c.trait_signature='training_a:2'
    assert(before~=logic.fingerprint({c}));before=logic.fingerprint({c});c.caravan_available=false
    assert(before~=logic.fingerprint({c}))
end)
test('failed_training_trait_copy_never_deletes_original_candidate',function()
    local subtype='wh2_main_lzd_slann_mage_priest'
    local original={id=1,faction='kislev',subtype=subtype,in_pool=true,male=false,
        provenance='ordinary_generated',trait_signature='ice_training:1'}
    local pool={original};local removed=false
    local adapter={read_pool=function() return pool end,can_remove_candidate=function() return true end,
        spawn_candidate=function()
            local created={id=2,faction='kislev',subtype=subtype,in_pool=true,male=false,
                provenance='ordinary_generated',trait_signature=''}
            pool={original,created};return created
        end,verify_candidate=function() return true end,remove_candidate=function() removed=true end}
    local result=logic.refresh(adapter,'kislev',subtype,logic.fingerprint(pool))
    assert(result.status=='UNKNOWN' and result.reason=='invalid_generated_candidate' and not removed)
end)
test('caravan_background_refresh_keeps_identity_without_spawn_or_delete',function()
    local key='wh3_main_cth_lord_caravan_master'
    local c={id=1,faction='cathay',subtype=key,in_pool=true,male=true,background='old',
        provenance='caravan_available',caravan_available=true}
    local pool={c};local adapter={read_pool=function() return pool end,can_remove_candidate=function() return true end,
        spawn_candidate=function() error('must not spawn a caravan') end,
        remove_candidate=function() error('must not delete a caravan') end,
        refresh_caravan_candidate=function(_,_,old)
            local changed={};for k,v in pairs(old) do changed[k]=v end;changed.background='new';pool={changed};return 'new'
        end}
    local result=logic.refresh(adapter,'cathay',key,logic.fingerprint(pool))
    assert(result.status=='SUCCEEDED' and result.completed==1 and result.added==0)
    assert(result.pairs[1].old==1 and result.pairs[1].new==1 and result.pairs[1].mode=='background')
end)
test('caravan_background_readback_rejects_changed_identity_or_other_metadata',function()
    local key='wh3_main_cth_lord_caravan_master'
    for _,field in ipairs({'id','forename','caravan_available'}) do
        local c={id=1,faction='cathay',subtype=key,in_pool=true,male=true,background='old',
            forename='name',provenance='caravan_available',caravan_available=true}
        local pool={c};local adapter={read_pool=function() return pool end,can_remove_candidate=function() return true end,
            refresh_caravan_candidate=function(_,_,old)
                local changed={};for k,v in pairs(old) do changed[k]=v end
                changed.background='new';changed[field]='unexpected';pool={changed};return 'new'
            end}
        assert(logic.refresh(adapter,'cathay',key,logic.fingerprint(pool)).status=='UNKNOWN')
    end
end)
test('all_caravan_background_weights_exclude_old_and_protect_unknown_mod_skills',function()
    for _,key in ipairs({'wh3_main_cth_lord_caravan_master','wh3_dlc23_chd_lord_convoy_overseer','wh3_cp1_cth_sawai_caravan'}) do
        local old=policy.choose_caravan_background(key,'unknown',function() error('must not roll') end)
        assert(old==nil)
    end
    local key='wh3_main_cth_lord_caravan_master';local old='wh3_main_skill_innate_cth_caravan_master_cavalry'
    local total;local new=policy.choose_caravan_background(key,old,function(n) total=n;return n end)
    assert(total==14 and new~=old and policy.caravan_background_known(key,new))
    assert(policy.choose_caravan_background(key,old,function() return 0 end)==nil)
end)
return passed
