# 商队与特殊招募反馈分析（0.3.1）

此页保留 0.3.1 的分析结论。后续 0.3.2 的实际实现、冰雪宫廷范围修正及实机验证见[实现记录](special-recruitment-implementation-0.3.2.json)。

本次反馈成立：震旦长牙之路领队和混沌矮人车队领队均不在当前刷新支持范围。当前代码主动拒绝它们；0.3.1 的多法术系修复没有扩展这一范围。本轮仅分析、归档，没有修改功能或更新工坊。

## 对象与直接原因

| 用户描述 | 本机简体中文名 | 人物子类型 |
| --- | --- | --- |
| 长牙之路运输将领 | 督运总督（Caravan Master） | `wh3_main_cth_lord_caravan_master` |
| 混矮商队将领 | 车队监督（Convoy Overseer） | `wh3_dlc23_chd_lord_convoy_overseer` |
| 巴什瓦商队的同类入口 | 至伟虎人雇佣兵 | `wh3_cp1_cth_sawai_caravan` |

前者领导震旦的商队运输贸易；后者领导混沌矮人的资源交换车队。[官方混矮介绍](https://store.steampowered.com/app/2059190/Total_War_WARHAMMER_III__Forge_of_the_Chaos_Dwarfs/)说明 Convoys 用军备换取资源。这里的招募对象虽是领队人物，却不是普通陆军领主候选刷新流程。

1. [logic.lua](../src/script/campaign/xatw3_campaign_utilities/logic.lua) 的 `special_subtype` 按人物 key 包含 `caravan` 或 `convoy` 判断特殊类型。
2. [runtime.lua](../src/script/campaign/xatw3_campaign_utilities/runtime.lua) 的 `supported` 在检查缓存及元数据之前拒绝这些 key；`spawn_candidate` 再复用该检查。
3. [ui.lua](../src/script/campaign/xatw3_campaign_utilities/ui.lua) 只有受支持子类型才能启用刷新。业务候选保护和 [native_pool.lua](../src/script/campaign/xatw3_campaign_utilities/native_pool.lua) 的原生对象定位也各有拒绝检查；强行发请求或预先缓存类型不能取得支持。

这一边界由提交 `ef4da86` 引入，见[当时的排查记录](update-9.0.5-investigation.md)。它是普通池原生路径的资格限制，不能据此声称引擎根本不可能实现商队刷新，也没有证据把它认作上次爪语者问题的同一根因。

本机 9.0.5 原始 DB 的上述三类均为 `auto_generate=true`、`recruitable=false`。因此，仅检查“会自动生成”会把商队混进普通候选范围；`recruitable=false` 也不表示玩家不能在其专属机制中雇用。原版 `wh3_campaign_caravans_core.lua` 同时管理 Cathay 和 Chaos Dwarfs，并在 `CaravanRecruited` 后根据领队的 `background_skill` 查 `traits_to_units` 生成初始护卫队。普通人物换新没有接入完整的商队对象、编队及派遣状态；支持该功能需要单独适配和验收，不能只删除字符串拦截。

## 同类未支持场景

除商队明确排除外，当前类型发现要求原版 `AutoGenerate=true`，且实际候选职业属于普通职业集合。本机 DB 已核对以下特殊来源类型的 `auto_generate=false`，因此当前不会被发现为可刷新类型：

| 场景 | 已核对的类型示例／分类 | 当前原因 |
| --- | --- | --- |
| 基斯里夫冰雪宫廷 | 冰雪女巫、寒霜侍女的冰雪／暴风系 | 训练来源，非普通自动生成 |
| 吸血鬼伯爵血裔 | `vmp_bloodlines` 五类血裔 | 特殊血裔来源，非普通自动生成 |
| 蜥蜴人史兰 | `lzd_slann_mage_priest`，含普通与游牧版本 | 原版选系／仪式来源，非普通自动生成 |
| 混沌特殊晋升 | 恶魔亲王、神尊嗜血狂魔／万变魔君／大不净者／守秘者 | 特殊来源，非普通自动生成 |
| 古墓王王朝国王 | `tmb_dynasties` | 王朝专属类型；不是所有普通古墓王 |
| 海盗海岸科技传奇提督 | `cst_legendary_admirals` | 科技专属类型；不是所有舰队司令 |
| 绿皮科技特殊军阀 | `grn_workshop`，如 Oglok／Raknik | 特殊人物类型；不是普通兽人／地精领主整体禁用 |
| 黑暗精灵黑色方舟 | `wh2_main_def_black_ark` 等 | 非普通自动生成 |
| 高精龙舰提督 | `wh3_dlc27_hef_dragonships` | 特殊舰队类型，非普通自动生成 |
| 食人魔营地暴君 | `wh3_main_ogr_tyrant_camp` | 营地专用类型，非普通自动生成 |
| 鼠人灾祸领主 | `wh3_skv_verminlord` | 特殊类型，非普通自动生成 |

该表是已确认的类型边界，不能解释成每一种都做过游戏内失败复现。事件生成本身不是全局排除条件：某个事件如果使用普通可自动生成类型，仍需按候选履历和原生资格实际判断。其他 Mod 的 key 只要含 `caravan`／`convoy`，当前也会被字符串规则拦截，即使该 Mod 使用了普通职业。

## “刷新后不变”的另外几种情况

- **人物保护。** 唯一／传奇、不朽、受伤、开局特殊人物、已招募过和未知履历人物不会被替换。普通池中其他合格人物仍可刷新；不足 3 人的受保护普通池也可能新增候选，不能把保护等同于整池禁用。
- **空池与内容解锁。** 空池不会凭空补员；刷新不能绕过 DLC、建筑、容量和特殊解锁。容量满了与刷新是否执行是不同问题，不能仅凭招募按钮灰色判断刷新失败。
- **作用域与状态。** 目前仅超凡帝国 `main_warhammer`，不覆盖混沌魔域和序章。非己方回合、待决战斗、执行中、原生构建／依赖校验失败、前次结果不明造成锁定等会拒绝操作。来源不可读或类型混杂的 UI 也不会猜测目标。
- **兵种招募。** 亡者复苏、佣兵、精英兵团等单位候选不属于本 Mod 的领主／事务官刷新对象。

## 验证与记录

重新读取本机 `db.pack`、`data_script.pack` 和 `local_cn.pack`，核对 662 条人物子类型记录及原版商队／训练／史兰脚本。针对 17 个代表类型，用真实生产 Lua 和当前 DB 的 AutoGenerate 值做入口模拟验证：三类商队在任何元数据读取前拒绝，即使缓存为普通将领也不能生成；其余特殊类型在 AutoGenerate 检查拒绝；普通阳系经略使作为对照通过元数据入口。职业值在该模拟中固定为 `general`，不是原生池资格或实机证明。本轮未启动游戏、未尝试删除或替换商队。

结果、源码与游戏包哈希、中文名和本地模型失败记录见[机器可读分析](special-recruitment-scope-20261116.json)。按项目配置尝试本地代码模型一次，接口返回 HTTP 404；诊断发现该地址当前只列出视频模型，不再提供配置的 `qwen38-coder`。未回退旧地址、未采用候选，由主执行者完成分析。Steam 保持主动离线。
