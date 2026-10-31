# 战锤 3 使用独立显卡的排查记录

2026-10-31，执行机器 `pc-20260924rtuf-f11af23c08`，Windows 10 Pro 19045。此前两个模组的发布未以显卡恢复或实机截图为前置；本轮用户已明确要求继续诊断并尝试修复 RTX 3060 无法识别的问题。

## 当前查到的事实

| 检查 | 实际结果 |
| --- | --- |
| 显卡设备记录 | 存在 NVIDIA GeForce RTX 3060，设备 ID `PCI\VEN_10DE&DEV_2520&SUBSYS_000010DE&REV_A1\4&2A43D483&0&0010` |
| Windows 当前设备状态 | `Present=False`、`CM_PROB_PHANTOM`；仅枚举当前设备时找不到任何 NVIDIA PCI 设备 |
| 该记录的上游 PCIe 端口 | Intel PCI Express Root Port 2，`VEN_8086&DEV_2F04`，同样 `Present=False`；不能据此认定主板物理槽位编号 |
| 当前显示设备 | 四个 ToDesk / Virtual Display 适配器 |
| 已安装驱动 | 历史绑定版本 `32.0.15.9174`，驱动文件存在；重启前后 `nvlddmkm` 内核驱动均未运行 |
| NVIDIA 查询 | 已安装的 `nvidia-smi` 返回无法与 NVIDIA 驱动通信 |
| 硬件重扫 | `pnputil /scan-devices` 成功执行，随后当前设备列表仍没有 NVIDIA |
| 游戏实际适配器 | 重启前的 WH3 `gfx.log.txt` 仅列出 Microsoft Basic Render Driver；战役画面不完整，未取得可接受的功能截图；重启后未启动游戏 |

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

## 获准重启后的复查

用户批准重启后，后台记录确认 Windows 已完成新一次启动，启动时间为 **2026-10-31 17:02:31（北京时间，09:02:31 UTC）**，取代此前 10 月 22 日的启动现场。一次性启动任务在 17:03:22–17:04:17 进行了 6 次检查：

- 每次当前 NVIDIA PCI 设备数均为 0；RTX 3060 和历史父端口 `2F04` 均仍为 `Present=False`、Code 45。
- 6 次 `nvidia-smi` 均退出 9，报告无法与驱动通信；`nvlddmkm` 始终停止。`repair_confirmed=false`，任务保存回执后已自行移除。
- 19:21–19:22 的实时复查与开机检查一致。再次执行硬件重扫返回 0，之后仍没有 NVIDIA PCI 设备或该父端口。

本轮额外核对了软件配置和本次启动日志：

- `pci.sys` 为 Boot 启动且正在运行；PCI Express 根复合体正常；CPU 侧其他 `2F02`、`2F03`、`2F08` 端口在场且无问题码。没有当前处于错误状态的 PCI 设备或 NVIDIA 新实例。
- 显卡及历史父端口仍 `ConfigFlags=0`，没有设备级 Upper/LowerFilters；System 和 Display 类也没有 Upper/LowerFilters。当前及已读取的继承引导设置未见 PCIe 禁用项；`HypervisorPresent=false`，未发现 Hyper-V 的 `vmms`、`vmcompute` 服务。
- 本次启动以来查询到的相关 System 日志为 4 条 Kernel-PnP 219，均指向 `ROOT\DISPLAY\0000` 至 `0003` 虚拟显示设备；这些设备当前状态正常。未发现本次启动中的 NVIDIA / `2F04` PnP 配置事件、NVIDIA 驱动错误或 WHEA 事件。日志缺席不能单独证明具体根因，也不能将虚拟显示器的启动日志当作 RTX 3060 加载失败。

