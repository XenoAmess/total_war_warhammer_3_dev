-- Geometry checks exercise the controller; they do not substitute for rendering.
local passed = {}
local function fixture(scale, dx, dy, text_width)
    scale, dx, dy = scale or 1, dx or 0, dy or 0
    local function comp(id, parent, x, y, w, h)
        local c={id=id,children={},visible=true,x=x or 0,y=y or 0,w=w or 0,h=h or 0}
        function c:Position() return self.x,self.y end
        function c:Dimensions() return self.w,self.h end
        function c:Visible() return self.visible end
        function c:SetVisible(v) self.visible=v end
        function c:SetStateText(v) self.text=v end
        function c:SetTooltipText(v) self.tooltip=v end
        function c:SetInteractive(v) self.interactive=v end
        function c:SetCanResizeWidth(v) self.resize_width=v end
        function c:SetCanResizeHeight(v) self.resize_height=v end
        function c:SetDockingPoint(v) self.docking=v end
        function c:SetDockOffset(x,y) self.dock_x,self.dock_y=x,y end
        function c:Resize(w,h) self.w,self.h=w,h end
        function c:MoveTo(x,y) self.x,self.y=x,y end
        function c:SetTextHAlign(v) self.halign=v end
        function c:SetTextVAlign(v) self.valign=v end
        function c:SetTextXOffset(x,y) self.text_left,self.text_right=x,y end
        function c:SetTextYOffset(x,y) self.text_top,self.text_bottom=x,y end
        function c:TextDimensionsForText() return self.tw,self.th end
        if parent then parent.children[id]=c end
        return c
    end
    local f={root=comp('root'),creations=0,comp=comp}
    f.panel=comp('character_panel',f.root,dx,dy,820*scale,650*scale)
    -- Native info_holder is taller than its root and extends above it.
    f.holder=comp('character_panel_info_holder',f.panel,dx,dy-208*scale,820*scale,754*scale)
    f.footer=comp('footer',f.holder,dx,dy+430*scale,820*scale,50*scale)
    f.recruit=comp('button_raise',f.footer,dx+260*scale,dy+429.5*scale,300*scale,51*scale)
    f.load=comp('button_load_character',f.footer,dx+774*scale,dy+437*scale,36*scale,36*scale)
    f.province=comp('province_cycle',f.footer,dx+13*scale,dy+430*scale,100*scale,49*scale)
    local function find(parent,...)
        for _,id in ipairs({...}) do
            local function descend(node)
                if not node then return false end
                if node.children[id] then return node.children[id] end
                for _,child in pairs(node.children) do
                    local found=descend(child); if found then return found end
                end
                return false
            end
            parent=descend(parent); if not parent then return false end
        end
        return parent
    end
    local core={get_ui_root=function() return f.root end,add_listener=function() end}
    function core:get_or_create_component(id,_,parent)
        if parent.children[id] then return parent.children[id] end
        f.creations=f.creations+1
        f.button=comp(id,parent,0,0,340,30)
        f.label=comp('button_txt',f.button,26,2,287,30)
        f.label.tw,f.label.th=(text_width or 100)*scale,14*scale
        f.flame=comp('button_flame',f.button,0,0,310,30)
        return f.button
    end
    f.runtime={initialized=true,refresh_verified=true,subtypes={},state={locked=false},
        can_act=function() return true end,supported=function(key) return key=='supported' end}
    f.ui=ui_module.new(f.runtime,{}, {core=core,find_uicomponent=find,UIComponent=function(c) return c end,
        cm={get_local_faction_name=function() return 'faction' end},
        common={get_localised_string=function(key) return key end}})
    f.ui.selected_subtype='supported'
    f.ui.refresh_buttons()
    return f
end
local function inside(inner,outer)
    assert(inner.x>=outer.x and inner.y>=outer.y)
    assert(inner.x+inner.w<=outer.x+outer.w and inner.y+inner.h<=outer.y+outer.h)
