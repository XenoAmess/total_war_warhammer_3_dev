# Move Capital

第二批 DLC 补验：与招募刷新 0.3.4 共同启用，巴什瓦从泰坦谷迁往卡拉克·阿佐恩通过原生按钮及确认验收。建筑、等级、所有权、省会标志、候选与已有运输队保持；后续刷新、雇用、派遣及过回合首都保持通过。城镇转让是准备夹具；普通扫威雇用仍受原版军队上限 1/1 阻止，不计为雇用通过。本 Mod 源码与 0.2.0 包均未改变，见[第二批验收记录](docs/dlc-compatibility-20261118-round2.json)。

**DLC validation, 2026-11-18:** the unchanged 0.2.0 package passed Chaos Dwarf single-player checks with Recruitment Refresh 0.3.3 enabled. Moving Uzkulak's capital to the Great Skull Lakes factory preserved both settlements' buildings, levels, ownership and province-capital flags, recruitment pools and owned convoys. Native convoy dispatch and Death-lore lord hiring at the new capital also passed. The target settlement transfer and vanilla convoy-capacity technology are test fixtures, not conquest or full research acceptance. See [the DLC evidence and limits](docs/dlc-compatibility-20261118.json).

**0.2.0 is published** with experimental multiplayer synchronization; public description, changelog, gallery, launcher metadata and subscribed package hash are verified. See [publication receipt](docs/workshop-publication-0.2.0.json). Multiplayer native acceptance is deliberately excluded by the user; see [protocol, offline coverage and recovery limits](../../docs/multiplayer-transport.md) and [changelog](CHANGELOG.md). The published-version evidence below is historical.

The final 0.2.0 package passed offline tests and isolated Kislev single-player UI/transaction regression on 9.0.5; see [candidate evidence](docs/multiplayer-implementation.json). This does not establish native multiplayer compatibility.

Game update check: 0.1.1 also passed isolated Kislev native UI/transaction checks on **9.0.5.0 / build 26403568**, with the package unchanged. See [compatibility evidence](docs/compatibility-9.0.5.json).

**ID:** `move_capital`
**Version:** `0.2.0` (published)

Version 0.1.1 fixes the native button label rendering outside its bounds. Shared tests (73), Mod tests (48), and final-pack Kislev native UI/transaction regression pass. Two actual gameplay images are committed, uploaded to the Workshop gallery and embedded in its description. Gallery CDN payloads and the real subscribed package match the expected hashes. See the [publication receipt](docs/workshop-publication-0.1.1.json).

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
