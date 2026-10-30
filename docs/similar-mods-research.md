# 同类 Mod 源码调查与后续实现

调查日期：2026-10-31。目标仍是招募界面的即时刷新按钮和迁都；此前未完成候选刷新，不能把禁用按钮视为交付。

## 已查阅并拆包的实例

以下文件通过本机 Steam 的 `ISteamUGC.DownloadItem` 下载，仅供阅读，没有订阅、启用或执行第三方 Mod。原始文件和解包内容放在仓库外 `D:\workspace\.codex-wh3-runtime\research`，不转载到本项目。

| 作者发布页 | 本次读到的实现 | 对本项目的意义 |
| --- | --- | --- |
| [Faster Character Refresh](https://steamcommunity.com/sharedfiles/filedetails/?id=2820394157) | 包中仅有 `campaign_variables` 数据和编辑器设置；候选最短/最长存留回合改为 2/3 | 使用引擎自动轮换，不是即时按钮，也没有 Lua 删除候选的实现 |
| [Updated One Turn Refresh Hero Pool](https://steamcommunity.com/sharedfiles/filedetails/?id=3452514536) | `character_recruitment_min_rounds_in_pool=2`、`max_rounds_in_pool=2`、`recruitment_pool_entries_per_category=3`；没有 Lua | 同样依赖回合轮换；作者说明和下载到的表值需要结合回合实际行为理解 |
| [Execute (useless) Lords & Heroes](https://steamcommunity.com/sharedfiles/filedetails/?id=2958113532) | 当前包的 UITrigger 查找 `get_character_by_cqi`，对其家族成员压制永生，再调用 `kill_character(cqi,false)` | 针对有地图人物接口的对象；不能由此推断它可以直接删除从未招募的池内人物 |
| [Innate Trait Picker](https://steamcommunity.com/sharedfiles/filedetails/?id=3814615131) | 作者使用小型原生辅助库读取角色技能树、调整背景技能节点，再调用游戏自身的背景技能接口；逐步检查结果并恢复失败操作 | 现有角色的背景技能不只是一个可任意替换的字符串；为原地重掷候选提供了值得验证的方向 |
| [角色定制台 / Character Customizer](https://steamcommunity.com/sharedfiles/filedetails/?id=3795916051) | 已阅读作者说明：通过独立界面选择角色类型、背景技能与外观后生成角色；本轮尚未拆包 | 提供另一种招募体验，不能当作原生招募池即时替换已经得到验证 |

本机原版数据库的候选存留值为 10/15 回合。两个加速 Mod 的表值已经从实际下载的二进制表中独立解码核对。

## 可追溯文件

| Workshop ID | 文件 | SHA-256 |
| --- | --- | --- |
| 2820394157 | `TLA_refresh.pack` | `545bee333b3c4ad1f0525a5196399c8982c26191fe83d1a90e0cabc97e3cb5b2` |
| 3452514536 | `@refresh.pack` | `1b56d38ac39b5dfc4bb21e7bd11372996d406654d6134928a994324a17212773` |
| 2958113532 | `Freiya_sm0_execute.pack` | `c09fe229ce9320a0e34ebc8ef362e28b98813f741b2c659dbc66dc1b10a2ddbe` |
| 3814615131 | `innate_trait_picker.pack` | `678796810ad8a8309569621042c75a90234b1580a3f13df34b2eca99fea9740f` |

处决 Mod 另有作者的[公开仓库](https://github.com/sm0kin/TW-Mods/tree/35a70003172368d6b478ddf9ebde8d82c7565e98/sm0/!RPFM_my_mods/warhammer_3/sm0_execute)，但实际下载包比该仓库版本新，因此以上实现描述以本次 Steam 下载文件为准。

## 需要改变的判断

1. 之前只尝试通用杀死人物接口，未能证明它支持从未招募的候选。继续重复调用同一路径不能解决问题。
2. “刷新”是用户要求；“必须销毁旧人物 ID 再创建新 ID”是此前实现自行选择的手段。若能在原生招募界面中正确重掷普通候选，并保持数量、正常招募、费用、特殊人物保护及存档一致，内部 ID 不变不应自动判为失败。但不能仅改显示文本冒充重掷。
3. 优先查明游戏自身的候选淘汰/生成机制，同时验证候选原地重掷路径。后台模型、招募后实际效果和保存读回必须与界面一致。
4. 原生扩展是可选技术路线，不能仅因 Lua 通用删除失败就断言不可实现。可参考具有公开源码的 [memreader Plus](https://github.com/PKozdra/memreader_plus)，但在依赖、结构校验和实机验证完成前，不把该路线写成已经成功。

## 实验与验收约束

继续使用独立测试存档。第三方示例源码用于研究机制，不复制没有明确许可的实现或分发其 DLL。若采用原生扩展，应明确支持平台和版本、验证结构后再修改，避免未经识别的内存写入。生产按钮在真实招募刷新通过前保持禁用；工作不会以“禁用成功”收尾。每轮实验记录实际候选内容、招募与存档结果，之后更新设计和验收报告。
