-- Controller geometry; native rendering is verified separately.
local passed={}
local function fixture(scale,dx,dy)
 scale,dx,dy=scale or 1,dx or 0,dy or 0
 local function comp(id,parent,x,y,w,h)
  local c={id=id,children={},visible=true,x=x or 0,y=y or 0,w=w or 0,h=h or 0}
  function c:Id() return self.id end
  function c:Position() return self.x,self.y end
  function c:Dimensions() return self.w,self.h end
  function c:Visible() return self.visible end
  function c:CurrentState() return self.state or 'active' end
  function c:ChildCount() return #self.children end
  function c:Find(i) return self.children[i+1] end
  function c:SetVisible(v) self.visible=v end
  function c:SetTooltipText(v) self.tooltip=v end
  function c:SetInteractive(v) self.interactive=v end
  function c:SetImagePath(v) self.image=v end
  function c:SetCanResizeWidth(v) self.resize_width=v end
  function c:SetCanResizeHeight(v) self.resize_height=v end
  function c:SetDockingPoint(v) self.docking=v end
  function c:SetDockOffset(x,y) self.dock_x,self.dock_y=x,y end
  function c:Resize(w,h) self.w,self.h=w,h end
  function c:MoveTo(x,y) self.x,self.y=x,y end
  if parent then parent.children[#parent.children+1]=c end
  return c
 end
 local f={root=comp('root'),creations=0,comp=comp,scale=scale}
 f.panel=comp('character_panel',f.root,dx,dy,820*scale,650*scale)
 f.holder=comp('character_panel_info_holder',f.panel,dx,dy-208*scale,820*scale,754*scale)
 f.footer=comp('footer',f.holder,dx,dy+430*scale,820*scale,50*scale)
 f.recruit=comp('button_raise',f.footer,dx+260*scale,dy+429.5*scale,300*scale,51*scale)
 f.load=comp('button_load_character',f.footer,dx+774*scale,dy+437*scale,36*scale,36*scale)
 f.province=comp('province_cycle',f.footer,dx+13*scale,dy+430*scale,100*scale,49*scale)
 f.categories=comp('lords_and_agents_holder',f.panel)
 f.lords=comp('lord_parent',f.categories);f.agents=comp('agent_parent',f.categories);f.agents.visible=false
 f.lord_tab=comp('supported',f.lords);f.lord_tab.state='selected'
 local function find(parent,...)
  for _,id in ipairs({...}) do
   local function descend(node)
    if not node then return false end
    for _,child in ipairs(node.children) do
     if child.id==id then return child end
     local found=descend(child);if found then return found end
    end
    return false
   end
   parent=descend(parent);if not parent then return false end
  end
  return parent
 end
 local core={get_ui_root=function() return f.root end,add_listener=function() end}
 function core:get_or_create_component(id,template,parent)
  for _,child in ipairs(parent.children) do if child.id==id then return child end end
  assert(template=='ui/templates/square_small_button.twui.xml')
  f.creations=f.creations+1;f.button=comp(id,parent,0,0,28,28)
  f.icon=comp('icon',f.button,0,0,24,24);f.flame=comp('button_flame',f.button,0,0,100,100)
  return f.button
 end
 f.runtime={initialized=true,refresh_verified=true,subtypes={supported='general'},state={locked=false},can_act=function() return true end,supported=function(k) return k=='supported' end}
 f.ui=ui_module.new(f.runtime,{}, {core=core,find_uicomponent=find,
  UIComponent=function(c) return setmetatable({}, {__index=c}) end,
  cm={get_local_faction_name=function() return 'faction' end},common={get_localised_string=function(k) return k end}})
 f.ui.selected_subtype='supported';f.ui.refresh_buttons();return f
end
local function inside(a,b) assert(a.x>=b.x and a.y>=b.y and a.x+a.w<=b.x+b.w and a.y+a.h<=b.y+b.h) end
local function clear(a,b,g)
 g=g or 0;assert(a.x+a.w+g<=b.x or b.x+b.w+g<=a.x or a.y+a.h+g<=b.y or b.y+b.h+g<=a.y)
end
local function visible(f,obstacle)
 assert(f.button.visible and f.button.interactive)
 inside(f.button,f.panel);inside(f.button,f.footer);inside(f.icon,f.button)
 assert(f.button.w==math.floor(36*f.scale) and f.button.h==f.button.w)
 assert(f.icon.image=='ui/skins/default/dev/refresh_icon.png' and not f.flame.visible)
 assert(f.button.tooltip=='xatw3_refresh_tooltip')
 for _,b in ipairs({f.recruit,f.load,f.province}) do clear(f.button,b,math.ceil(8*f.scale)) end
 if obstacle then clear(f.button,obstacle,math.ceil(8*f.scale)) end
end
local function test(name,fn) fn();passed[#passed+1]=name end

test('hidden_lord_page_cannot_supply_hero_target',function()
 local f=fixture();assert(f.ui.selected_subtype=='supported')
 f.lords.visible=false;f.agents.visible=true
 local tab=f.comp('wizard',f.agents);tab.state='selected'
 f.ui.refresh_buttons();assert(f.ui.selected_subtype==nil and not f.button.interactive)
 -- The hidden lord tab still reports visible and selected, as in the engine.
 assert(f.lord_tab.visible and f.lord_tab.state=='selected')
 f.runtime.subtypes.hero='dignitary';f.runtime.supported=function(k) return k=='supported' or k=='hero' end
 tab.state='active';local ordinary=f.comp('dignitary',f.agents);ordinary.state='selected'
 f.ui.refresh_buttons();assert(f.ui.selected_subtype=='hero' and f.button.interactive)
 f.agents.visible=false;f.lords.visible=true;f.ui.refresh_buttons();assert(f.ui.selected_subtype=='supported')
 f.lords.visible=false;f.ui.refresh_buttons();assert(f.ui.selected_subtype==nil and not f.button.interactive)
end)
test('icon_scales_and_offsets',function() for _,s in ipairs({0.75,1,1.5}) do visible(fixture(s,123,271)) end end)
test('native_controls_avoided_without_enumerating_rebuilt_cards',function()
 local f=fixture();f.load.x=568;f.load.y=430;f.load.w=120;f.load.h=49
 f.panel.ChildCount=function() error('Candidate-card traversal is unsafe during rebuild') end
 f.ui.refresh_buttons();visible(f,f.load);assert(f.button.x>=696)
end)
test('narrow_gap_left_fallback_and_no_space',function()
 local f=fixture();f.load.x=568;f.load.y=430;f.load.w=135;f.load.h=49
 f.ui.refresh_buttons();visible(f);assert(f.button.x==711)
 local wall=f.load;wall.w=252;wall.h=50
 f.ui.refresh_buttons();visible(f,wall);assert(f.button.x<f.recruit.x)
 f.province.x=0;f.province.w=260;f.province.h=50;f.ui.refresh_buttons();assert(not f.button.visible)
end)
test('hidden_controls_ignored_disabled_controls_reserved',function()
 local f=fixture();local b=f.load;b.x=568;b.y=430;b.w=252;b.h=50
 b.visible=false;f.ui.refresh_buttons();assert(f.button.x==568)
 b.visible=true;b.interactive=false;f.ui.refresh_buttons();visible(f,b);assert(f.button.x<260)
end)
test('alternate_anchor_reflow_and_reuse',function()
 local f=fixture();f.recruit.visible=false;f.recruit=f.comp('button_confirm',f.footer,260,429.5,300,51)
 f.ui.refresh_buttons();visible(f);local x,y=f.button.x,f.button.y
 for _,c in ipairs({f.panel,f.holder,f.footer,f.recruit,f.load,f.province}) do c.x=c.x+71;c.y=c.y+53 end
 f.ui.refresh_buttons();visible(f);assert(f.button.x==x+71 and f.button.y==y+53 and f.creations==1)
end)
test('missing_anchors_icon_and_bounds_hide',function()
 for _,k in ipairs({'footer','recruit','icon','bounds'}) do
  local f=fixture()
  if k=='footer' then f.footer.visible=false elseif k=='recruit' then f.recruit.visible=false
  elseif k=='icon' then table.remove(f.button.children,1) else f.footer.h=10 end
  f.ui.refresh_buttons();assert(not f.button.visible)
 end
end)
test('busy_locked_unverified_unsupported_disable',function()
 for _,k in ipairs({'busy','locked','unverified','unsupported'}) do
  local f=fixture()
  if k=='busy' then f.ui.submitting=true elseif k=='locked' then f.runtime.state.locked=true
  elseif k=='unverified' then f.runtime.refresh_verified=false else f.ui.selected_subtype='other';f.lord_tab.state='active' end
  f.ui.refresh_buttons();assert(f.button.visible and not f.button.interactive)
 end
end)
return passed
