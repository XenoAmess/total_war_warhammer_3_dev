# 招募候选刷新 / Recruitment Refresh

当前工坊版本 **0.2.4 已发布**：点击刷新时，选中的非空普通招募子类型不足 **3 名**就补足到 3 名，已有更多候选时不缩减。受保护候选保留，新增人物只沿用同类人物的性别，不复制其特性。原版招募费用、容量及解锁条件保持；空池与特殊招募不扩充。已通过 76 项共用、67 项专属测试及 9.0.5 离线实机的 1→3、2→3、5→5 和新增候选正常招募。工坊更新说明已公开，订阅下载包哈希一致，Steam 已恢复主动离线。见[更新日志](CHANGELOG.md)、[人数验收](docs/candidate-count-0.2.4.json)和[发布回执](docs/workshop-publication-0.2.4.json)。

此前候选 `0.2.3` 的修复已包含在 0.2.4，未单独发布：在 Windows x64、游戏 `9.0.5.0` / Steam build `26403568` 离线实机通过波耶与牧首刷新、受保护候选保留、刷新后的正常招募及图标避让。新增精确引擎构建校验，禁止商队/车队特殊类型进入普通刷新。原始反馈场景未完整复现，不宣称全种族兼容。见[9.0.5 验收](docs/compatibility-9.0.5.json)与[调查记录](docs/update-9.0.5-investigation.md)。

《全面战争：战锤 3》“招募候选刷新”Mod：普通领主/事务官招募刷新。本目录是[多 Mod 仓库](../../README.md)中的独立项目。

`0.2.2` 已发布至[原工坊条目](https://steamcommunity.com/sharedfiles/filedetails/?id=3830548217)：原生刷新图标、可见分类页识别修复及 3 张实机图片，图库和正文均已更新。73 项共用测试、55 项 Mod 测试及基斯里夫领主/牧首实机回归通过，订阅下载包哈希一致。实机范围为 100% UI 缩放、原生控件避让；不宣称其他 Mod 兼容。见[验收状态](docs/acceptance-results-0.2.2.json)和[发布回执](docs/workshop-publication-0.2.2.json)。以下为旧版本历史。

`0.2.1 Alpha` 已更新[原工坊条目](https://steamcommunity.com/sharedfiles/filedetails/?id=3830548217)，正文、发布包、远端启动器元数据和真实订阅下载均已核对。旧启动器自身的原生读取接口已返回本 Mod；完整游戏内回归和截图按用户授权后补。见[发布记录](docs/workshop-publication.md)。

`0.2.1` 将按钮移到“招募”右侧，单击直接刷新，成功后返回招募页；保留错误提示、执行中防重和关闭面板保护。两个 Mod 的老启动器元数据均已补齐，订阅包哈希和旧启动器接口读取已验证；实际字体渲染与游戏行为仍待验，见[修复验收](docs/ui-launcher-fix-0.2.1.md)。

此版本不再包含迁都功能；迁都已拆为[独立 Mod](../move_capital/README.md)，已发布于[独立工坊条目](https://steamcommunity.com/sharedfiles/filedetails/?id=3830651933)。旧存档中已经迁移的首都保持现状，不会回滚。

原 0.1.0 合并版已完成离线真实按钮刷新、正常招募及各 10 次连续按钮操作通过；受伤、不朽、已招募和未知履历人物保护通过。类型由引擎的普通自动生成标记与实际候选职业共同识别，冰雪宫廷等特殊训练不启用。本机完整玩家流程实测为基斯里夫波耶老爷和牧首，另有帝国两类法师共用原生池的隔离实验；不据此宣称全种族兼容。见 [同类 Mod 调查与新实验](docs/similar-mods-research.md) 与 [验收报告](docs/acceptance-report.md)。

刷新功能需要启用 [memreader Plus](https://steamcommunity.com/sharedfiles/filedetails/?id=3811098873)。本项目通过它调用游戏自己的候选淘汰与列表清理函数，不直接改写人物或容器内存。当前验证基线为 Windows x64、WH3 `9.0.4.0`、单人超凡帝国；缺少依赖或函数签名/结构校验失败时，按钮与后台均停止刷新。

在工坊订阅本 Mod 和 memreader Plus，并在启动器中同时启用。进入单人超凡帝国后，在普通人物招募页选择候选类别并点击“刷新候选”。旧存档中履历不明的候选受到保护，后续自然生成的普通候选才会获得可刷新履历。

## 开发

以下命令从仓库根目录执行。构建只需要 Python 标准库：

```powershell
python tools/build.py --mod recruitment_refresh
python tools/build.py --mod recruitment_refresh --language en --output mods/recruitment_refresh/build/en
```

产物为本目录的 `build/xatw3_campaign_utilities.pack` 和含 SHA-256 的 `manifest.json`。包内文件来自 `src/`，本地化来自 `localisation/`，包名等配置见 [mod.json](mod.json)。构建不会改动游戏安装；英文构建为替代语言版本，不与中文包同时启用。

离线检查使用 Python 3.13 与 Lupa 提供的 Lua 5.1：

```powershell
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe tools/test.py --mod recruitment_refresh
```

根目录 `tools/live_probe.py --mod recruitment_refresh` 构建单独的引擎测试夹具；只在专用测试环境显式安装，正式包不会包含该夹具。它允许从指定本机目录执行可信测试命令，不能与正式包一起上传。专属离线用例在 `tests/`，封面绘制脚本在 `tools/preview.py`；共用入口见 [项目结构](../../docs/project-structure.md)。

## 文档

- [预研报告](docs/feasibility-study.md)
- [设计文档](docs/mod-design.md)
- [测试验收与发布方案](docs/test-acceptance-plan.md)

根目录发布工具 `tools/workshop.py --mod recruitment_refresh` 默认要求本目录验收清单的 `mod_id`、包名、哈希一致且 L0–L3 全部 PASS。本次用户明确要求 0.2.1 先发布，显式使用[新包专用延期记录](docs/publication-waiver-0.2.1-20261031.json)仅延期该包的 L2/L3，原始待验状态保留。工坊资料和既有条目状态在 `workshop/`；工具更新同一个条目，上传回执与公开查询验证分别记录。
