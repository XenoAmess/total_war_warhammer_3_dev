# 战锤 3 使用独立显卡的排查记录

2026-10-31，执行机器 `pc-20260924rtuf-f11af23c08`，Windows 10 Pro 19045。用户已调整优先级：两个模组先发布；显卡排查和实机截图后续继续，不作为本次上传的前置条件。

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

## 后续处理与成功标准

1. 先复查当前 PCI 设备和对应父设备链，核对设备是否换过端口、是否出现新实例。仅以当前连接的实例为准，不把历史记录当作当前显卡。硬件重扫后仍须再次枚举确认。[微软 PnPUtil 文档](https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/pnputil-command-syntax)
2. 设备重新出现后，检查其问题码和驱动绑定；再用 `nvidia-smi`、DXGI 枚举核实 NVIDIA 已可用。需要重启或检查实体连接时，另行安排，避免中断当前机器上的其他工作。[NVIDIA 查询工具说明](https://docs.nvidia.com/deploy/nvidia-smi/)
3. NVIDIA 正常枚举后，再核对 Windows 图形首选项和 WH3 的适配器选择。在 Steam 主动离线状态取得新鲜回执后启动游戏，以新生成的 `gfx.log.txt` 中实际选中的 NVIDIA 适配器及正常主菜单、战役画面作为成功证据，随后分别补做两个 Mod 的功能截图。

保留当前远程连接使用的 ToDesk / Virtual Display 设备。当前没有移除或禁用显示设备、卸载驱动、修改 BIOS、重启机器，也没有将软件渲染器标为独显修复。微软新版 WARP 1.0.22 已下载并通过 Microsoft 签名检查，但未安装；先前 DXVK / Lavapipe 测试文件和临时注册项已恢复。BasicRender/WARP 仍属于 CPU 软件渲染。[微软 BasicDisplay / BasicRender 说明](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/microsoft-basic-display-driver)
