local function later(fn)cm:callback(function()local ok,e=pcall(fn);if not ok then xatw3_test.record('BHASHIVA_HERO_NAV_FAIL '..tostring(e))end end,.7)end
cm:dismiss_advice()
for _,c in ipairs(cm.cutscene_list)do if c:is_active()then c:skip()end end
local event=find_uicomponent(core:get_ui_root(),'events','button_set','accept_holder','button_accept')
if event and event:Visible(true)then event:SimulateLClick()end
CampaignUI.CloseCurrentHUDPanel()
local region=cm:get_region('wh3_main_combi_region_vale_of_titans')
local adjacent=region:adjacent_region_list()
for i=0,adjacent:num_items()-1 do
 local other=adjacent:item_at(i)
 if not other:settlement():is_null_interface()then
  common.get_context_value('CcoCampaignSettlement',other:cqi(),'Select')
  break
 end
end
common.get_context_value('CcoCampaignSettlement',region:cqi(),'Select')
later(function()
 local settlement=find_uicomponent(core:get_ui_root(),'settlement_panel')
 xatw3_test.record('BHASHIVA_CITY_PANEL '..tostring(settlement and settlement:Visible(true)))
 local b=assert(find_uicomponent(core:get_ui_root(),'hud_campaign','hud_center_docker','button_agents'))
 xatw3_test.record('BHASHIVA_HERO_OPENER '..b:CurrentState());assert(b:Visible(true));b:SimulateLClick()
 xatw3_test.record('BHASHIVA_HERO_CLICK_RETURNED')
 later(function()
  local function walk(c,path,depth)
   if not c:Visible(true)then return end
   local p=path..'/'..c:Id();xatw3_test.record('HERO_PANEL '..p..' state='..c:CurrentState())
   if depth<9 then for i=0,c:ChildCount()-1 do walk(UIComponent(c:Find(i)),p,depth+1)end end
  end
  walk(assert(find_uicomponent(core:get_ui_root(),'character_panel')),'',0)
  xatw3_test.record('BHASHIVA_HERO_PANEL_READY')
 end)
end)
