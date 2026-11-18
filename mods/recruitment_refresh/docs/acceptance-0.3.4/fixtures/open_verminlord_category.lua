local b=assert(find_uicomponent(core:get_ui_root(),'character_panel','lord_parent','list_box','wh3_skv_verminlord'))
assert(b:Visible(true)and(b:CurrentState()=='active'or b:CurrentState()=='hover'));b:SimulateLClick()
cm:callback(function()
 local p=assert(find_uicomponent(core:get_ui_root(),'character_panel','lord_magic_lore_type','lore_type_list'))
 for i=0,p:ChildCount()-1 do local c=UIComponent(p:Find(i));if c:Visible(true)then xatw3_test.record('VERMINLORD_LORE_TAB '..c:Id()..' '..c:CurrentState())end end
 xatw3_test.record('VERMINLORD_CATEGORY_READY')
end,.6)
