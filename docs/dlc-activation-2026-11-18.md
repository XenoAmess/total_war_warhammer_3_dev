# DLC 授权同步与验证入口（2026-11-18）

本机账号 `76561198273714027` 已临时联网同步授权，随后恢复普通客户端主动离线。联网最初两次 SDK 仍返回旧缓存；客户端重启后的新 SDK 会话才读到新增授权，枚举数由 45 变为 70。枚举包含免费内容和旧作兼容授权，不等于 70 个付费 DLC。

本次同步后检测到以下近期付费授权均为已拥有、已安装；另检测到《战锤 I》基础游戏授权。没有观察到待完成的本体或 DLC 数据传输，现有资源已覆盖这些内容；游戏仍为 `9.0.5.0 / build 26403568`，EXE 哈希未变。

| 内容组 | 实际检测到的近期授权 |
| --- | --- |
| 战锤 I 内容 | Chaos Warriors、Call of the Beastmen、The King and the Warlord、Norsca、Realm of The Wood Elves |
| 战锤 III 种族／领主包 | Ogre Kingdoms、Champions of Chaos、Forge of the Chaos Dwarfs |
| Shadows of Change | The Changeling、Yuan Bo、Mother Ostankya |
| Thrones of Decay | Elspeth、Tamurkhan、Malakai |
| Omens of Destruction | Gorbad、Golgfag、Skulltaker |
| Tides of Torment | Aislinn、Sayl、Dechala |

共 20 项近期付费 DLC；兼容授权重复条目和免费内容未计入。古墓群王、吸血鬼海岸等原有授权仍有效。原始应用 ID、安装读回、购买时间和 Steam 回执见[授权记录](dlc-activation-2026-11-18.json)及[完整同步后清单](dlc-activation-2026-11-18/dlc-after-offline-full.json)。清单中为历史诊断补查的其他 App ID 不作为战锤 DLC 统计。

| 先前验证缺口 | 本次状态 |
| --- | --- |
| 混矮车队、混矮下两 Mod 共同启用 | 已解除授权阻塞并实测；发现并修复独立车队界面缺入口，以及多法术系领主返回错误法术系两处问题 |
| 爪语者、巴什瓦运输将领 | 巴什瓦 `4399460` 仍未拥有，不能直接补测；已检查其安装资源中的界面路径，不冒充实机通过 |
| Verminlord | Thanquol `3589660` 仍未拥有；当前所有权表将四个对应亚种关联到 `wh3_dlc29_loet_thanquol` |
| 其他新增 DLC 与特殊招募家族 | 完成相关元数据与面板路径检查；未逐个运行完整战役或特殊解锁流程 |
| 联机 | 购买 DLC 不替代第二端环境和原生联机验收，本次未进行 |

具体修改与精确包验收：[招募刷新 0.3.3](../mods/recruitment_refresh/docs/dlc-compatibility-20261118.md)、[迁都 0.2.0](../mods/move_capital/docs/dlc-compatibility-20261118.json)。授权同步和补验阶段没有上传创意工坊；随后按用户指令[发布并核对了招募刷新 0.3.3](../mods/recruitment_refresh/docs/workshop-publication-0.3.3.json)，迁都包不变。[后续 DLC 补验清单](dlc-acceptance-ledger.md)保留本批基线、已验范围及下一批待验事项。
