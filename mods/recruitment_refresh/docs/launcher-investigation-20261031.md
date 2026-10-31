# 订阅与启动器列表排查（2026-10-31）

用户截图中，新 CA TWMM 管理器显示 18 个已安装 Mod，包含本 Mod；旧 CA 启动器显示 17 个已订阅 Mod，缺少本 Mod。不能由截图推定这两个列表使用同一数据来源。

旧发布流程已公开上传条目 `3830548217`，并下载校验包 SHA-256，但没有执行 SubscribeItem，也没有下载后启动游戏的证据。下载回执 `GetItemState=4` 表示 Installed，Subscribed 是独立的 bit 1。因此此前的发布/下载校验不等于完整订阅后实机验收。`move_capital` 的既有实机记录来自发布前部署至 data 目录的包，也不是订阅链路。

本机只读分析旧启动器 3.25.3：

- greenworks 的 SDK 010 查询路径读取 `pack_name` 和 `game_version` key-value；原生上传路径先删除旧值再写入。原工具仅设置标题、描述、内容、预览、可见性和普通分类标签，存在元数据兼容缺口。
- 原生地址 `0x1002732e–0x100273aa` 检查两个键；`0x1002d028–0x1002d1b9` 是删除/添加路径。精确 SDK 010 的 vtable offset `0xa8/0xac` 分别为 RemoveItemKeyValueTags/AddItemKeyValueTag。生产修复使用命名 flat API，不调用这些地址。
- 旧启动器 JavaScript `syncData` 还使用 `subscribed || !published` 过滤。未订阅的缓存包可能在新管理器出现而被旧列表排除。
- 原包是 PFH5 type 3 Mod 包，未发现需要改 Movie 包或改包名的证据。本机旧 Launcher 用户目录没有可供重现本次反馈的日志，没有清除用户缓存。

共用发布工具现已加入两个键的写入和失败中止，配置见[元数据约定](../../../docs/workshop-launcher-metadata.md)。这是已实现的兼容修复候选；尚不能宣称远端元数据已修复或订阅端列表恢复。需要发布后查询远端两个键，取得真实 Subscribed 状态，下载同一 SHA，并在旧启动器查看原始 getModInformation 数据及最终列表。

本机运行材料位于 `D:/workspace/.codex-wh3-runtime/workshop-consumer-audit-20261031/`。当前不启动 Steam SDK 或游戏：最近账号查询显示其他机器正在运行 Civilization VI；本机 Steam 进程不存在，不能将其记为已取得主动离线回执。GPU 亦仍未枚举，新的游戏界面验收未完成。
