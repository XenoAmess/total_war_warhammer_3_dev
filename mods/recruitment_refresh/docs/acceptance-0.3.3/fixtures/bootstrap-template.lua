assert(string.sub('abcdef',1,3)=='abc')
assert(xatw3_campaign_utilities.version=='0.3.2')
assert(xatw3_move_capital.version=='0.2.0')
assert(xatw3_campaign_utilities.runtime.refresh_verified)
local f=assert(io.open('D:/workspace/.codex-wh3-runtime/dlc-acceptance-20261118/evidence_helpers.lua','r'));local s=f:read('*a');f:close();local c=assert(loadstring(s));setfenv(c,getfenv(1));c()
local faction=cm:get_local_faction();local regions={};local list=faction:region_list()
for i=0,list:num_items()-1 do regions[#regions+1]=list:item_at(i):name() end
xatw3_test.save('bootstrap-'..faction:name(),{faction=faction:name(),capital=xatw3_move_capital.runtime.capital(faction:name()),regions=regions,refresh_release=require('script.xatw3_release_recruitment_refresh'),capital_release=require('script.xatw3_release_move_capital')})
xatw3_test.record('DLC_BOTH_MODS_COLD_READY '..faction:name())
cm:callback(function()
 local b=find_uicomponent(core:get_ui_root(),'custom_loading_screen','button_continue');if b and b:Visible() then b:SimulateLClick() end
 for _,c in ipairs(cm.cutscene_list) do if c:is_active() then c:skip() end end
end,2)
