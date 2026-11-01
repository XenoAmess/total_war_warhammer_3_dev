# Native button label fix, 2026-11-01

Actual 9.0.4 rendering of 0.1.0 placed the localized Move Capital label outside its button. Version 0.1.1 sets text on the native `button_txt` child, resets root and child docking, contains and centers the child, and hides the decorative flame. Confirmation and capital transactions are unchanged.

Validation: 73 shared tests and 48 Mod tests passed, including actual controller geometry, reuse/reposition and missing-label hiding, Lua 5.1 compilation, deterministic build and pack readback. Final native acceptance is recorded separately.

Local-model task `capital-label` received the current source, tests, contract and native diagnosis before implementation. One HTTP POST completed with a valid candidate. The owner adopted its child-label construction with corrections: retain tooltip, reset docking, center text, use `button_flame`, hide on missing label rather than throwing, and avoid root text. Raw UTF-8 request, SSE and usage receipt are retained at `D:/workspace/.codex-wh3-runtime/icon-media-20261101/models/capital-label/`, machine `pc-20260924rtuf-f11af23c08`. The owner wrote and ran the regression test.
