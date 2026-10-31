# 迁移首都：旧启动器修复

既有条目 `3830651933` 已补齐旧启动器依赖的 `pack_name`、`game_version` key-value。远端返回规范拼写 `PACK_NAME`，旧启动器会转小写处理。修复没有重新上传游戏包；`0.1.0` 包名及 SHA-256 保持 `xatw3_move_capital.pack`、`ec85a9689efe42d4e0435157a952fd1a5fe8247d7743878f18195669064399c4`。

已实际订阅并下载，Steam 标志由 4（仅安装缓存）变为 5（已订阅且已安装），哈希一致。使用本机旧启动器 3.25.3 自带 Electron/greenworks 的 `getModInformation` 查询，已返回本 Mod 和独立的招募刷新 Mod；本 Mod 显示 `subscribed=true`、`up_to_date=true`、`conflicted=false`，包来自工坊目录。

本轮没有启动游戏，也没有把原生接口读取等同 GUI 截图。旧启动器接口在离线时返回 No Connection，必要在线验证完成后已恢复主动离线；最终新鲜回执时间为 2026-10-31 15:00:22 UTC，Steam 普通启动且 CEF 调试端口关闭。见[机器可读回执](launcher-repair-20261031.json)。

共用工具新增元数据读取、重复键、大小写规范、失败停止及人工实时账号确认校验，72 项通过。[模型使用记录](local-model-launcher-repair-20261031.json)为两个 Mod 共用同一批两次请求，不重复计数。
