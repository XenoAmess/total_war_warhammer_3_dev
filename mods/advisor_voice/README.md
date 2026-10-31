# 顾问换声预研

已完成顾问资源解析、音频实际提取、中文文案关联及单文件替换包的静态验证。已定位的 2,717 个顾问 DB 关联媒体 ID 均有中文文案候选；尚未完成自定义配音编码与游戏内换声验收，没有可发布 Mod 或工坊条目。

- [音频提取、中文文案与替换机制报告](docs/advisor-audio-extraction-and-replacement.md)
- [本次提取与文本证据](docs/advisor-audio-extraction-evidence-2026-10-31.json)
- [本地模型实际贡献及失败记录](docs/local-model-contributions-2026-10-31.json)
- [预研报告](docs/advisor-voice-research.md)
- [机器可读研究证据](docs/advisor-voice-research-evidence-2026-10-31.json)

本机中文清单位于 `build/research-2026-10-31/texts/media-chinese-text.tsv`，原始游戏文案与音频不随 Git 上传。复现命令及本机资源路径见机制报告。

测试：`python mods/advisor_voice/tests/run.py --mod advisor_voice`（仓库根目录执行）。专属工具位于 `tools/`，所有命令均要求 `--mod advisor_voice`。

共用工具及开发规则见 [仓库入口](../../README.md)。本目录仍按研究项目管理；正式 Mod 实现时按 [目录约定](../../docs/project-structure.md) 添加 `mod.json` 与源码。
