local function tick_ui()
 local f=io.open('D:/workspace/.codex-wh3-runtime/dlc-round2-20261118/native/ui-command.lua','r')
 if f then
  local code=f:read('*a');f:close();os.remove('D:/workspace/.codex-wh3-runtime/dlc-round2-20261118/native/ui-command.lua')
  local c,e=loadstring(code,'xatw3_ui_only_acceptance');if c then setfenv(c,getfenv(1));local ok,result=pcall(c);xatw3_test.record('UI_COMMAND_RESULT ok='..tostring(ok)..' result='..tostring(result))else xatw3_test.record('UI_COMPILE_ERROR '..tostring(e))end
 end
 core:get_tm():real_callback(tick_ui,500,'dlc_ui_only_dispatch')
end
core:get_tm():real_callback(tick_ui,500,'dlc_ui_only_dispatch');xatw3_test.record('UI_ONLY_DISPATCH_READY')
