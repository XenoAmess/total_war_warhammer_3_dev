# 工坊图文与实机截图

2026-10-31 用户调整优先级：先发布两个拆分模组的内容、标题、封面和各自 BBCode；显卡修复、实机截图、图库和正文内嵌图片作为发布后的独立工作继续。当前不上传无法展示功能的异常画面。

默认发布仍要求精确包哈希与 L0–L3 通过。用户明确要求先发布时，可显式传入 `--native-waiver mods/<mod_id>/docs/publication-waiver-20261031.json`，仅延期该 Mod、该包的 L2/L3；L0/L1 和包身份检查始终强制。发布状态保存原始验收结果与延期记录哈希，不把未完成检查标记为通过。

每个 Mod 独立维护 `mods/<mod_id>/workshop/description.bbcode`、更新说明、封面及 `screenshots/`。正文 BBCode 和展示用截图都提交到 Git；封面不代替实机截图。截图须展示该 Mod 单独启用时的按钮或效果，记录实际游戏版本、包哈希和采集时间；黑图、空白图、示意图不能冒充实机画面。

`workshop/screenshots.json` 使用以下结构，`file` 相对于同级 `screenshots/`：

```json
{
  "screenshots": [
    {
      "file": "recruitment-button.png",
      "sha256": "实际文件的 SHA-256",
      "caption": "招募页面的刷新候选按钮",
      "url": "https://公开可访问的图片地址"
    }
  ]
}
```

正文将每张图片按对应功能放在说明文字附近，使用 `[img]图片完整地址[/img]`。可使用本仓库已推送的公开原图 URL 或实际 Steam 图片 CDN URL；不能使用本机路径。上传前校验图片哈希、大小、路径和正文内嵌链接，随后通过 Steamworks 把同一张图片加入该 Mod 的工坊图库。发布验证还须检查匿名页面确实包含正文图片，以及图片 URL 可下载。

Steamworks 附加图片要求小于 1 MiB，支持 PNG/JPG/GIF，见 [Valve 的 AddItemPreviewFile 文档](https://partner.steamgames.com/doc/api/ISteamUGC#AddItemPreviewFile)。需要压缩时保留原始采集文件及其哈希，展示图不改写游戏内容或伪造按钮。

发布状态中的 `gallery` 仅记录收到成功回调的图库槽位。相同内容跳过，原槽位换图则更新，新图追加；提交结果未知时保留 `gallery_pending`，先依据远端实际结果解决，再重试，避免重复追加。没有截图清单的旧项目继续按原流程工作。