**当前判断：重启未恢复，仍需优先验证供电、PCIe 链路和固件初始化；尚不能确定是哪一个部件或设置导致。** 显示优先级或 ToDesk 的虚拟屏幕不能代替解释“当前 PCI 设备树中没有显卡及其历史父端口”。Windows 的 PCI 总线驱动负责设备枚举；当前没有支持通过改游戏显卡选项或重装 NVIDIA 驱动修复上游端口缺席的证据。[微软 PCI 驱动职责说明](https://learn.microsoft.com/en-us/windows-hardware/drivers/pci/pci-power-management-and-device-drivers)

开机原始回执在 `D:/workspace/.codex-wh3-runtime/gpu-diagnosis-20261031/restart-20261031/post-restart.json`，本轮实时设备、配置、日志、重扫和模型审阅材料在同级 `post-restart-followup-20261031/`。本轮对新证据调用本地模型两次：第一次 `finish_reason=length` 的候选完整丢弃；缩小输出范围后第二次为 HTTP 200、完整 SSE、`finish_reason=stop`，仅采纳复核后的分析方向，未执行候选命令。后台 Steam 查询返回 `steam_not_found`；客户端没有运行，未声称其处于主动离线，也没有启动 Steam 或游戏。

用户随后确认**暂时无人现场，只能远程操作**。本机当前设备、服务和常见厂商 WMI 类中未发现可用的 IPMI/BMC、Intel AMT 或厂商固件管理入口；这不证明不存在另行配置的外部远程电源设备。本轮保持正常开机与 ToDesk 连接，未继续关机、切换 BIOS 启动或修改固件。当前可用入口不足以完成实体供电、插槽或 BIOS 检测的交叉验证，后续现场步骤仍待安排，显卡仍未修复。

## 后续处理与成功标准

1. Windows 重启及重启后的设备核对已完成，均未恢复。下一项有区分价值的操作是**有现场人员配合的完全断电冷启动**：正常关机，切断机箱电源，再接电开机；现场须能重新开机，不能在无人现场时远程关机后期待自动恢复。若恢复，只说明与电源/固件/链路状态有关的可能性增加，不能单独确定根因。恢复连接后重新查询当前 PCI 设备、问题码和 `nvidia-smi`，不把扫描命令成功当作修复成功。[微软 PnPUtil 文档](https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/pnputil-command-syntax)
2. 冷启动仍无设备时，在关机并断开电源后检查显卡是否插紧、独立供电和转接/延长线（如有）。若 BIOS 提供 PCIe 设备或链路状态页，读取其实际检测结果；没有该页面就记为未知。BIOS 能看到设备而 Windows 看不到时，再集中检查 Windows；两边均检测不到时，优先现场换槽或换卡交叉验证。不根据历史端口名称推断物理槽位，不盲目恢复 BIOS 默认值或刷固件。
3. 设备重新出现后，检查其问题码和驱动绑定；再用 `nvidia-smi`、DXGI 枚举核实 NVIDIA 已可用。只有存在实际驱动绑定或加载错误时，才针对错误处理驱动。[NVIDIA 查询工具说明](https://docs.nvidia.com/deploy/nvidia-smi/)
4. NVIDIA 正常枚举后，再核对 Windows 图形首选项和 WH3 的适配器选择。在 Steam 主动离线状态取得新鲜回执后启动游戏，以新生成的 `gfx.log.txt` 中实际选中的 NVIDIA 适配器及正常主菜单、战役画面作为成功证据，随后分别补做两个 Mod 的功能截图。

保留当前远程连接使用的 ToDesk / Virtual Display 设备。除已获准并完成的重启外，没有移除或禁用显示设备、卸载驱动、修改 BIOS，也没有将软件渲染器标为独显修复。微软新版 WARP 1.0.22 在此前已下载并通过 Microsoft 签名检查，但未安装；先前 DXVK / Lavapipe 测试文件和临时注册项已恢复。BasicRender/WARP 仍属于 CPU 软件渲染。[微软 BasicDisplay / BasicRender 说明](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/microsoft-basic-display-driver)
