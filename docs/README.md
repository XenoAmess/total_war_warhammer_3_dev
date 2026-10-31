# 共性文档

根目录文档只记录整个仓库通用的流程和约定，具体 Mod 的预研、设计、验收及发布记录保存在各自目录。

| 文档 | 内容 |
| --- | --- |
| [项目结构](project-structure.md) | 目录边界、Mod 配置、共用工具用法和新增 Mod 步骤 |
| [本地模型接入](local-model-usage.md) | 本项目积极使用本地模型的流程、请求构造、并行与实际接入结果 |
| [本地模型 worker 指南](local-model-worker-guide.md) | 从 CK3 项目原文抄录的跨机器调用指南 |
| [本地模型统一配置](local-model-executor-config.json) | 服务地址、模型、固定系统模板、请求默认值及重试策略 |
| [本地模型可行性经验](local-model-executor-feasibility-2026-10-28.md) | 指定上游提交中的实现、反馈与采用经验全文 |
| [本地模型能力边界](local-model-capability-boundary-2026-10-28.md) | 指定上游提交中的验证范围与失败经验全文 |
| [本地模型运营历史](autonomous-agent-progress/2026-10-31-resume91-models.md) | 指定上游提交中的请求、真实并发与审阅历史全文 |
| [抄录来源清单](local-model-import.json) | 固定上游版本、原文校验值和历史附件边界 |
| [本机调用与采用记录](local-model-onboarding-2026-10-31.json) | 本机实际请求、编码故障、修复后返回及文档采用范围 |
| [Steam 操作约定](steam-operation.md) | 主动离线、账号占用检查、必要在线阶段和状态读回 |
| [工坊图文与实机截图](workshop-media.md) | 各 Mod 的 BBCode、截图清单、图库上传和发布验证 |
| [显卡渲染排查](gpu-rendering-investigation-20261031.md) | RTX 3060 当前枚举状态、已完成检查与后续恢复判据 |
| [仓库工作约定](../AGENTS.md) | Steam 与 Git 提交推送规则 |

各 Mod 的资料入口：

- [招募候选刷新](../mods/recruitment_refresh/docs/README.md)：刷新实现、原生研究、拆分验收及原合并版本的历史证据。
- [迁移首都](../mods/move_capital/docs/design-and-acceptance.md)：独立迁都设计与最简验收。
- [顾问换声](../mods/advisor_voice/README.md)：资源可行性预研及机器可读证据，尚无可构建 Mod。
