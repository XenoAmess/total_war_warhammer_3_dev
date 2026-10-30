# 征募与迁都 / Recruitment and Capitals

《全面战争：战锤 3》战役 Mod 的开发仓库：普通领主/事务官招募刷新，以及玩家迁移派系首都。

当前为 `0.1.0` 开发版本，**完整流程仍在验收，尚未发布到 Steam 创意工坊**。领主和事务官已完成真实按钮刷新、正常招募及各 10 次连续按钮操作；受伤、不朽、已招募和未知履历人物保护通过。类型由引擎的普通自动生成标记与实际候选职业共同识别，冰雪宫廷等特殊训练不启用。本机完整玩家流程实测为基斯里夫波耶老爷和牧首，另有帝国两类法师共用原生池的隔离实验；不据此宣称全种族兼容。见 [同类 Mod 调查与新实验](docs/similar-mods-research.md) 与 [验收报告](docs/acceptance-report.md)。

刷新功能需要启用 [memreader Plus](https://steamcommunity.com/sharedfiles/filedetails/?id=3811098873)。本项目通过它调用游戏自己的候选淘汰与列表清理函数，不直接改写人物或容器内存。当前验证基线为 Windows x64、WH3 `9.0.4.0`、单人超凡帝国；缺少依赖或函数签名/结构校验失败时，按钮与后台均停止刷新。迁都使用游戏脚本接口。

## 开发

构建只需要 Python 标准库：

```powershell
python tools/build.py
python tools/build.py --language en --output build/en
```

产物为 `build/xatw3_campaign_utilities.pack` 和含 SHA-256 的 `manifest.json`。构建不会改动游戏安装；英文构建为替代语言版本，不与中文包同时启用。

离线检查使用 Python 3.13 与 Lupa 提供的 Lua 5.1：

```powershell
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe tools/test.py
```

`tools/live_probe.py` 构建单独的引擎测试夹具；只在专用测试环境显式安装，正式包不会包含该夹具。它允许从指定本机目录执行可信测试命令，不能与正式包一起上传。

## 文档

- [预研报告](docs/feasibility-study.md)
- [设计文档](docs/mod-design.md)
- [测试验收与发布方案](docs/test-acceptance-plan.md)

发布工具 `tools/workshop.py` 只允许上传与验收清单哈希一致、且 L0–L3 全部 PASS 的包。工具在创建条目后立即记录 ID，重试更新同一个条目。上传回执与公开页面验证分别记录。
