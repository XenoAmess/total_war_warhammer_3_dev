local M = {}
local policy = require('script.campaign.xatw3_campaign_utilities.recruitment_policy')
local function is_selected(state)
    return state == 'selected' or state == 'selected_hover'
end
local PREFIX = 'xatw3_'

function M.new(runtime, logic, environment)
    environment = environment or getfenv(2)
    local core, cm, common = environment.core, environment.cm, environment.common
    local find_uicomponent, UIComponent, CampaignUI = environment.find_uicomponent,
        environment.UIComponent, environment.CampaignUI
    local self = {selected_subtype = nil}
    local function text(key) return common.get_localised_string(PREFIX .. key) end
    local function after(callback) cm:callback(callback, 0.1) end

    local function caravan_panel()
        local root = core:get_ui_root()
        for _, key in ipairs({'cathay_caravans', 'cp1_cth_bhashiva_caravans', 'military_convoys'}) do
            local panel = find_uicomponent(root, key)
            if panel and panel:Visible() then return panel end
        end
    end

    local function active_categories(panel)
        local holder = panel and find_uicomponent(panel, 'lords_and_agents_holder')
        if not holder then return nil end
        local agents = find_uicomponent(holder, 'agent_parent')
        local lords = find_uicomponent(holder, 'lord_parent')
        if agents or lords then
            return agents and agents:Visible() and agents
                or lords and lords:Visible() and lords or nil
        end
        return holder
    end

    local function selected_category(panel)
        local ok, id = pcall(function()
            local categories = active_categories(panel)
            if not categories then return nil end
            local list = find_uicomponent(categories, 'list_box') or categories
            if not list:Visible() then return nil end
            local selected, count = nil, 0
            for index = 0, list:ChildCount() - 1 do
                local child = UIComponent(list:Find(index))
                if child and child:Visible() and is_selected(child:CurrentState()) then
                    selected, count = child:Id(), count + 1
                end
            end
            if count == 1 and type(selected) == 'string' and selected ~= '' then return selected end
        end)
        if ok then return id end
    end

    local function selected_lore(panel)
        local ok, result = pcall(function()
            local root = panel and find_uicomponent(panel, 'general_selection_panel')
            if not root or not root:Visible() then return nil end
            root = find_uicomponent(root, 'main_holder')
            if not root or not root:Visible() then return nil end
            root = find_uicomponent(root, 'lore_select_parent')
            if not root or not root:Visible() then return nil end
            local selected
            for _, path in ipairs({{'wizard_type', 'type_list'}, {'lord_magic_lore_type', 'lore_type_list'}}) do
                local group = find_uicomponent(root, path[1])
                local list = group and group:Visible() and find_uicomponent(group, path[2])
                if list and list:Visible() then
                    for index = 0, list:ChildCount() - 1 do
                        local child = UIComponent(list:Find(index))
                        if child:Visible() and is_selected(child:CurrentState()) then
                            if selected then return nil end
                            selected = {group = path[1], list = path[2], key = child:Id()}
                        end
                    end
                end
            end
            return selected
        end)
        if ok then return result end
    end

    local function button(id, panel, label)
        local convoy = panel:Id() == 'military_convoys'
        local parent = panel
        if convoy then parent = find_uicomponent(panel, 'master_panel') end
        if not parent then return nil end
        local component = core:get_or_create_component(PREFIX .. id,
            'ui/templates/square_small_button.twui.xml', parent)
        component:SetVisible(false)
        local footer = convoy and parent
            or find_uicomponent(panel, 'character_panel_info_holder', 'footer')
        if not footer or not footer:Visible() then return component end
        local anchor = find_uicomponent(footer, convoy and 'recruit_masters_heading' or 'button_raise')
        if not convoy and (not anchor or not anchor:Visible()) then anchor = find_uicomponent(footer, 'button_confirm') end
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
        local scale = ah / (convoy and 30 or 51)
        local size = math.floor((convoy and 28 or 36) * scale)
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
        if convoy then
            -- The native master list has no ordinary recruitment footer. Use
            -- the vacant right edge of its heading, away from hire controls.
            x = math.floor(math.min(ax + aw, right) - size - gap)
            if x < left then return component end
        else
            for position = math.ceil(ax + aw + gap), math.floor(right - size) do
                if position >= left and not overlaps(position, cy, size, size) then x = position; break end
            end
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
        local convoy = find_uicomponent(root, 'military_convoys')
        if convoy and convoy:Visible() then
            self.selected_subtype = nil
            local master = find_uicomponent(convoy, 'master_panel')
            local reserves = master and master:Visible() and find_uicomponent(master, 'reserve_master_listbox')
            local b = button('refresh_candidates', convoy, 'refresh_caravan')
            if not b then return end
            if reserves and reserves:Visible() then self.selected_subtype = 'wh3_dlc23_chd_lord_convoy_overseer' end
            b:SetInteractive(runtime.refresh_verified == true and self.selected_subtype ~= nil
                and runtime.supported(self.selected_subtype) and runtime.can_act(faction)
                and not runtime.state.locked and not self.submitting)
            if not runtime.refresh_verified then b:SetTooltipText(text('refresh_unavailable'), true) end
            return
        end
        local panel = find_uicomponent(root, 'character_panel')
        if panel and panel:Visible() then
            local categories = active_categories(panel)
            local previous_subtype = self.selected_subtype
            self.selected_subtype = nil
            local exact_matches = 0
            if categories then
                for subtype in pairs(runtime.subtypes or {}) do
                    local tab = find_uicomponent(categories, subtype)
                    if tab and tab:Visible() and is_selected(tab:CurrentState()) then
                        self.selected_subtype = subtype
                        exact_matches = exact_matches + 1
                    end
                end
                if exact_matches > 1 then self.selected_subtype = nil end
            end
            local has_list = false
            if categories and exact_matches == 0 then
                -- Shared agent tabs do not identify a lore. Read the current
                -- cards before consulting the incomplete subtype discovery cache.
                local list = find_uicomponent(panel, 'character_list')
                has_list = list ~= nil and list ~= false
                for _, id in ipairs({'listview', 'list_clip', 'list_box'}) do
                    list = list and list:Visible() and find_uicomponent(list, id) or nil
                end
                if list and list:Visible() then
                    local ok, subtype = pcall(function()
                        local selected, selected_count, only, mixed, count = nil, 0, nil, false, 0
                        for index = 0, list:ChildCount() - 1 do
                            local card = UIComponent(list:Find(index))
                            local candidate = card:Visible() and find_uicomponent(card, 'button_wh3')
                            if candidate and candidate:Visible() then
                                local read, key = pcall(function()
                                    local context = candidate:GetContextObject('CcoCampaignCharacter')
                                    return context and context:Call('AgentSubtypeRecordContext.Key')
                                end)
                                if not read or type(key) ~= 'string' or key == '' then key = nil end
                                count = count + 1
                                if count == 1 then only = key end
                                if not key or key ~= only then mixed = true end
                                if is_selected(card:CurrentState()) or is_selected(candidate:CurrentState()) then
                                    selected, selected_count = key, selected_count + 1
                                end
                            end
                        end
                        if selected_count == 1 then return selected end
                        if selected_count == 0 and not mixed then return only end
                    end)
                    if ok and runtime.supported(subtype) then self.selected_subtype = subtype end
                end
                -- An unreadable, unsupported or ambiguous list must not fall
                -- back to a different cached subtype on the same agent tab.
                if not has_list then
                    local selected, matches = nil, 0
                    for subtype, agent in pairs(runtime.subtypes or {}) do
                        local tab = find_uicomponent(categories, agent)
                        if tab and tab:Visible() and is_selected(tab:CurrentState()) then
                            selected, matches = subtype, matches + 1
                        end
                    end
                    if matches == 1 then self.selected_subtype = selected end
                    -- Several known subtypes can share one native agent tab.
                    -- A clicked subtype is reusable only on that active tab.
                    local agent = runtime.subtypes and runtime.subtypes[previous_subtype]
                    local tab = agent and find_uicomponent(categories, agent)
                    if not self.selected_subtype and tab and tab:Visible()
                        and is_selected(tab:CurrentState()) then
                        self.selected_subtype = previous_subtype
                    end
                end
            end
            local b = button('refresh_candidates', panel, 'refresh')
            if policy.caravan(self.selected_subtype) then
                b:SetTooltipText(text('refresh_caravan_tooltip'), true)
            elseif self.selected_subtype and policy.minimum(self.selected_subtype) == 0 then
                b:SetTooltipText(text('refresh_limited_tooltip'), true)
            end
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

    function self.consume_request(request, token)
        local pending = self.single_player_request
        if not pending or pending.token ~= token then return nil end
        for _, field in ipairs({'version', 'action', 'sequence', 'turn', 'target', 'faction'}) do
            if request[field] ~= pending.request[field] then return nil end
        end
        self.single_player_request = nil
        return pending.request
    end

    function self.submit(request)
        if not request or request.action ~= 'refresh' or self.submitting then return end
        self.submitting = true
        if cm.is_multiplayer and cm:is_multiplayer() then
            if not runtime.multiplayer or not runtime.multiplayer.submit('xatw3_campaign_utilities', request) then
                self.submitting = false
                self.message('error', text('multiplayer_unavailable'))
            end
            return
        end
        -- The engine truncates UITrigger strings at 256 bytes. In SP the frozen
        -- complete request stays local; the event carries a one-use reference.
        self.single_player_counter = (self.single_player_counter or 0) + 1
        if self.single_player_counter >= 16000000 then self.submitting = false; return end
        local token = 'sp' .. tostring(self.single_player_counter)
        local payload = table.concat({'xatw3', '1', request.action, tostring(request.sequence),
            tostring(request.turn), request.target, token}, '|')
        if #payload > 240 then
            self.submitting = false
            self.message('error', text('request_too_large'))
            return
        end
        local frozen = {}
        for _, field in ipairs({'version', 'action', 'sequence', 'turn', 'target', 'faction', 'expected'}) do
            frozen[field] = request[field]
        end
        self.single_player_request = {token = token, request = frozen}
        local function dispatch()
            CampaignUI.TriggerCampaignScriptEvent(cm:get_local_faction():command_queue_index(), payload)
        end
        if request.action == 'refresh' then
            self.reopen = {subtype = request.target,
                category = selected_category(find_uicomponent(core:get_ui_root(), 'character_panel')),
                lore = selected_lore(find_uicomponent(core:get_ui_root(), 'character_panel')),
                button = runtime.subtypes and runtime.subtypes[request.target] == 'general'
                    and 'button_create_army' or 'button_agents'}
            local caravan = policy.caravan(request.target) and caravan_panel()
            if caravan then self.reopen.caravan = caravan:Id() end
            -- Native recruitment cards cache the old character details. Let the
            -- game close the panel and release those contexts before removing them.
            CampaignUI.ClosePanel('character_panel')
            if caravan then CampaignUI.ClosePanel(caravan:Id()) end
            CampaignUI.CloseCurrentHUDPanel()
            local attempts = 0
            local function wait_until_closed()
                local panel = find_uicomponent(core:get_ui_root(), 'character_panel')
                if (panel and panel:Visible()) or caravan_panel() then
                    attempts = attempts + 1
                    if attempts < 30 then after(wait_until_closed)
                    else
                        self.submitting, self.reopen = false, nil
                        self.message('error', text('panel_close_failed'))
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
        if #plan.replace == 0 and (plan.add or 0) == 0 then
            self.message('error', text('no_candidates')); return
        end
        request.expected = plan.fingerprint
        self.submit(request)
    end

    function self.install()
        core:add_listener(PREFIX .. 'panels', 'PanelOpenedCampaign', true,
            function(context)
                if context.string == 'character_panel' or context.string == 'military_convoys' then self.selected_subtype = nil end
                after(self.refresh_buttons)
            end, true)
        core:add_listener(PREFIX .. 'closed', 'PanelClosedCampaign', true,
            function(context)
                if context.string == 'character_panel' or context.string == 'military_convoys' then self.selected_subtype = nil end
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
            elseif result.reason == 'native_pool_unavailable' then message = text('native_pool_unavailable')
            elseif result.reason == 'unresolved_operation' then message = text('uncertain')
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
                    local b
                    if reopen.caravan then
                        b = find_uicomponent(root, 'hud_campaign', 'faction_buttons_docker',
                            reopen.caravan == 'military_convoys' and 'button_convoys' or 'button_caravan')
                    else b = find_uicomponent(root, 'hud_campaign', 'hud_center_docker', reopen.button) end
                    if b and b:Visible() and (b:CurrentState() == 'active' or b:CurrentState() == 'hover') then b:SimulateLClick() end
                    after(function()
                        local function restore()
                            local panel = find_uicomponent(root, 'character_panel')
                            local categories = active_categories(panel)
                            local tab = categories and find_uicomponent(categories, reopen.category or reopen.subtype)
                            if not reopen.category and not tab and categories and runtime.subtypes then
                                tab = find_uicomponent(categories, runtime.subtypes[reopen.subtype])
                            end
                            if tab and tab:Visible() and not is_selected(tab:CurrentState()) then tab:SimulateLClick() end
                            after(function()
                                -- Native lore tabs are rebuilt after their shared class.
                                local panel = find_uicomponent(root, 'character_panel')
                                local lore = panel and panel:Visible() and find_uicomponent(panel, 'general_selection_panel')
                                local holder = lore and find_uicomponent(lore, 'main_holder')
                                if holder then lore = lore:Visible() and holder or nil end
                                local ids = {'lore_select_parent', 'wizard_type', 'type_list', reopen.subtype}
                                if reopen.lore then
                                    -- Lords use lore keys (e.g. wh_main_lore_death),
                                    -- while hero tabs can use agent subtype keys.
                                    ids = {'lore_select_parent', reopen.lore.group, reopen.lore.list, reopen.lore.key}
                                end
                                for _, id in ipairs(ids) do
                                    lore = lore and lore:Visible() and find_uicomponent(lore, id) or nil
                                end
                                if lore and lore:Visible() and not is_selected(lore:CurrentState()) then lore:SimulateLClick() end
                                self.selected_subtype = nil
                                after(finish)
                            end)
                        end
                        if reopen.caravan then
                            local parent = find_uicomponent(root, reopen.caravan)
                            if reopen.caravan == 'military_convoys' then
                                local master = parent and parent:Visible() and find_uicomponent(parent, 'master_panel')
                                local slot = parent and parent:Visible() and find_uicomponent(parent, 'master_slot')
                                if master and not master:Visible() and slot and slot:Visible() then slot:SimulateLClick() end
                                after(finish)
                                return
                            end
                            local purchase = parent and parent:Visible() and find_uicomponent(parent,
                                'caravans_panel', 'reserves_listview', 'add_caravan_button', 'button_purchase')
                            if purchase and purchase:Visible() then purchase:SimulateLClick() end
                            after(restore)
                        else restore() end
                    end)
                end)
            else finish() end
        end
        self.refresh_buttons()
    end

    return self
end

return M