end
local function clear(a,b)
    assert(a.x+a.w<=b.x or b.x+b.w<=a.x or a.y+a.h<=b.y or b.y+b.h<=a.y)
end
local function visible_layout(f)
    assert(f.button.visible and f.button.interactive)
    assert(f.button.x>f.recruit.x+f.recruit.w)
    inside(f.button,f.panel); inside(f.button,f.footer); inside(f.label,f.button)
    assert(f.label.tw<=f.label.w and f.label.th<=f.label.h)
    assert(f.label.halign=='centre' and f.label.valign=='centre' and not f.flame.visible)
    assert(f.label.dock_x==0 and f.label.text_left==0 and f.label.text_top==0)
    clear(f.button,f.recruit); clear(f.button,f.load); clear(f.button,f.province)
end
local function test(name,fn) fn(); passed[#passed+1]=name end
test('bottom_layout_and_text_fit_at_multiple_scales_and_offsets',function()
    for _,scale in ipairs({0.75,1,1.5}) do
        for _,width in ipairs({64,130}) do visible_layout(fixture(scale,123,271,width)) end
    end
end)
test('alternate_recruit_anchor_and_reflow_reuse_component',function()
    local f=fixture(); f.recruit.visible=false
    f.recruit=f.comp('button_confirm',f.footer,260,429.5,300,51)
    f.ui.refresh_buttons(); visible_layout(f)
    local bx,by=f.button.x,f.button.y
    for _,c in ipairs({f.panel,f.holder,f.footer,f.recruit,f.load,f.province}) do c.x=c.x+71; c.y=c.y+53 end
    f.ui.refresh_buttons(); visible_layout(f)
    assert(f.button.x==bx+71 and f.button.y==by+53 and f.creations==1)
end)
test('native_controls_and_footer_boundary_limit_available_space',function()
    for _,obstacle in ipairs({'load','province'}) do
        local f=fixture(); f[obstacle].x=f.button.x+50; f.ui.refresh_buttons(); assert(not f.button.visible)
    end
    local f=fixture(); f.footer.w=600; f.ui.refresh_buttons(); assert(not f.button.visible)
    f=fixture(); f.load.x=f.button.x; f.load.y=f.footer.y-100
    f.ui.refresh_buttons(); assert(f.button.visible) -- No vertical overlap.
end)
test('missing_or_hidden_anchors_hide_existing_button',function()
    for _,missing in ipairs({'footer','recruit','label','hidden_footer'}) do
        local f=fixture()
        if missing=='footer' then f.holder.children.footer=nil
        elseif missing=='recruit' then f.footer.children.button_raise=nil
        elseif missing=='label' then f.button.children.button_txt=nil
        else f.footer.visible=false end
        f.ui.refresh_buttons(); assert(not f.button.visible)
    end
end)
test('bad_or_oversized_text_measurement_hides_button',function()
    for _,kind in ipairs({'wide','tall','zero','error','nil'}) do
        local f=fixture()
        if kind=='wide' then f.label.tw=1000
        elseif kind=='tall' then f.label.th=100
        elseif kind=='zero' then f.label.tw=0
        elseif kind=='nil' then f.label.tw=nil
        else f.label.TextDimensionsForText=function() error('measurement unavailable') end end
        f.ui.refresh_buttons(); assert(not f.button.visible)
    end
end)
test('refresh_button_disables_while_busy_or_unverified',function()
    for _,kind in ipairs({'busy','locked','unverified','unsupported'}) do
        local f=fixture()
        if kind=='busy' then f.ui.submitting=true
        elseif kind=='locked' then f.runtime.state.locked=true
        elseif kind=='unverified' then f.runtime.refresh_verified=false
        else f.ui.selected_subtype='unsupported' end
        f.ui.refresh_buttons(); assert(f.button.visible and not f.button.interactive)
    end
end)
return passed
