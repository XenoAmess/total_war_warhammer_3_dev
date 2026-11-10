# 0.3.0 已公开发布（2026-11-11）

已更新原工坊条目 [3830548217](https://steamcommunity.com/sharedfiles/filedetails/?id=3830548217)，中英更新说明、公开正文、图库、启动器元数据及真实订阅下载包哈希均已核对。联机为实验性实现，按用户要求未做联机实机验收；单机验收见对应精确包记录。Steam 已恢复普通客户端主动离线，临时调试端口关闭。[发布回执](workshop-publication-0.3.0.json)。以下为历史记录。

# 0.2.4 候选人数与兼容性更新

2026-11-05 已在[既有工坊条目](https://steamcommunity.com/sharedfiles/filedetails/?id=3830548217)公开发布 0.2.4，包含此前未单独发布的 0.2.3 修复。[中英双语更新说明](../workshop/change-notes.txt)已通过 SubmitItemUpdate 提交，公开 changelog 页面可读到 0.2.4 和新增候选测试说明。正文逐字核对、启动器元数据及原有三张图片核对通过；真实订阅包 47758 字节，SHA256 `a2bbf8e5ed3e69fe9f115ec5f56c2b2d5795811c24ea2e0d7120ca23c685a2aa` 与实机验收包一致。

发布使用用户本轮新鲜的账号空闲确认，未复用旧确认或把 429 当作空闲。首次离线切换未取得读回；发布 Python 进程退出后重新请求离线成功，普通 Steam 客户端重启后再次确认主动离线，临时调试端口关闭。没有启动游戏。详见[0.2.4 发布回执](workshop-publication-0.2.4.json)。

## 0.2.2 实机 UI 与图片更新

已更新既有工坊条目，包 SHA 与最终实机验收一致。3 张实机图片已提交仓库、上传工坊图库，并嵌入 BBCode 正文。公开正文逐字核对；图库经无缓存 Steamworks 查询、Steam CDN 原图下载及 SHA-256 比对通过。真实订阅安装标志为 5，下载包哈希一致。Steam 已恢复主动离线，临时调试端口关闭。详见[本版回执](workshop-publication-0.2.2.json)。

匿名 HTML 页面本次返回 429，未将其记为像素或页面展示验收；当前验证范围与诊断保留在回执。

## 历史记录

# 招募候选刷新工坊更新

2026-10-31 14:56 UTC 已在[既有条目](https://steamcommunity.com/sharedfiles/filedetails/?id=3830548217)发布 `0.2.1 Alpha`。新包 41,622 字节，SHA-256 `80f89c5faf3f0ff7c9e8873190f1f0d07dc38590b84e632983716a31210ef5a0`；正文和远端启动器元数据核对通过，真实订阅下载标志为 5，下载哈希一致。旧启动器自带原生接口同时列出了本 Mod 和迁移首都，均已订阅且最新，路径均来自工坊。

用户本轮明确授权[新包的 L2/L3 延期](publication-waiver-0.2.1-20261031.json)，并在公开状态接口限流时实时确认其他机器上的游戏已退出；原文、原始时间及 `USER_CONFIRMED_IDLE` 来源保留。最终普通 Steam 客户端在 15:00:22 UTC 的新鲜原生回执为主动离线，CEF 调试端口关闭。新[发布回执](workshop-publication.json)与[启动器修复记录](launcher-repair-20261031.json)区分已完成的订阅/原生接口验证与仍待补的游戏实测和截图。

## 0.2.0 历史

2026-10-31 已公开更新既有条目：[招募候选刷新 | Recruitment Refresh](https://steamcommunity.com/sharedfiles/filedetails/?id=3830548217)，版本 `0.2.0 Alpha`。标题、新封面、刷新专属内容与[独立 BBCode](../workshop/description.bbcode)均已上传，正文链接到独立迁都 Mod。

Steam 成功回调和匿名公开查询均通过；逐项核对了账号、游戏、公开可见性、标题、正文、前置依赖、版本日志、封面哈希和实际下载包哈希。必需物品只有 memreader Plus `3811098873`。新包 39,458 字节，SHA-256 `a35b030c1dc1b5de7b72900d9ec25744bf3acbc6c4a5145879efa6a97cc48481`。完整回执与证据哈希见[0.2.0 机器可读发布记录](workshop-publication-0.2.0.json)。

本次按用户“先发布、截图另补”的明确指令，使用[精确包延期记录](publication-waiver-20261031.json)延期 L2/L3，保持原始 IN_PROGRESS。离线测试通过不代表本次完整实机流程通过，旧包实测也未用来替代新包验收。待显卡恢复后继续单独启用测试并补传功能截图、图库和正文内嵌图片。

发布前均重新检查账号空闲，未顶掉其他机器。上传工具对已存在的依赖返回 EResult 29 的情况已修复并验证。发布 SDK 退出后完成主动离线恢复，普通 Steam 客户端的新鲜原生状态回执为离线，临时 CEF 调试端口已关闭。最初网页限流已解除，最终公开页面核验通过。

原 0.1.0 合并版本发布回执保存在 [历史记录](workshop-publication-0.1.0-combined.md)。
