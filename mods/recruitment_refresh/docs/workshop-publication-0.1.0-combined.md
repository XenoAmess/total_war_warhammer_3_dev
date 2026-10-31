# Steam 创意工坊发布记录

状态：**已公开发布，L0–L4 通过。Steam 已恢复主动离线。**

- 条目：[征募与迁都 | Recruitment Refresh & Move Capital](https://steamcommunity.com/sharedfiles/filedetails/?id=3830548217)
- 条目 ID：`3830548217`；目标 App：`1142710`；作者：`76561198273714027`。
- 版本：`0.1.0 Alpha`；上传完成：2026-10-31 02:05:34 UTC（北京时间 10:05:34）。
- 可见性：`public / 0`；匿名 API 返回 `result=1`、`banned=0`。
- 必需物品：[memreader Plus](https://steamcommunity.com/sharedfiles/filedetails/?id=3811098873)，已通过 AddDependency 成功回调和匿名页面双重核对。
- 内容：仅 `xatw3_campaign_utilities.pack`，42,899 字节，不包含测试夹具、DLL、存档或第三方 Mod。
- 生产源码提交：`cb43cc56f3cadbfaa6d652e3cadf6eb895dd6c90`；正式包 SHA-256：`b25fd6a9d5ccbffcd3f18ac0e28d91276e2bafddd4dad597cb5b2ef61a3a01ce`。

## 账号占用与离线恢复

前次官方 miniprofile 查询发现其他机器正在运行《钢铁雄心 IV》，因此保持离线等待，没有初始化发布 SDK。后台每分钟只读监测，2026-10-30 19:14:28 UTC 首次观察到游戏结束。该历史结果没有直接用于次日发布。

本次切在线前（2026-10-31 02:04:56 UTC），重新取得完整公开 profile 的新鲜空闲证据；初始化 SDK 前（02:05:12 UTC）再次检查空闲，并核对当前账号与预期作者一致，之后才创建条目。条目 ID 收到后立即持久化，全部操作只更新这一个条目。

上传及客户端下载验证结束后立即请求 Steam 主动离线。首次即时读回处于转换过程，返回 unavailable，没有计作成功；重新请求并在 02:06:09 UTC 取得真实离线回执。随后正常关闭临时 CEF 调试实例，以普通 `-silent` 启动；02:07:40 UTC，PID `13664` 的回执为 `status=offline`、`offline_mode=true`，临时端口 8080 不再监听。没有强制结束 Steam、编辑登录文件、断网或接管其他机器。

## 发布验证

| 检查 | 结果 |
| --- | --- |
| 上传 API 实际完成 | PASS |
| 匿名官方元数据 | PASS：App、作者、标题、完整说明、公开可见性和 `mod/campaign` 标签一致 |
| 匿名条目页面 | PASS：标题、说明和必需物品 `3811098873` 正确 |
| 更新说明 | PASS：首个版本说明可匿名读取 |
| 预览图 | PASS：公开 CDN 下载与 `build/preview.png` 字节完全一致 |
| Steam 实际下载 | PASS：02:05:38 UTC 下载完成，安装标记 4，无待更新/下载标记 |
| 下载包哈希 | PASS：42,899 字节，SHA-256 与离线实机冻结包完全一致 |
| 发布后 Steam 模式 | PASS：主动离线，普通启动，临时控制通道已关闭 |

常规 `sharedfiles` 页面路由一度返回 HTTP 429；通过 Steam 官方同一条目的 `workshop/filedetails` 路由完成匿名 HTML 回读，没有将限流错误计作页面通过。公开元数据通过官方 `ISteamRemoteStorage/GetPublishedFileDetails` 接口回读。

原始证据位于仓库外 `D:/workspace/.codex-wh3-runtime/research/publication-7007c0d2be35453a8e28ee943c72496f/`，包括上传回执、匿名元数据及页面、下载哈希、预览图与离线回执。精确文件哈希保存在 [验收结果](acceptance-results.json)，公开条目状态保存在 [publication-state.json](../workshop/publication-state.json)。

本版本实测范围为 Windows x64、WH3 9.0.4、单人超凡帝国，完整人物流程为基斯里夫波耶老爷和牧首。其他种族完整战役、组合 Mod、联机和特殊招募不据此宣称兼容，详见 [验收报告](acceptance-report.md)。
