local panel=assert(find_uicomponent(core:get_ui_root(),'character_panel'))
local function rect(c)
 local x,y=c:Position();local w,h=c:Dimensions();return{x=x,y=y,w=w,h=h,visible=c:Visible(true),state=c:CurrentState()}
end
local refresh=rect(assert(find_uicomponent(panel,'xatw3_refresh_candidates')))
local native=rect(assert(find_uicomponent(panel,'footer','button_raise')))
assert(refresh.visible and native.visible)
assert(refresh.x+refresh.w<=native.x or native.x+native.w<=refresh.x or refresh.y+refresh.h<=native.y or native.y+native.h<=refresh.y,'Refresh overlaps native hire')
xatw3_test.save('final-native-ui-geometry',{status='PASS',package_sha256=xatw3_test.package_sha,refresh=refresh,native_hire=native,scope='Actual final cold package, native Skaven lord page; no overlap between refresh and native hire controls'})
xatw3_test.record('FINAL_NATIVE_UI_GEOMETRY_PASS')
