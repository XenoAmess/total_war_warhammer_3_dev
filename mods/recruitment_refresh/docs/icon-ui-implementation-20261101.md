# Icon UI implementation, 2026-11-01

Version 0.2.2 replaces the text button with the game's small square refresh icon. The controller reserves native Recruit/Confirm, Load Character and province-cycle rectangles, searches the right side then the left, and hides the icon when neither side fits. The tooltip retains the localized explanation. Successful refresh remains a single click with no modal.

Native inspection also found that hidden `lord_parent` pages retain selected visible child tabs. Selection now resolves within the visible `agent_parent` or `lord_parent`, clearing the prior target before resolving the current page. Empty special recruitment pages cannot borrow a hidden lord selection.

Offline validation: 73 shared tests and 55 Mod tests passed, Lua 5.1 compilation, deterministic build and pack readback. Geometry tests cover 75%, 100% and 150% scales, native controls, constrained widths, hidden controls, and page switching. These are controller tests, not evidence of rendering at every scale. Final native acceptance and publication are recorded separately.

## Local model review

Machine: `pc-20260924rtuf-f11af23c08`. Endpoint/model and fixed three-message request format follow the repository configuration. Requests, SSE, usage and receipts are retained under `D:/workspace/.codex-wh3-runtime/icon-media-20261101/models/`.

Four independent tasks were attempted, with six HTTP POSTs in total and peak client concurrency two. Icon implementation was adopted with owner corrections; its broad tree traversal was subsequently removed in favor of the user's native-controls-only scope. The proposed geometry tests were rejected and rewritten because the candidate mocks and assertions did not exercise the implementation correctly. Interface diagnostics were not treated as a proven diagnosis. Category selection had two transport timeouts, then an HTTP 200 completed response with an invalid output schema; its patch was rejected because it compared UI wrappers by identity, removed the native agent-tab fallback, and proposed calls missing from the supplied test fixture. The owner implemented and validated the visible-page fix after the unsuccessful attempts. No truncated candidate was adopted.
