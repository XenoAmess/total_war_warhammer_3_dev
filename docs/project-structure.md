# 多 Mod 项目结构

## 目录边界

```text
AGENTS.md                     仓库级工作约定
README.md                     Mod 目录与开发入口
requirements-dev.txt          共用开发依赖
docs/                         共性文档
tools/                        共用打包、测试、发布工具
tests/                        共用工具的 Python 测试
mods/
  recruitment_refresh/
    mod.json                  当前 Mod 的名称、包名、语言及工坊依赖
    README.md                 功能、安装与本 Mod 的开发入口
    src/                      原样进入 pack 的文件树
    localisation/             本 Mod 的语言源文件
    tests/                    本 Mod 的测试；run.py 为离线测试入口
    tools/                    本 Mod 独有的工具，例如封面绘制脚本
    docs/                     预研、设计、验收、历史报告与发布记录
    workshop/                 描述、更新说明、封面源文件与条目状态
    build/                    本 Mod 的构建产物，Git 忽略
  advisor_voice/
    README.md                 预研阶段说明
    docs/                     顾问换声预研与证据
```

根目录不存放某个 Mod 的游戏脚本、语言资源、封面绘制逻辑或工坊条目状态。暂时仅有预研的目录不放 `mod.json`，构建工具会明确拒绝，不生成空包。

`src/` 内采用游戏包中的相对路径，例如 `src/script/campaign/mod/example.lua` 会成为包内 `script/campaign/mod/example.lua`。仓库目录名称不会进入包内，因此移动仓库结构可以保持既有包字节不变。

## Mod 配置

每个可构建 Mod 的 `mod.json` 至少包含：

```json
{
  "schema_version": 1,
  "id": "example_mod",
  "title": "Example Mod",
  "version": "0.1.0",
  "pack_name": "example_mod.pack"
}
```

`id` 必须与目录名一致，使用小写字母、数字和下划线，以字母开头。`pack_name` 为独立的小写 `.pack` 文件名；已有发布的包名与工坊 ID 保持稳定。

有本地化时增加 `languages`、`default_language`、`localisation_pack_path`，并提供各语言 TSV，所有语言的 key 必须一致。工坊依赖及标签分别放入 `workshop.required_items`、`workshop.tags`。完整例子见 [征募与迁都配置](../mods/recruitment_refresh/mod.json)。

## 共用工具

以下命令在仓库根目录运行；`--mod` 必填，没有默认 Mod。

```powershell
python tools/build.py --mod recruitment_refresh
python tools/build.py --mod recruitment_refresh --language en --output mods/recruitment_refresh/build/en
python tools/test.py --mod recruitment_refresh
python tools/preview.py --mod recruitment_refresh
python tools/live_probe.py --mod recruitment_refresh --runtime D:/workspace/.codex-wh3-runtime/acceptance --dispatcher-only
```

默认产物、预览图和测试摘要均位于所选 Mod 的 `build/`。测试入口先运行根目录共用 Python 测试，再运行该 Mod 的 `tests/run.py`。只运行共用测试时使用 `python -m unittest discover -s tests -p 'test_*.py'`。

`live_probe.py` 仅构建测试夹具，不安装或启动游戏。夹具允许执行本机可信命令，只能用于独立测试环境，不能上传到工坊。

发布命令形式如下，仅在完成账号空闲检查、必要在线切换和精确包验收后执行：

```powershell
python tools/workshop.py --mod recruitment_refresh --dll "C:/SteamLibrary/steamapps/common/Total War WARHAMMER III/steam_api64.dll" --owner 76561198273714027
```

发布工具按该 Mod 读取 `docs/acceptance-results.json`、`workshop/publication-state.json`、描述、更新说明及预览图；上传暂存目录也在该 Mod 的 `build/`。验收和工坊状态必须包含相同 `mod_id`，包名及 SHA-256 也须匹配；不满足时在连接 Steam 前拒绝。创建条目后立即记录 ID，后续重试更新同一个条目。工具不负责切换客户端模式，操作者须遵守 [Steam 操作约定](steam-operation.md)。

## 新增 Mod

1. 建立 `mods/<mod_id>/`，先写本 Mod 的 README 和专属预研。
2. 开始实现时添加 `mod.json` 和 `src/`；有本地化时提供语言配置及 TSV。
3. 将专属测试放入 `tests/`，提供 `tests/run.py`；可复用的引擎无关工具才提到根目录。
4. 工坊资料和条目状态放入本 Mod 的 `workshop/`，验收记录放入本 Mod 的 `docs/`。
5. 使用显式 `--mod` 构建和验收，再将入口加入根目录 Mod 目录表。

结构迁移时核对各 Mod 的源码、资源和构建包，保留已有包名、工坊 ID 与历史证据。具体迁移复验结果放入对应 Mod 的验收报告。
