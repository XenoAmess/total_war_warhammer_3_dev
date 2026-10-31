# Move Capital

**ID:** `move_capital`
**Version:** `0.1.0`

This mod provides a dedicated UI and logic for moving the faction capital to a selected settlement in the main Warhammer campaign.

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
- **Testing:** Pending minimal real-game acceptance.
- **Release:** Pending workshop upload.
