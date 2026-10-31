# 战锤 3 使用独立显卡的排查记录

2026-10-31，执行机器 `pc-20260924rtuf-f11af23c08`，Windows 10 Pro 19045。此前两个模组的发布未以显卡恢复或实机截图为前置；本轮用户已明确要求继续诊断并尝试修复 RTX 3060 无法识别的问题。

## 当前查到的事实

| 检查 | 实际结果 |
| --- | --- |
| 显卡设备记录 | 存在 NVIDIA GeForce RTX 3060，设备 ID `PCI\VEN_10DE&DEV_2520&SUBSYS_000010DE&REV_A1\4&2A43D483&0&0010` |
| Windows 当前设备状态 | `Present=False`、`CM_PROB_PHANTOM`；仅枚举当前设备时找不到任何 NVIDIA PCI 设备 |
| 该记录的上游 PCIe 端口 | Intel PCI Express Root Port 2，`VEN_8086&DEV_2F04`，同样 `Present=False`；不能据此认定主板物理槽位编号 |
| 当前显示设备 | 四个 ToDesk / Virtual Display 适配器 |
| 已安装驱动 | 历史绑定版本 `32.0.15.9174`，驱动文件存在；`nvlddmkm` 内核驱动未运行，NVIDIA Display Container 服务运行中 |
| NVIDIA 查询 | 已安装的 `nvidia-smi` 返回无法与 NVIDIA 驱动通信 |
| 硬件重扫 | `pnputil /scan-devices` 成功执行，随后当前设备列表仍没有 NVIDIA |
| 游戏实际适配器 | 本次 WH3 `gfx.log.txt` 仅列出 Microsoft Basic Render Driver；战役画面不完整，未取得可接受的功能截图 |

这些结果说明“Windows 当前没有把这块 NVIDIA 卡枚举为可用设备”，不等于机器没有装显卡，也不能直接判定显卡损坏。微软将 `CM_PROB_PHANTOM` 定义为设备当前不在场的 Code 45；它与普通的设备禁用、缺少驱动不是同一种状态。[微软 Code 45 文档](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/cm-prob-phantom)

仅指定游戏使用“高性能 GPU”、修改游戏显卡序号或重装游戏，无法代替恢复设备枚举。上游端口也未出现，使 PCIe 连接、供电、固件设置、设备迁移或系统枚举状态成为需要进一步区分的方向；目前没有证据确认其中任意一项。驱动未运行也可能是设备未枚举的结果，不能据此断定驱动损坏。

## 2026-10-31 后台复查与修复尝试

本轮在 08:46–08:48 UTC（北京时间 16:46–16:48）取得新鲜读回，结果仍为未恢复：

- 当前连接设备中没有任何 `VEN_10DE` PCI 设备，也没有以未知设备出现的 NVIDIA 新实例。显卡、其 HDMI 音频控制器和历史父端口 `VEN_8086&DEV_2F04` 均为 Code 45；PCI Express 根复合体 `ACPI\PNP0A08\0` 正常在场。
- 显卡和父端口的 `ConfigFlags=0`，没有发现设备管理器禁用标志。`pnputil /scan-devices` 返回 0、完成扫描，随后父端口仍 `Present=False`，当前 NVIDIA PCI 设备数仍为 0。这只证明重扫执行成功，不是修复成功。
- `nvlddmkm.sys` 版本 `32.0.15.9174`，文件存在且 NVIDIA Corporation 签名通过验证；内核驱动为按需启动、当前停止。此时没有足够证据把问题归为驱动文件缺失或损坏，也没有卸载或重装驱动。
- 本轮采集的系统日志中，2026-09-27 00:39:51–02:12:46（北京时间）有 1,742 条 WHEA-Logger 17 事件指向同一个 `VEN_8086&DEV_2F04` 端口。事件明确报告已更正的 PCI Express 硬件错误。这是链路曾经报错的历史证据，不能当成本轮持续报错、准确失效时间或显卡已损坏的证明。[微软 WHEA 硬件错误事件说明](https://learn.microsoft.com/en-us/windows-hardware/drivers/whea/whea-hardware-error-events)
- 显卡和父端口记录的最后到达时间均为 2026-10-21 21:19:19（北京时间），本次 Windows 启动时间为 2026-10-22 10:33:52。到达时间不是最后正常工作时间；现有记录不足以确认具体在哪次启动中消失。

据此，下一步应检查 PCIe 枚举、链路、供电和 BIOS 初始化。当前无法远程区分具体原因，也不能保证一次重启即可恢复。重装 NVIDIA 驱动不是目前优先动作，因为其上游端口尚未在场。

本轮已保留原始设备快照、扫描回执、PnP/启动历史、WHEA 事件和签名检查结果，目录为 `D:/workspace/.codex-wh3-runtime/gpu-diagnosis-20261031/`，仅代表本机。使用配置中的本地模型做了一次独立诊断分析：HTTP 200、完整 SSE、`finish_reason=stop`、JSON 可解析；主执行者仅采纳经本机证据复核的方向，拒绝其不存在的 `pnputil /reinstall` 命令和“重启即可确定物理故障”等过度结论。原始请求、响应和用量保存在该目录的 `model-analysis/`，审阅记录见 `review.json`。本轮后台 Steam 回执为主动离线，没有启动游戏。

## 后续处理与成功标准

1. 本轮已完成父设备链、新实例和重扫后的当前设备核对。后续优先协调一次普通重启，重新执行 `Get-PnpDevice -PresentOnly -Class Display`、父设备查询及 `nvidia-smi`。重启会中断当前远程会话，须先协调时间、保存工作并确认可重新连接；本轮未执行重启。[微软 PnPUtil 文档](https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/pnputil-command-syntax)
2. 若重启仍无设备，安排现场冷启动并检查显卡是否插紧、独立供电连接，以及 BIOS 的 PCIe 检测与相关设置；不根据历史端口名称推断物理槽位，不盲目恢复 BIOS 默认值或刷固件。必要时由现场人员在断电条件下换槽、换卡交叉验证。重启或冷启动恢复也不能单独证明具体根因。
3. 设备重新出现后，检查其问题码和驱动绑定；再用 `nvidia-smi`、DXGI 枚举核实 NVIDIA 已可用。只有存在实际驱动绑定或加载错误时，才针对错误处理驱动。[NVIDIA 查询工具说明](https://docs.nvidia.com/deploy/nvidia-smi/)
4. NVIDIA 正常枚举后，再核对 Windows 图形首选项和 WH3 的适配器选择。在 Steam 主动离线状态取得新鲜回执后启动游戏，以新生成的 `gfx.log.txt` 中实际选中的 NVIDIA 适配器及正常主菜单、战役画面作为成功证据，随后分别补做两个 Mod 的功能截图。

保留当前远程连接使用的 ToDesk / Virtual Display 设备。当前没有移除或禁用显示设备、卸载驱动、修改 BIOS、重启机器，也没有将软件渲染器标为独显修复。微软新版 WARP 1.0.22 已下载并通过 Microsoft 签名检查，但未安装；先前 DXVK / Lavapipe 测试文件和临时注册项已恢复。BasicRender/WARP 仍属于 CPU 软件渲染。[微软 BasicDisplay / BasicRender 说明](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/microsoft-basic-display-driver)
