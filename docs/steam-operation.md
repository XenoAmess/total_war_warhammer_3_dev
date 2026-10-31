# Steam 共用操作约定

本流程适用于仓库内全部 Mod，工作约定以根目录 [AGENTS.md](../AGENTS.md) 为准。

普通开发、构建、离线分析和实机验收保持 Steam 主动离线。仅下载必要依赖、上传或更新工坊及必要的客户端下载验证等阶段临时在线，必要操作完成或终止后立即恢复离线。

状态使用后台实时查询，不抢焦点、不移动窗口、不截图。好友隐身、`BLoggedOn=false`、断网、缓存设置、启动参数以及切换调用 ACK 都不能替代主动离线读回。现有探针为相邻仓库的 `../ck3_eternal_recurrence/tools/steam_offline_state_probe.py`；每次启动测试游戏前保存新鲜回执，只接受 `status=offline` 且 `offline_mode=true`。查询未知时修复流程，不将未知记作离线。

参考相邻项目 [steam-ck3-versions skill](../../ck3_eternal_recurrence/skills/steam-ck3-versions/SKILL.md) 的恢复流程及其较新的后台查询约定。查询工具依赖本机 Steam 版本和来源校验，不能将其他机器或旧客户端的回执直接当作本机当前证据。

发布前保持离线，先查询账号是否在其他机器运行游戏。有占用则等待结束后重新检查；状态未知不当作空闲，不能初始化会占用游戏会话的发布 SDK、顶号或强制接管。`tools/workshop.py` 的官方 miniprofile 查询有游戏即拒绝；没有游戏时仍须完整公开 profile 的新鲜空闲证据，不能仅凭缺少游戏字段就判断空闲。

确认空闲后才临时在线，核对实际账号与预期作者一致，执行所选 Mod 的必要操作；结束或终止后恢复主动离线，等待并读回真实状态。仍在转换或返回 unavailable 的即时回执不计成功。临时本机控制通道用完后关闭，正常启动 Steam 并重新确认离线，不通过编辑登录文件、断网或强制结束客户端伪造状态。

各 Mod 的具体时间、客户端版本、账号检查、上传、下载和离线回执保存在各自验收/发布记录，公共文档不混放某个 Mod 的运行证据。已有实例见 [征募与迁都的 Steam 操作记录](../mods/recruitment_and_capitals/docs/steam-operation.md)。
