function xatw3_test.prepare_verminlord(kind)
 local target='wh3_dlc29_skv_verminlord_'..kind
 local b=assert(find_uicomponent(core:get_ui_root(),'character_panel','lord_magic_lore_type','lore_type_list','wh3_dlc29_lore_verminlord_'..kind))
 assert(b:Visible(true));b:SimulateLClick()
 cm:callback(function()
  local ok,e=pcall(function()xatw3_test.case(target,'verminlord-'..kind,false)end)
  if not ok then xatw3_test.record('VERMINLORD_PREPARE_FAIL '..tostring(e))end
 end,.6)
end
xatw3_test.record('VERMINLORD_PREPARER_READY')
