local function prepare(target,name)
 local panel=assert(find_uicomponent(core:get_ui_root(),'character_panel'))
 local b=assert(find_uicomponent(panel,'wizard_type','type_list',target));assert(b:Visible(true));b:SimulateLClick()
 cm:callback(function()local ok,e=pcall(function()xatw3_test.case(target,name,false)end);if not ok then xatw3_test.record('CLAW_CASE_PREPARE_FAIL '..tostring(e))end end,.6)
end
xatw3_test.prepare_claw=prepare
xatw3_test.record('CLAW_CASE_PREPARER_READY')
