# 刷新与迁都拆分：0.2.0

原工坊条目 `3830548217` 更新为“招募候选刷新”，只提供普通领主和事务官候选刷新。目录改为 `mods/recruitment_refresh/`，包名 `xatw3_campaign_utilities.pack`、Lua 命名空间和 `xatw3_campaign_utilities_state` 保持，以保留旧存档候选履历。迁都的 UI、适配接口、业务分支及本地化已移出；旧通道收到迁都请求时拒绝，不消耗序号或修改状态。

独立迁都见 [move_capital](../../move_capital/README.md)，无需订阅刷新 Mod 或 memreader Plus。已经写入存档的首都位置保留，不通过拆分自动回滚。

## 本次验证范围

离线检查包括 29 项刷新业务、8 项 UI、3 项原生接口拒绝、5 项类型元数据，共 45 项；共用工具检查另有 42 项。检查旧迁都请求拒绝、候选保护、正常替换、结果不明锁定，以及重新打开招募页的生命周期。本版本正式包为 39,458 字节，SHA-256 `a35b030c1dc1b5de7b72900d9ec25744bf3acbc6c4a5145879efa6a97cc48481`。

按用户要求只进行单独启用的最简实机测试：仅刷新 Mod 加 memreader Plus，加载独立存档，分别刷新一次普通领主/事务官候选并核对新旧 ID、数量和受保护人物，正常招募一名新领主。检查城镇面板不再出现原迁都按钮。此次不做同时启用测试，也不重跑原版完整压力矩阵。

2026-10-31 已公开更新原工坊条目；L0/L1 和 L4 通过。用户明确要求先发布，不再等待显卡显示与截图问题，故本次使用[精确包延期记录](publication-waiver-20261031.json)保留 L2/L3 为 IN_PROGRESS，后续补做单独实机流程与功能截图。发布回执见 [工坊更新](workshop-publication.md) 与 [机器可读记录](workshop-publication.json)。旧合并版本完整验收保留在 [0.1.0 报告](acceptance-report-0.1.0-combined.md) 和 [结果](acceptance-results-0.1.0-combined.json)，不能用来替代当前新包的实机回执。
