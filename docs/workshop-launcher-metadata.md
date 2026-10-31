# 工坊发布与旧启动器元数据

发布工具除普通分类标签外，还须在同一次更新内替换两个 key-value 标签：

| Key | 值 |
| --- | --- |
| `pack_name` | 保持原有的小写 `.pack` 文件名 |
| `game_version` | 已测试游戏版本的 Windows `dwFileVersionMS`，十进制字符串 |

在各 Mod 的 `mod.json` 中显式填写 `workshop.game_version`，格式为四段版本号。当前游戏 `9.0.4.0` 对应 `(9 << 16) | 0 = 589824`；不能填 Mod 版本 `0.2.0`、Steam build ID 或 `dwFileVersionLS=262144`。这个字段只表达指定的游戏版本，不代表新修改已经完成实机验收。不要从机器上新安装的版本自动推定兼容性。

`tools/workshop_metadata.py` 在联网和初始化 SDK 之前校验输入，通过命名的 Steamworks flat API 删除这两个键的旧值，然后各写入一个值；不删除其他键。任一调用失败即停止，不调用提交。成功上传后才将元数据记入 publication-state；已有公开发布记录不会因离线修改而更新。

2026-10-31 对本机旧启动器 3.25.3 的只读分析发现，其 greenworks 使用 `STEAMUGC_INTERFACE_VERSION010` 查询这两个键，原生上传路径也删除并重写这两个键。原发布工具只设置普通 tags，没有执行该步骤。旧启动器的 JavaScript 还会排除已发布但未订阅的条目，因此仅下载文件不能代替订阅验证。

API 语义见 [Valve ISteamUGC](https://partner.steamgames.com/doc/api/ISteamUGC#AddItemKeyValueTag)。本修复的离线测试验证调用参数、重复更新、失败中止和发布前校验；并不证明客户端已经显示条目。完成发布后仍需检查远端 key-value、订阅状态、客户端下载及启动器列表。

已发布条目可使用 `tools/workshop_launcher.py` 的查询与修复函数只更新这两个键，无需重新上传游戏包。查询禁止使用缓存，保留重复键值以便发现旧值未清理；修改后再次查询并严格核对。已匹配的条目不再提交；提交结果不明时不自动重放。该模块不初始化 SDK、不切 Steam 模式，调用方必须显式选择 Mod、核对现有条目作者及 app ID、取得新鲜账号空闲证据，并在必要在线阶段结束后恢复主动离线。
