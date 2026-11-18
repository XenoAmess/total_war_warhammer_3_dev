from pathlib import Path
import argparse,json
p=argparse.ArgumentParser();p.add_argument('--mod',required=True,choices=['recruitment_refresh']);p.parse_args()
repo=Path.cwd();docs=repo/'mods/recruitment_refresh/docs'
record=json.loads((docs/'workshop-publication-0.3.4.json').read_text(encoding='utf-8'))
assert record['status']=='PUBLISHED_PUBLIC_SUBSCRIBED_VERIFIED'and record['steam_final_mode']=='offline'
def replace(path,old,new):
 text=path.read_text(encoding='utf-8');assert old in text,str(path)+' expected text missing'
 path.write_bytes(text.replace(old,new).encode('utf-8'))
replace(repo/'README.md','`0.3.3 Alpha` 已发布；混矮车队与领主法术系修复，订阅包哈希及载入核对通过','`0.3.4 Alpha` 已发布；巴什瓦商队面板恢复与 DLC 直接补验，订阅包哈希及载入核对通过')
p=repo/'mods/recruitment_refresh/README.md';text=p.read_text(encoding='utf-8');parts=text.split('\n\n',2);assert'0.3.4 本地候选'in parts[1]
parts[1]='**0.3.4 已公开发布至[原工坊条目](https://steamcommunity.com/sharedfiles/filedetails/?id=3830548217)。** 修复巴什瓦商队刷新后招募页未恢复的问题；199 项离线测试通过，直接补验爪语者三系、巴什瓦运输将领、四种灾祸领主及迁都兼容、实际操作后的存读档。公开正文、更新日志、依赖、启动器元数据、封面与原图库均核对通过，真实订阅下载包与验收包哈希相同，订阅包离线前端载入身份核对通过；测试装载已清理，Steam 已恢复普通客户端主动离线。夹具和未验范围见[第二批 DLC 报告](docs/dlc-compatibility-20261118-round2.md)，发布验证见[回执](docs/workshop-publication-0.3.4.json)。以下 0.3.3 及更早记录描述发布当时的历史状态。'
p.write_bytes('\n\n'.join(parts).encode('utf-8'))
replace(repo/'mods/recruitment_refresh/CHANGELOG.md','## 0.3.4 — 2026-11-18（候选，未上传工坊）','## 0.3.4 — 2026-11-18（已发布）')
replace(repo/'mods/recruitment_refresh/CHANGELOG.md','## 0.3.3 — 2026-11-18（已发布）','- 原工坊条目更新完成；公开正文／更新日志、依赖、启动器元数据、封面与原图库核对通过；真实订阅包哈希及离线前端载入身份一致。测试装载已清理，Steam 主动离线，见[发布回执](docs/workshop-publication-0.3.4.json)。\n\n## 0.3.3 — 2026-11-18（已发布）')
replace(docs/'README.md','# 招募候选刷新文档\n','# 招募候选刷新文档\n\n- [0.3.4 巴什瓦、四种灾祸领主与两 Mod 直接补验](dlc-compatibility-20261118-round2.md)\n- [0.3.4 创意工坊发布回执](workshop-publication-0.3.4.json)\n')
replace(docs/'dlc-compatibility-20261118-round2.md','最终冷启动候选 **0.3.4**','最终冷启动包 **0.3.4**')
replace(docs/'dlc-compatibility-20261118-round2.md','**尚未上传创意工坊**；已发布版本仍为 0.3.3。','**已发布至原创意工坊条目并核对真实订阅包**，见[发布回执](workshop-publication-0.3.4.json)。')
replace(docs/'dlc-compatibility-20261118-round2.md','L0–L3 通过，L4 未执行，工坊仍为已发布的 0.3.3。本轮没有上传工坊，也没有把单机结果外推为联机或其他新 DLC 派系通过。','L0–L4 通过，工坊 0.3.4 已发布。工坊上传与订阅包验证属于后续独立发布阶段，没有把单机结果外推为联机或其他新 DLC 派系通过。')
replace(repo/'docs/dlc-activation-2026-11-18-round2.md','0.3.4 未上传工坊；最终 Steam 主动离线。','0.3.4 已发布至原工坊条目并核对真实订阅包；最终 Steam 主动离线。')
replace(repo/'docs/dlc-acceptance-ledger.md','`0.3.4` **未上传工坊**，见[精确包验收](../mods/recruitment_refresh/docs/acceptance-results-0.3.4.json)。','`0.3.4` **已发布并核对真实订阅包**，见[精确包验收](../mods/recruitment_refresh/docs/acceptance-results-0.3.4.json)及[发布回执](../mods/recruitment_refresh/docs/workshop-publication-0.3.4.json)。')
replace(repo/'docs/dlc-acceptance-ledger.md','本批工坊发布状态以[0.3.3 精确包验收](../mods/recruitment_refresh/docs/acceptance-results-0.3.3.json)及对应发布回执为准，不由授权快照推定。','当前工坊发布状态以[0.3.4 精确包验收](../mods/recruitment_refresh/docs/acceptance-results-0.3.4.json)及对应发布回执为准，0.3.3 为第一批历史，不由授权快照推定。')
p=repo/'docs/dlc-activation-2026-11-18-round2.json';data=json.loads(p.read_text(encoding='utf-8'));native=data['native_acceptance'];native.pop('recruitment_refresh_candidate',None);native.update(recruitment_refresh_release='0.3.4 PUBLISHED_PUBLIC_SUBSCRIBED_VERIFIED',publication_record='../mods/recruitment_refresh/docs/workshop-publication-0.3.4.json');p.write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print('Published state reconciled across release documentation')
