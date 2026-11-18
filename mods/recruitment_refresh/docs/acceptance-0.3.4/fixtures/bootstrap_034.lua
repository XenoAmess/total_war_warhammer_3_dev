assert(string.sub('abcdef',1,3)=='abc')
assert(xatw3_campaign_utilities.version=='0.3.4')
assert(xatw3_move_capital.version=='0.2.0')
assert(xatw3_campaign_utilities.runtime.refresh_verified)
local f=assert(io.open('D:/workspace/.codex-wh3-runtime/dlc-round2-20261118/evidence_helpers_034.lua','r'));local s=f:read('*a');f:close();local c=assert(loadstring(s));setfenv(c,getfenv(1));c()
local faction=cm:get_local_faction();local regions={};local list=faction:region_list()
for i=0,list:num_items()-1 do regions[#regions+1]=list:item_at(i):name() end
xatw3_test.save('bootstrap-'..faction:name(),{faction=faction:name(),capital=xatw3_move_capital.runtime.capital(faction:name()),regions=regions,refresh_release=require('script.xatw3_release_recruitment_refresh'),capital_release=require('script.xatw3_release_move_capital')})
xatw3_test.record('DLC_BOTH_MODS_COLD_READY '..faction:name())
cm:callback(function()
 local b=find_uicomponent(core:get_ui_root(),'custom_loading_screen','button_continue');if b and b:Visible() then b:SimulateLClick() end
 for _,c in ipairs(cm.cutscene_list) do if c:is_active() then c:skip() end end
end,2)

xatw3_test.package_sha='0d28ee92aa0bf1f5a9c3d7d7331fec682ece2def45c90341f084726607d3bf9d'
xatw3_test.pool_keys={'wh3_cp1_cth_clawspeaker_beasts','wh3_cp1_cth_clawspeaker_life','wh3_cp1_cth_clawspeaker_shadows','wh3_cp1_cth_sawai','wh3_cp1_cth_sawai_caravan','wh3_dlc24_cth_celestial_general_yang','wh3_dlc24_cth_celestial_general_yin','wh3_dlc24_cth_gate_master','wh3_dlc29_skv_verminlord_corruptor','wh3_dlc29_skv_verminlord_deceiver','wh3_dlc29_skv_verminlord_warbringer','wh3_dlc29_skv_verminlord_warpseer','wh3_main_cth_alchemist','wh3_main_cth_astromancer','wh3_main_cth_dragon_blooded_shugengan_yang','wh3_main_cth_dragon_blooded_shugengan_yin','wh3_main_cth_lord_caravan_master','wh3_main_cth_lord_magistrate_yang','wh3_main_cth_lord_magistrate_yin'}
assert(require('script.xatw3_release_recruitment_refresh')=='5a958457fb30b620e246ee928b180244cb0ba5a148c41c4edb5cf16936e84bbe')
local f=assert(io.open('D:/workspace/.codex-wh3-runtime/dlc-round2-20261118/acceptance_tools.lua','r'));local s=f:read('*a');f:close();local chunk=assert(loadstring(s));setfenv(chunk,getfenv(1));chunk()
xatw3_test.record('ROUND2_COLD_READY '..cm:get_local_faction_name()..' SHA '..xatw3_test.package_sha)

local f=assert(io.open('D:/workspace/.codex-wh3-runtime/dlc-round2-20261118/install_ui_dispatch.lua','r'));local s=f:read('*a');f:close();local chunk=assert(loadstring(s));setfenv(chunk,getfenv(1));chunk()

assert(cm:get_local_faction_name()=='wh3_cp1_cth_tiger_warriors')
xatw3_test.record('FINAL_034_COLD_CHECKPOINT_LOADED')
