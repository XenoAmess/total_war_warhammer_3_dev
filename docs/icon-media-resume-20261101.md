# Native UI and media work awaiting desktop access

The user's current scope is native button/icon avoidance only. Both existing Workshop items must receive actual gameplay gallery images and matching inline BBCode embeds. No final candidate has been uploaded in this work package.

Final candidates built and tested:

| Mod | Version | SHA-256 | Offline tests |
| --- | --- | --- | --- |
| recruitment_refresh | 0.2.2 | b260913929e90fa06df949098d03e5d0c72c291fabd12210a2a4d1f4e94255a2 | 73 shared, 55 Mod |
| move_capital | 0.1.1 | 4d86e9ee1c2ffe12ab13fd9c2da1be5ad8c2bc20c30caf464dbe3e2415ff59f8 | 73 shared, 48 Mod |

Earlier development packs passed native lord refresh (three replaced, count preserved, one sequence, no modal) and capital movement (new capital readback, ownership/level/province-capital preserved). Their screenshots exposed additional page-selection and label-layout bugs. These were fixed afterward, so those earlier screenshots and native outcomes are **not final candidate acceptance**.

Windows later lost access to the interactive desktop: foreground HWND NULL, OpenInputDesktop failed, LogonUI present in active console session 1. The user was asked to restore an unlocked desktop. Game processes were closed gracefully, temporary data packs/user.script/save files removed by exact SHA checks, and preferences restored. Original PNGs, session manifests, logs and rejected development attempts remain under `D:/workspace/.codex-wh3-runtime/icon-media-20261101/`.

## Resume

1. Read current native offline state before each launch. Runtime `launch.py --mod <id>` enforces this and installs the exact frozen production pack plus a separate dispatcher fixture.
2. After frontend readiness, `frontend-continue.lua` uses native `button_start_campaign` to load the isolated baseline save directly. Wait for campaign readiness and the actual loading-screen Continue button; do not run campaign UI commands before the loading screen is dismissed and events have settled. Runtime mouse helper maps logical 1920×1080 to physical 2400×1350 under 125% Windows DPI, with a 0.5-second click hold.
3. Recruitment: recheck lord icon geometry and real refresh with `check-native.lua`, `click-refresh.lua`, `verify-refresh.lua`; inspect ordinary hero page and unsupported special hero page, including switching back to lords. Confirm hidden `lord_parent` cannot supply an active target on the hero page. Complete normal recruitment and persistence regression appropriate to the final UI changes. Do not claim every scale rendered: offline geometry covers 75/100/150%, native baseline is 100%.
4. Capital: `capital-native.lua` selects the other owned city without relocating the camera, pauses before confirmation/after, and verifies the transaction. `capital-continue.lua` advances each pause. Check the corrected text child visually and geometrically on the final 0.1.1 pack. Retain confirmation (only refresh confirmation was removed).
5. Capture actual game client pixels using `capture.py`. Stage final-pack images with `stage-media.py`, which verifies PNG/pack hashes, generates full-size JPEGs strictly below 1 MiB and writes per-Mod manifests. Do not use development-pack screenshots, generated imagery, or mocked UI.
6. Add each image exactly once to that Mod's BBCode, update release notes/README and genuine final acceptance. Commit/push image files before using their raw GitHub URLs.
7. Close game, obtain fresh account-idle evidence, temporarily go online for publishing both existing items, verify public description/gallery and real subscribed download hashes, immediately restore confirmed active offline mode and remove the temporary CEF debug endpoint. No previous native-test waiver matches these candidates.
8. Commit/push publication evidence and verify origin/main contains the final commits.

Runtime scripts are operator aids, not release content. The prior capital 0.1.0 and refresh 0.2.1 publication-state records remain unchanged until actual publication succeeds.
