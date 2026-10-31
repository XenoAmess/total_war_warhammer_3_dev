# Total War: WARHAMMER III Mod 项目集

《全面战争：战锤 3》多 Mod 开发仓库。根目录管理共用工具、共性文档和开发约定；每个 Mod 的源码、资源、测试、设计、验收与工坊资料均放在 `mods/<mod_id>/`。

| Mod | 状态 | 入口 |
| --- | --- | --- |
| 招募候选刷新 | `0.2.0 Alpha` 拆分验收中，保留原工坊条目 | [项目说明](mods/recruitment_refresh/README.md) · [Steam 创意工坊](https://steamcommunity.com/sharedfiles/filedetails/?id=3830548217) |
| 迁移首都 | `0.1.0 Alpha` 独立验收中，无辅助 Mod 依赖 | [项目说明](mods/move_capital/README.md) |
| 顾问换声 | 原版资源预研完成，尚无实现或可发布包 | [预研入口](mods/advisor_voice/README.md) |

目录约定与新增 Mod 步骤见 [项目结构](docs/project-structure.md)，Steam 离线及账号占用规则见 [Steam 操作约定](docs/steam-operation.md)。

## 开发

在仓库根目录执行，所有涉及 Mod 的入口必须显式传入 `--mod`：

```powershell
python tools/build.py --mod recruitment_refresh
```

构建只需 Python 标准库，产物写入 `mods/recruitment_refresh/build/`。各 Mod 的构建目录独立，构建不修改游戏安装。

运行共用工具测试和所选 Mod 的离线测试，需要 Python 3.13、Lua 5.1 的 Lupa，以及预览图工具使用的 Pillow：

```powershell
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe tools/test.py --mod recruitment_refresh
```

共用工具分别负责 PFH5 打包、本地化编译、离线测试调度、实机测试夹具和 Steam 工坊上传。Mod 专属测试及预览图绘制逻辑由各自目录提供。详见 [工具用法与目录约定](docs/project-structure.md)。

## 文档

- [共性文档索引](docs/README.md)
- [招募候选刷新文档](mods/recruitment_refresh/docs/README.md)
- [迁移首都设计与验收](mods/move_capital/docs/design-and-acceptance.md)
- [顾问换声预研](mods/advisor_voice/docs/advisor-voice-research.md)

发布工具根据各 Mod 的 `mod.json` 和专属验收、工坊状态选择目标，拒绝混用其他 Mod 的记录。Steam 平时保持主动离线，必要发布前须检查其他机器账号占用，完成后立即恢复离线。完整约定见 [AGENTS.md](AGENTS.md)。
