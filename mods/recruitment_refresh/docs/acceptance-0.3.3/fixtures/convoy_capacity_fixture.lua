local faction=cm:get_local_faction();local expression='FactionCaravansContext.MaximumCaravans'
local before=common.get_context_value('CcoCampaignFaction',faction:command_queue_index(),expression)
local button=assert(find_uicomponent(core:get_ui_root(),'military_convoys','master_panel','hire_add_master_button'))
local evidence={fixture='Complete vanilla wh3_dlc23_tech_chd_industry_22, whose maximum_caravans_mod effect grants +1 active convoy. This is not a full research playthrough.',capacity_before=before,native_hire_state_before=button:CurrentState(),active_convoys=cm:model():world():caravans_system():faction_caravans(faction):active_caravans():num_items(),package_sha256=xatw3_test.package_sha}
assert(before==1 and evidence.active_convoys==1 and evidence.native_hire_state_before=='inactive')
cm:instantly_research_technology(faction:name(),'wh3_dlc23_tech_chd_industry_22',false)
cm:callback(function()
 evidence.capacity_after=common.get_context_value('CcoCampaignFaction',faction:command_queue_index(),expression);assert(evidence.capacity_after==2)
 xatw3_test.save('vanilla-convoy-capacity-fixture',evidence);xatw3_test.record('VANILLA_CONVOY_CAPACITY_FIXTURE 1->2')
end,1)
