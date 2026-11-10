# Changelog

## 0.3.0 — 2026-11-11（已发布）

- 增加实验性多人同步：所有端关闭人物面板、比对包/依赖/候选状态，统一执行并核对结果；重复请求和中断保护覆盖两个 Mod。
- 类型检查使用请求派系，候选指纹覆盖保护资格和生成参数；补员性别模板按稳定 ID 选取，避免枚举顺序造成差异。
- 修复游戏事件长度截断：单机使用一次性短引用传递冻结请求，联机使用小分片，避免完整候选快照被截成失效请求。
- 单机继续单击直接刷新、不足 3 人补足、保护特殊候选；商队/车队仍禁用。
- 按用户要求不做联机实机验收，不据离线模拟宣称已验证多人稳定性。见[协议与限制](../../docs/multiplayer-transport.md)。

## 0.2.4 — 2026-11-05

相对工坊 0.2.2，包含未单独发布的 0.2.3 修复：

- 手动刷新将选中的非空普通招募子类型补足到至少 3 名。已有更多候选时保持人数，重复刷新不持续增加。
- 受保护人物保留；原版费用、容量、建筑及内容解锁检查保持。空池和特殊招募不扩充。
- 增加精确引擎构建校验，已验证 Windows x64 9.0.4 / 9.0.5；未验证构建禁用原生刷新。
- 商队、车队类型在支持检查、生成及原生定位前拒绝，避免误入普通候选刷新。
- 改善原生池校验失败及面板关闭失败提示，保留部分完成、结果不明时的锁定保护。
- 9.0.5 基斯里夫离线实机验证 1→3、2→3、5→5、保护人物保留、新增候选正常招募及按钮避让。未单独验证用户截图中的纳垢英雄，不宣称全种族兼容。

Refresh now fills a selected nonempty ordinary subtype pool to at least three candidates. Larger pools retain their size; protected characters and normal recruitment requirements remain. This release also adds verified engine-build checks, excludes caravan/convoy recruitment, and clarifies validation errors. Native regression passed on Kislev in Windows x64 game 9.0.5.

完整工坊中英双语更新说明见 [change-notes.txt](workshop/change-notes.txt)，实机记录见 [0.2.4 验收](docs/candidate-count-0.2.4.json)。
