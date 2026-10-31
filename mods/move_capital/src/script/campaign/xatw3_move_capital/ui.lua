local M = {}
local PREFIX = 'xatw3mc_'

function M.new(runtime, logic, environment)
    environment = environment or getfenv(2)
    local core, cm, common = environment.core, environment.cm, environment.common
    local find_uicomponent, UIComponent, CampaignUI = environment.find_uicomponent,
        environment.UIComponent, environment.CampaignUI
    local self = {pending = nil, selected_region = nil, submitting = false, dialog = nil}

    local function text(key) return common.get_localised_string(PREFIX .. key) end
    local function after(callback) cm:callback(callback, 0.1) end

    local function button(id, parent, label, anchor)
        local component = core:get_or_create_component(PREFIX .. id,
            'ui/templates/square_medium_text_button.twui.xml', parent)
        component:SetStateText(text(label))
        component:SetTooltipText(text(label .. '_tooltip'), true)
        component:SetCanResizeWidth(true)
        component:Resize(170, 34)
        component:SetVisible(true)
        local x, y = anchor:Position()
        component:MoveTo(x, y - 45)
        return component
    end

    function self.refresh_buttons()
        if not runtime.initialized then return end
        local faction = cm:get_local_faction_name()
        local root = core:get_ui_root()
        local panel = find_uicomponent(root, 'settlement_panel')
        if panel and panel:Visible() then
            local anchor = find_uicomponent(panel, 'button_rename') or panel
            local b = button('move_capital', panel, 'capital', anchor)
            local eligible = false
            if self.selected_region then
                eligible = logic.capital_eligible(runtime.region(self.selected_region), faction, runtime.capital(faction))
            end
            b:SetInteractive(eligible and runtime.can_act(faction) and not runtime.state.locked and not self.submitting)
        end
    end

    local function show_dialog(message, confirmation)
        local dialog = core:get_or_create_component(PREFIX .. 'confirm_action',
            'ui/common ui/dialogue_box.twui.xml', core:get_ui_root())
        local label = find_uicomponent(dialog, 'DY_text')
        if not label then error('The native confirmation dialog text component is unavailable') end
        label:SetStateText(message)
        find_uicomponent(dialog, 'purchase_options'):SetVisible(false)
        find_uicomponent(dialog, 'both_group'):SetVisible(confirmation)
        find_uicomponent(dialog, 'ok_group'):SetVisible(not confirmation)
        dialog:PropagatePriority(1000)
        dialog:SetVisible(true)
        self.dialog = dialog
    end

    function self.message(title, message)
        self.pending = nil
        show_dialog(text(title) .. '\n\n' .. message, false)
    end

    function self.confirm(request, description)
        self.pending = request
        show_dialog(text('confirm_title') .. '\n\n' .. description, true)
    end

    function self.submit()
        local request = self.pending
        self.pending = nil
        if not request or self.submitting then return end
        self.submitting = true
        -- SP-only: no UI-dependent data is evaluated by remote clients.
        local payload = table.concat({'xatw3mc', '1', request.action, tostring(request.sequence),
            tostring(request.turn), request.target, request.expected}, '|')
        local function dispatch()
            CampaignUI.TriggerCampaignScriptEvent(cm:get_local_faction():command_queue_index(), payload)
        end
        dispatch()
    end

    function self.prepare(action)
        local faction = cm:get_local_faction_name()
        if self.submitting or not runtime.can_act(faction) or runtime.state.locked then return end
        local request = {version = 1, action = action, faction = faction,
            sequence = runtime.state.next_sequence, turn = runtime.turn()}
        if action == 'capital' then
            request.target = self.selected_region
            if not request.target then return end
            request.expected = runtime.capital(faction)
            local allowed = logic.capital_eligible(runtime.region(request.target), faction, request.expected)
            if not allowed then return end
            self.confirm(request, text('confirm_capital'))
        end
    end

    function self.install()
        core:add_listener(PREFIX .. 'panels', 'PanelOpenedCampaign',
            function(context) return context.string == 'settlement_panel' end,
            function() after(self.refresh_buttons) end, true)
        core:add_listener(PREFIX .. 'settlement', 'SettlementSelected', true, function(context)
            self.selected_region = context:garrison_residence():region():name()
            after(self.refresh_buttons)
        end, true)
        core:add_listener(PREFIX .. 'clicks', 'ComponentLClickUp', true, function(context)
            if context.string == 'button_tick' or context.string == 'button_cancel' then
                local ancestor = UIComponent(context.component)
                for _ = 1, 12 do
                    if ancestor:Id() == PREFIX .. 'confirm_action' then
                        self.dialog:SetVisible(false)
                        if context.string == 'button_tick' then self.submit() else self.pending = nil end
                        return
                    end
                    local parent = ancestor:Parent()
                    if not parent then break end
                    ancestor = UIComponent(parent)
                end
            end
            if context.string == PREFIX .. 'move_capital' then self.prepare('capital'); return end
        end, true)
        runtime.on_result = function(result)
            self.submitting = false
            local message = text('failed')
            if result.status == 'SUCCEEDED' then message = text('done')
            elseif result.reason == 'stale' then message = text('stale')
            elseif result.status == 'UNKNOWN' then message = text('uncertain') end
            local function finish()
                self.message(result.status == 'SUCCEEDED' and 'success' or 'error', message)
                after(self.refresh_buttons)
            end
            finish()
        end
        self.refresh_buttons()
    end

    return self
end

return M
