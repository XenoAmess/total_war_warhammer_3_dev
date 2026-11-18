# 第二批 DLC 授权同步（2026-11-18）

账号 `76561198273714027` 已按用户指令临时联网同步，再恢复普通 Steam 客户端主动离线。账号实时空闲证据、下载状态和离线读回均已保存。[完整结构化记录](dlc-activation-2026-11-18-round2.json)、[最终 SDK 原始清单](dlc-activation-2026-11-18-round2/dlc-after-offline-full.json)、[相对第一批的差异](dlc-activation-2026-11-18-round2/license-diff.json)。

| 本批新增付费 DLC | App ID | 授权／安装读回 |
| --- | --- | --- |
| Nagash — Lords of the End Times | 3589650 | 已拥有、已安装 |
| Thanquol — Lords of the End Times | 3589660 | 已拥有、已安装 |
| Boris Todbringer — Lords of the End Times | 3589670 | 已拥有、已安装 |
| The Glottkin — Lords of the End Times | 3589680 | 已拥有、已安装 |
| Bhashiva — Character Pack | 4399460 | 已拥有、已安装 |

首次在线 SDK 仍返回上批 70 条缓存；普通客户端重启后，新离线 SDK 会话才枚举到 82 条。最终 75 条为已拥有且已安装，没有已拥有但待安装项，没有发出 `InstallDLC` 请求。未观察到必需的本体／DLC 数据传输；清单中的历史下载字节计数不是本批新下载证据。游戏仍为 `9.0.5.0 / build 26403568`，EXE SHA-256 `d2a8a58288bf8bd86768f21ff6be036cebb1916f9c312999c60afc1abe13789f`，与第一批一致。

## 不能把枚举数直接视为付费包数

以下 7 条原始枚举仍显示未拥有／未安装，均保留原状，没有自动购买或把未拥有项强行安装：

| App ID | SDK 名称 |
| --- | --- |
| 1834021 | Blood for the Blood God |
| 1834034 | 30th Anniversary Regiments |
| 1834050 | Gotrek & Felix |
| 1834056 | Catchweb Spidershrine |
| 1834060 | Glade Captain |
| 1834063 | Blood for the Blood God II |
| 2325830 | Shadows of Change 整包 |

其中 `1374300` Blood for the Blood God III 已拥有／已安装；变化之影的 The Changeling `3301110`、Yuan Bo `3301120`、Mother Ostankya `3301130` 三个独立包也已拥有／已安装。上面存在历史兼容、免费内容及整包条目，不能直接解释成还缺 7 个付费玩法包；免费角色的实际游戏内可用性尚未逐一核对。本次“已拥有”结论限定于实际 SDK 和本日保存的官方商店目录，不外推未来新 DLC。

## 两 Mod 的补验状态

此前阻塞爪语者生命／其他法术系、巴什瓦 Sawai 运输将领及四种 Verminlord 的授权缺口已解除。招募刷新继续使用已发布的 `0.3.3` 包，迁都继续使用 `0.2.0` 包；实际场景验收正在进行，授权同步本身不计为 Mod 实机通过。

后续结果归各 Mod 的专属记录，并更新[跨批次补验清单](dlc-acceptance-ledger.md)。原生联机仍需第二端及真实多人环境，购买 DLC 不解除此依赖。本地代码模型仍未提供 `qwen38-coder`，仅列出视频模型；没有候选请求或地址／模型回退。

两 Mod 的本批直接补验已完成并保留夹具与未验范围，见[招募刷新 0.3.4 候选报告](../mods/recruitment_refresh/docs/dlc-compatibility-20261118-round2.md)、[迁都 0.2.0 报告](../mods/move_capital/docs/dlc-compatibility-20261118-round2.json)及[持续验收清单](dlc-acceptance-ledger.md)。授权统计仍是上述实际读回，业务通过不改变 7 条未拥有原始标记。0.3.4 已更新原工坊条目并核对公开页面；订阅包检查因另一台机器正在运行 CK3 待验，最终 Steam 主动离线。
