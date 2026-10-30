# Steam 离线操作约定与本次回执

用户于 2026-10-31 明确要求：开发、构建、分析和实机验收保持 Steam 主动离线；仅下载必要依赖、工坊上传及发布验证等必要操作临时在线，结束或终止后立即恢复离线。根目录 [AGENTS.md](../AGENTS.md) 已记录此约定。

参考相邻项目的 [steam-ck3-versions skill](../../ck3_eternal_recurrence/skills/steam-ck3-versions/SKILL.md) 第 7 步，以及其 `AGENTS.md` 的“Steam 离线模式与账号占用”。其中旧的截图要求已被该项目较新的后台状态确认指令覆盖。本项目不为确认 Steam 状态激活、移动窗口或截图，不把好友隐身、断网、缓存偏好、启动参数或调用成功当成主动离线证据。

本机现成探针为 `../ck3_eternal_recurrence/tools/steam_offline_state_probe.py`。每次启动测试游戏前生成新的独立回执，只接受 `status=offline` 且 `offline_mode=true`；未知客户端版本或查询不可用时不启动。联网发布前也须核对账号占用，不顶掉其他机器。

本次实际恢复：

- `machine_id`: `pc-20260924rtuf-f11af23c08`，由相邻项目的现有机器身份实现实读。
- 时间：`2026-10-30T17:52:27.306465+00:00`，北京时间 2026-10-31 01:52:27。
- Steam：PID `3632`，版本 `11.15.70.27`。
- 读回：`native_current_user_byte`；两次离线原值均为 `1`，两次托盘模式均为 `4`，最终 `status=offline`、`offline_mode=true`。
- 原始回执：仓库外 `D:/workspace/.codex-wh3-runtime/research/steam-mode-after-gooffline-20261031-a01.json`。

仅使用 `-offlinemode` 启动参数的首次尝试没有取得离线回执，未计成功。实际通过当前安装版 Steam 菜单使用的 `SteamClient.User.GoOffline()` 完成切换，再用版本和来源绑定的原生只读探针确认。控制通道仅绑定本机所属 Steam 实例；没有编辑登录文件、调用猜测的 DLL 槽位、断网伪装离线或操作系统登录界面。临时本机 CEF 控制通道留至本次发布流程结束，最终恢复普通离线启动并重新取证。

此前在线实机记录仍保留为真实历史，不能追认为离线验收。后续冻结包冷启动已加入新鲜离线回执检查。
