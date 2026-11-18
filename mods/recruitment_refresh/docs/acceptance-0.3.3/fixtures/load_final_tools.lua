assert(xatw3_campaign_utilities.version=='0.3.3')
assert(require('script.xatw3_release_recruitment_refresh')=='495317074cb7210a6fb94dd6a1cdf6a6f499abe6470ca84fbce4cc6eb40fbcc6')
xatw3_test.package_sha='51af917201f2b82aac216783b3b5291ac8198671a444182c9f3a15b0cfbe73cd'
local f=assert(io.open('D:/workspace/.codex-wh3-runtime/dlc-acceptance-20261118/chd_tools.lua','r'));local s=f:read('*a');f:close();local c=assert(loadstring(s));setfenv(c,getfenv(1));c()
local master=assert(find_uicomponent(core:get_ui_root(),'military_convoys','master_panel'));local b=assert(find_uicomponent(master,'xatw3_refresh_candidates'));local h=assert(find_uicomponent(master,'recruit_masters_heading'))
local function rect(c)local x,y=c:Position();local w,h=c:Dimensions();return{x=x,y=y,w=w,h=h}end
local r,a=rect(b),rect(h);assert(b:Visible(true) and r.x>=a.x and r.y>=a.y and r.x+r.w<=a.x+a.w and r.y+r.h<=a.y+a.h)
xatw3_test.save('final-convoy-button',{status='PASS',package_sha256=xatw3_test.package_sha,button=r,heading=a,state=b:CurrentState(),target=xatw3_campaign_utilities.ui.selected_subtype})
xatw3_test.record('FINAL_CONVOY_BUTTON_LAYOUT_PASS')
