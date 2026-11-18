cm:dismiss_advice()
local event=find_uicomponent(core:get_ui_root(),'events','button_set','accept_holder','button_accept');if event and event:Visible(true)then event:SimulateLClick()end
CampaignUI.ClosePanel('military_convoys');CampaignUI.CloseCurrentHUDPanel()
local target=cm:get_region('wh3_main_combi_region_great_skull_lakes');local settlement=target:settlement();local x,y,d,b,h=cm:get_camera_position()
cm:scroll_camera_from_current(false,1,{settlement:display_position_x(),settlement:display_position_y(),7.6,b,4})
xatw3_test.record('CAPITAL_CAMERA_RETURNED_FROM_CONVOY_MAP')
