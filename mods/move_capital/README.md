# Move Capital

**ID:** `move_capital`
**Source candidate:** `0.1.1` (Workshop remains `0.1.0`)

The candidate fixes the native button label rendering outside its bounds. Shared tests (73), Mod tests (48), and final-pack Kislev native UI/transaction regression pass. Two actual gameplay images are included in the repository and prepared for the Workshop gallery and inline description; publication remains pending. See the [fix record](docs/button-label-fix-20261101.md) and [candidate acceptance](docs/acceptance-results-0.1.1.json).

This mod provides a dedicated UI and logic for moving the faction capital to a selected settlement in the main Warhammer campaign.

The existing Workshop item now includes the legacy launcher's required metadata. Actual subscription, download hash, and the installed legacy launcher's native Mod listing were verified for this mod and Recruitment Refresh. The 0.1.0 pack is unchanged. See the [launcher repair record](docs/launcher-repair-20261031.md).

## Features
- **Move Capital:** Select a settlement owned by your faction and move the capital there.
- **Safety Checks:** Ensures the target is a valid settlement, not the current capital, not besieged, and owned by the faction.
- **State Persistence:** Uses a dedicated save key `xatw3_move_capital_state` to track operation status and prevent duplicate or invalid actions.

## Dependencies
- **None.** This mod is standalone and does not require `memreader Plus` or the `Recruitment Refresh` mod.

## Usage
1. Open the settlement panel for a valid target.
2. Click the `Move Capital` button.
3. Confirm the action in the dialog.

## Localization
- **Prefix:** `xatw3mc_`
- **Keys:** `capital`, `capital_tooltip`, `confirm_title`, `confirm_capital`, `error`, `success`, `done`, `failed`, `stale`, `uncertain`.

## Status
- **Development:** Complete.
- **Testing:** Standalone native button/confirmation smoke test passed on the exact release pack. No combined enablement test was requested.
- **Release:** [Public Workshop item 3830651933](https://steamcommunity.com/sharedfiles/filedetails/?id=3830651933). Title, BBCode, cover, dependency list and downloaded pack hash verified. Gameplay screenshots are deferred by the user's publication-priority instruction.
- **Evidence:** [Publication record](docs/workshop-publication.md) and [acceptance results](docs/acceptance-results.json).
