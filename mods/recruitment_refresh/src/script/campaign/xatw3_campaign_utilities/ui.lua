local M = {}
local PREFIX = 'xatw3_'

function M.new(runtime, logic, environment)
    environment = environment or getfenv(2)
    local core, cm, common = environment.core, environment.cm, environment.common
    local find_uicomponent, UIComponent, CampaignUI = environment.find_uicomponent,
        environment.UIComponent, environment.CampaignUI
    local self = {selected_subtype = nil}
    local function text(key) return common.get_localised_string(PREFIX .. key) end
    local function after(callback) cm:callback(callback, 0.1) end

    local function button(id, panel, label)
        local component = core:get_or_create_component(PREFIX .. id,
            'ui/templates/square_small_button.twui.xml', panel)
        component:SetVisible(false)
        local footer = find_uicomponent(panel, 'character_panel_info_holder', 'footer')
        if not footer or not footer:Visible() then return component end
        local anchor = find_uicomponent(footer, 'button_raise')
        if not anchor or not anchor:Visible() then anchor = find_uicomponent(footer, 'button_confirm') end
        if not anchor or not anchor:Visible() then return component end
        local icon = find_uicomponent(component, 'icon')
        if not icon then return component end
        local flame = find_uicomponent(component, 'button_flame')
        if flame then flame:SetVisible(false) end

        local px, py = panel:Position()
        local pw, ph = panel:Dimensions()
        local fx, fy = footer:Position()
        local fw, fh = footer:Dimensions()
        local ax, ay = anchor:Position()
        local aw, ah = anchor:Dimensions()
        if ah <= 0 or aw <= 0 then return component end
        local scale = ah / 51
        local size = math.floor(36 * scale)
        local gap = math.ceil(8 * scale)
        local icon_size = math.floor(24 * scale)
        local left, top = math.max(px, fx), math.max(py, fy)
        local right, bottom = math.min(px + pw, fx + fw), math.min(py + ph, fy + fh)
        if right - left < size or bottom - top < size then return component end

        -- Only native footer controls: candidate-card trees are rebuilt by the
        -- engine while recruitment opens, so do not enumerate their descendants.
        local blockers = {}
        for _, name in ipairs({'button_raise', 'button_confirm', 'button_load_character', 'province_cycle'}) do
            local native = find_uicomponent(footer, name)
            if native and native:Visible() then
                local x, y = native:Position()
                local w, h = native:Dimensions()
                if w > 0 and h > 0 then blockers[#blockers + 1] = {x = x, y = y, w = w, h = h} end
            end
        end
        local function overlaps(x, y, w, h)
            for _, b in ipairs(blockers) do
                if x < b.x + b.w + gap and x + w + gap > b.x and
                   y < b.y + b.h + gap and y + h + gap > b.y then
                    return true
                end
            end
            return false
        end

        local cy = math.floor(ay + (ah - size) / 2)
        if cy < top or cy + size > bottom then return component end
        local x
        for position = math.ceil(ax + aw + gap), math.floor(right - size) do
            if position >= left and not overlaps(position, cy, size, size) then x = position; break end
        end
        if not x then
            for position = math.floor(ax - size - gap), math.ceil(left), -1 do
                if position + size <= right and not overlaps(position, cy, size, size) then x = position; break end
            end
        end
        if not x then return component end

        component:SetCanResizeWidth(true)
        component:SetCanResizeHeight(true)
        component:SetDockingPoint(0)
        component:SetDockOffset(0, 0)
        component:Resize(size, size)
        component:MoveTo(x, cy)
        icon:SetCanResizeWidth(true)
        icon:SetCanResizeHeight(true)
        icon:SetDockingPoint(0)
        icon:SetDockOffset(0, 0)
        icon:Resize(icon_size, icon_size)
        icon:MoveTo(x + math.floor((size - icon_size) / 2), cy + math.floor((size - icon_size) / 2))
        icon:SetImagePath('ui/skins/default/dev/refresh_icon.png')
        component:SetTooltipText(text(label .. '_tooltip'), true)
        component:SetVisible(true)
        return component
    end

    function self.refresh_buttons()
        if not runtime.initialized then return end
        local faction = cm:get_local_faction_name()
        local root = core:get_ui_root()
        local panel = find_uicomponent(root, 'character_panel')
        if panel and panel:Visible() then
            local categories = find_uicomponent(panel, 'lords_and_agents_holder')
            local previous_subtype = self.selected_subtype
            self.selected_subtype = nil
            if categories then
                -- Hidden native pages retain selected child tabs. Search only
                -- the currently visible page, never the recursive whole holder.
                local agents = find_uicomponent(categories, 'agent_parent')
                local lords = find_uicomponent(categories, 'lord_parent')
                if agents or lords then
                    categories = agents and agents:Visible() and agents
                        or lords and lords:Visible() and lords or nil
                end
            end
            if categories then
                for subtype in pairs(runtime.subtypes or {}) do
                    local tab = find_uicomponent(categories, subtype)
                    if tab and tab:Visible() and tab:CurrentState() == 'selected' then
                        self.selected_subtype = subtype
                    end
                end
                if not self.selected_subtype then
                    local selected, matches = nil, 0
                    for subtype, agent in pairs(runtime.subtypes or {}) do
                        local tab = find_uicomponent(categories, agent)
                        if tab and tab:Visible() and tab:CurrentState() == 'selected' then
                            selected, matches = subtype, matches + 1
                        end
                    end
                    if matches == 1 then self.selected_subtype = selected end
                    -- Several known subtypes can share one native agent tab.
                    -- A clicked subtype is reusable only on that active tab.
                    local agent = runtime.subtypes and runtime.subtypes[previous_subtype]
                    local tab = agent and find_uicomponent(categories, agent)
                    if not self.selected_subtype and tab and tab:Visible()
                        and tab:CurrentState() == 'selected' then
                        self.selected_subtype = previous_subtype
                    end
                end
            end
            if categories and not self.selected_subtype then
                local list = find_uicomponent(panel, 'character_list', 'listview', 'list_clip', 'list_box')
                if list and list:Visible() then
                    local fallback
                    for index = 0, list:ChildCount() - 1 do
                        local card = UIComponent(list:Find(index))
                        local candidate = find_uicomponent(card, 'button_wh3')
                        if candidate and candidate:Visible() then
                            fallback = fallback or candidate
                            if candidate:CurrentState() == 'selected' then fallback = candidate; break end
                        end
                    end
                    if fallback then
                        local ok, subtype = pcall(function()
                            local context = fallback:GetContextObject('CcoCampaignCharacter')
                            return context and context:Call('AgentSubtypeRecordContext.Key')
                        end)
                        if ok and runtime.supported(subtype) then self.selected_subtype = subtype end
                    end
                end
            end
            local b = button('refresh_candidates', panel, 'refresh')
            if not runtime.refresh_verified then b:SetTooltipText(text('refresh_unavailable'), true) end
            b:SetInteractive(runtime.refresh_verified == true and self.selected_subtype ~= nil and runtime.supported(self.selected_subtype)
                and runtime.can_act(faction) and not runtime.state.locked and not self.submitting)
        end
    end

    local function show_dialog(message)
        local dialog = core:get_or_create_component(PREFIX .. 'confirm_action',
            'ui/common ui/dialogue_box.twui.xml', core:get_ui_root())
        local label = find_uicomponent(dialog, 'DY_text')
        if not label then error('The native confirmation dialog text component is unavailable') end
        label:SetStateText(message)
        find_uicomponent(dialog, 'purchase_options'):SetVisible(false)
        find_uicomponent(dialog, 'both_group'):SetVisible(false)
        find_uicomponent(dialog, 'ok_group'):SetVisible(true)
        dialog:PropagatePriority(1000)
        dialog:SetVisible(true)
        self.dialog = dialog
    end

    function self.message(title, message)
        show_dialog(text(title) .. '\n\n' .. message)
    end

    function self.submit(request)
        if not request or request.action ~= 'refresh' or self.submitting then return end
        self.submitting = true
        -- SP-only: no UI-dependent data is evaluated by remote clients.
        local payload = table.concat({'xatw3', '1', request.action, tostring(request.sequence),
            tostring(request.turn), request.target, request.expected}, '|')
        local function dispatch()
            CampaignUI.TriggerCampaignScriptEvent(cm:get_local_faction():command_queue_index(), payload)
        end
        if request.action == 'refresh' then
            self.reopen = {subtype = request.target,
                button = runtime.subtypes and runtime.subtypes[request.target] == 'general'
                    and 'button_create_army' or 'button_agents'}
            -- Native recruitment cards cache the old character details. Let the
            -- game close the panel and release those contexts before removing them.
            CampaignUI.ClosePanel('character_panel')
            CampaignUI.CloseCurrentHUDPanel()
            local attempts = 0
            local function wait_until_closed()
                local panel = find_uicomponent(core:get_ui_root(), 'character_panel')
                if panel and panel:Visible() then
                    attempts = attempts + 1
                    if attempts < 30 then after(wait_until_closed)
                    else
                        self.submitting, self.reopen = false, nil
                        self.message('error', text('failed'))
                    end
                    return
                end
                dispatch()
            end
            after(wait_until_closed)
        else dispatch() end
    end

    function self.prepare(action)
        local faction = cm:get_local_faction_name()
        if self.submitting or not runtime.can_act(faction) or runtime.state.locked then return end
        if action ~= 'refresh' then return end
        local request = {version = 1, action = action, faction = faction,
            sequence = runtime.state.next_sequence, turn = runtime.turn()}
        if not runtime.refresh_verified then self.message('error', text('refresh_unavailable')); return end
        request.target = self.selected_subtype
        if not request.target or not runtime.supported(request.target) then return end
        local pool = runtime.read_pool(faction, request.target)
        if not pool then self.message('error', text('pool_unavailable')); return end
        local plan = logic.plan(pool, faction, request.target)
        if #plan.replace == 0 then self.message('error', text('no_candidates')); return end
        request.expected = plan.fingerprint
        self.submit(request)
    end

    function self.install()
        core:add_listener(PREFIX .. 'panels', 'PanelOpenedCampaign', true,
            function(context)
                if context.string == 'character_panel' then self.selected_subtype = nil end
                after(self.refresh_buttons)
            end, true)
        core:add_listener(PREFIX .. 'closed', 'PanelClosedCampaign', true,
            function(context)
                if context.string == 'character_panel' then self.selected_subtype = nil end
            end, true)
        core:add_listener(PREFIX .. 'clicks', 'ComponentLClickUp', true, function(context)
            if context.string == 'button_tick' or context.string == 'button_cancel' then
                local ancestor = UIComponent(context.component)
                for _ = 1, 12 do
                    if ancestor:Id() == PREFIX .. 'confirm_action' then
                        if self.dialog then self.dialog:SetVisible(false) end
                        return
                    end
                    local parent = ancestor:Parent()
                    if not parent then break end
                    ancestor = UIComponent(parent)
                end
            end
            if context.string == PREFIX .. 'refresh_candidates' then self.prepare('refresh'); return end
            local component = UIComponent(context.component)
            -- Category changes must never retain the last page's refresh target.
            self.selected_subtype = nil
            local ok, subtype = pcall(function()
                local record = component:GetContextObject('CcoAgentSubtypeRecord')
                if record then return record:Call('Key') end
                local character = component:GetContextObject('CcoCampaignCharacter')
                if character then
                    return character:Call('AgentSubtypeRecordContext.Key')
                end
            end)
            if ok and subtype then self.selected_subtype = subtype end
            after(self.refresh_buttons)
        end, true)
        runtime.on_result = function(result)
            self.submitting = false
            local message = text('failed')
            if result.reason == 'refresh_unverified' then message = text('refresh_unavailable')
            elseif result.reason == 'stale' then message = text('stale')
            elseif result.reason == 'no_candidates' then message = text('no_candidates')
            elseif result.status == 'UNKNOWN' or result.status == 'PARTIAL' then message = text('uncertain') end
            local reopen = self.reopen
            self.reopen = nil
            local function finish()
                if result.status ~= 'SUCCEEDED' then self.message('error', message) end
                after(self.refresh_buttons)
            end
            if reopen and (result.status == 'SUCCEEDED' or result.status == 'REJECTED') then
                after(function()
                    local root = core:get_ui_root()
                    local b = find_uicomponent(root, 'hud_campaign', 'hud_center_docker', reopen.button)
                    if b and b:Visible() and b:CurrentState() == 'active' then b:SimulateLClick() end
                    after(function()
                        local panel = find_uicomponent(root, 'character_panel')
                        local tab = panel and find_uicomponent(panel, 'lords_and_agents_holder', reopen.subtype)
                        if not tab and panel and runtime.subtypes then
                            tab = find_uicomponent(panel, 'lords_and_agents_holder', runtime.subtypes[reopen.subtype])
                        end
                        if tab and tab:Visible() and tab:CurrentState() ~= 'selected' then tab:SimulateLClick() end
                        self.selected_subtype = reopen.subtype
                        finish()
                    end)
                end)
            else finish() end
        end
        self.refresh_buttons()
    end

    return self
end

return M
