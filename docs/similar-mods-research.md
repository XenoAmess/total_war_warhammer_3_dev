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

## 原生候选清理路径已取得成功证据

从本机 9.0.4 引擎的自然轮换调用链定位到专用候选清理、非空条目整理和列表尾部清理函数。用公开源码的 memreader Plus 0.15.1 调用这些引擎函数；本项目 Lua 不直接写人物对象或容器内存。原生辅助库来自作者 GitHub Release，SHA-256 为 `9f451aac6dab4e05d597a3c2102272f79887c85f0338e9b880f374ec7594f3ab`。

实机测试存档中首先精确删除此前额外生成的 `16857`，波耶池从 4 人恢复到 `1411,1412,1413`，三名原候选背景技能保持。随后加载本项目新的生产模块：

- 领主请求序号 3：`1411,1412,1413` 全部替换为 `16858,16859,16860`，返回 `SUCCEEDED, completed=3`。
- 事务官请求序号 4：`1414,1415,1416` 全部替换为 `16861,16862,16863`，返回 `SUCCEEDED, completed=3`。
- 两类之后各连续刷新 10 次，每次均成功替换 3 人；池大小始终为 3，资金始终为 6000。生成者的姓名 key 和背景技能均非空，旧 ID 已离池。

证据是仓库外 `acceptance/native.log` 的 `TARGETED_POOL_REMOVAL_PASS`、`NATIVE_FULL_LORD_REFRESH_PASS`、`NATIVE_FULL_HERO_REFRESH_PASS` 和 `NATIVE_TEN_LORD_AND_HERO_REFRESHES_PASS`。本轮使用热加载生产源码和独立夹具；正式包的 UI、真实招募、保存重载和完整发布验收仍在继续，不能仅由这些后台接口测试宣布已发布。

后续 UI 实验：真实领主按钮请求 25 返回成功，旧 `16918,16919,16920` 被替换为 `16924,16925,16926`；但打开的原生面板仍缓存旧 ID。测试脚本查询旧卡片姓名时，在引擎 `+0x249b323` 读取 NULL+0x30 崩溃，之后最终退出码为 `0xc0000409`。memreader 的原始报告明确标出脚本线程、CCO `Call`、旧 ID `16918`，使问题可定位为旧 UI 上下文访问。已改为关闭原生面板、延迟确认关闭后执行、再重开面板的顺序，并增加界面未关闭就不提交的检查；尚需完成本轮正式包复验。

界面修正后的实机证据：

- 冷启动时正式 mod 包与 Steam 下载的 memreader Plus 均成功加载，测试 movie 包仅有命令记录器，没有内嵌生产源码。随后迭代 UI 关闭顺序时热加载了更新的 `ui.lua`，所以最终 UI 修改仍需另做正式包冷启动复验。
- `ClosePanel("character_panel")` 单独调用没有完成 HUD 招募页的关闭；补上原版 `CloseCurrentHUDPanel()`，并等待关闭动画结束、面板不可见后才提交。
- 领主按钮完成请求 3 后，重开的卡片为 `16858,16859,16860`，与模型一致；三人的真实姓名与头像路径都能读取。`16858` 经原生招募按钮部署为人物 `1065`，等级 1，背景技能保持，资金 `6000→5250`，军队数增加 1。
- 事务官界面按 agent 类型 `dignitary` 分页，不按 `wh3_main_ksl_patriarch` 分页；新增唯一匹配的类别解析和重开恢复。测试夹具先在独立存档中给基斯里夫建立正常的二级神殿，以满足原版英雄招募要求；生产代码没有绕过建筑和容量限制。
- 牧首按钮完成请求 4 后，重开的卡片为 `16862,16863,16864`，姓名与头像路径可读。`16862` 经原生招募按钮部署为人物 `1067`，等级 1，保持 `disciplined` 背景技能，资金 `5250→4900`，地图人物数增加 1。

当前新增证据标记为 `LORD_UI_REFRESH_AND_REOPEN_PASS`、`REFRESHED_LORD_NORMAL_RECRUITMENT_PASS`、`HERO_UI_REFRESH_AND_REOPEN_PASS`、`REFRESHED_HERO_NORMAL_RECRUITMENT_PASS`。后续继续做人物保护、过回合和保存重载，而不是将这轮中间结果当最终发布验收。
