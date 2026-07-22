# 提交前最终自检

> 生成时间：2026-07-22 ｜ 全部项均已实际核验（含**从零新建环境的完整执行**）。

## 关键修复（对照 GPT 复核第 6 轮）

| 修复 | 内容 |
|---|---|
| 目录名 | `skfolio_001_appendix` → `skfolio_001`（`negative_selftest.py`/`freeze_checksums.py` 按此固定名工作，改名后不再断） |
| Patch 统一 | 主案例 `cases/skfolio_002/agent_run/patch.applyable.diff` 现即正式 run 03 patch（`26830fed`），与 `official_run/agent.patch` 逐字一致；删除旧内部盲测记录，消除"两个 patch"歧义 |
| 环境步骤 | README/reproduction 改为在 metadata 预期位置新建 `.envs/skfolio` 与 `.envs/_runner`，**补上此前遗漏的 `pytest`**（这是首次全新执行时唯一暴露的隐藏依赖），不再宣称免配置一键 |
| 复现安全 | 所有打补丁/注入测试改在 `/tmp` 临时副本进行，绝不改动提交的冻结 Base |
| 措辞 | session UUID 表述为"平台运行元数据"，不称"完全无害"；报告精简 skfolio 介绍、中性化 semi_variance 叙述 |

## 从零环境完整执行结果（新建 `.envs` 后实跑，非断言）

| 命令 | 结果 |
|---|---|
| `validate_case.py cases/skfolio_002` | **FINAL 6/7**（唯一失败 Hidden completeness） |
| `negative_selftest.py` | **6/6** 符合预期 |
| Gold 验证（/tmp 副本 + gold.patch + 隐藏测试） | **4 passed**（行为 Oracle 7/7） |
| 正式 Agent Patch 三项拆分 | target **PASS** / completeness **FAIL** / regression **PASS** |

## 逐项核验

| # | 核验项 | 结果 |
|---|---|---|
| 1 | 主报告 6/7 与日志/grader_result 一致 | ✅ |
| 2 | 三项拆分口径一致（target/completeness/regression） | ✅ |
| 3 | Gold 行为 Oracle 7/7 | ✅ 新环境复现 |
| 4 | 主案例 patch == 正式 run 03 patch（`26830fed`） | ✅ 一致（sha256 比对） |
| 5 | 原始 raw JSONL 未修改（`6329e201…`） | ✅ |
| 6 | submission 内 checksums 自洽；task/grader 与原冻结值一致 | ✅（001 task `6d549c1b`；002 task `a7717398`/grader `0af33174`；002 patch `26830fed`） |
| 7 | submission 无 API Key | ✅ 0 命中 |
| 8 | submission 无本机用户路径/主机名/代理名 | ✅ 0 命中（本清单第 8 行的字面示例除外） |
| 9 | 运行痕迹（workspace 路径/UUID）仅存原始 raw，派生/结果已脱敏 | ✅ |
| 10 | 无 venv/缓存/results/tar | ✅ |
| 11 | 无未落地平台代码（adapters/build_case/agents.yaml） | ✅ |
| 12 | 两次无效运行未作主线（仅 limitations 提及） | ✅ |
| 13 | 命令用 `<PROJECT_ROOT>`/相对路径 | ✅ |
| 14 | JSON 文件合法 | ✅ |
| 15 | README 30 秒可懂入口 | ✅ |
| 16 | **从零新建环境按 README/reproduction 全流程跑通** | ✅（本轮实测，pytest 缺失已修） |

## 证据指纹（sha256 前 16 位）

- `official_run/agent.patch` = `cases/skfolio_002/agent_run/patch.applyable.diff` = `26830fed40bd54bb`
- `official_run/claude_stream.raw.jsonl`（原始，未公开，本地留存）：`6329e20108e33ce1`；公开仓库分发同源脱敏版 `claude_stream.sanitized.jsonl`（详见 `official_run/PROVENANCE.md`）
- 002 task `a7717398c52d2bb0` / grader `0af331745234dcd3`；001 task `6d549c1b87522c79`

## 提交前人工仍需确认

- [ ] 打包时对 `submission/` 目录 zip 即可（`.env.local`、`.envs/`、外部 `audit_backups/` 均在其外）；
- [ ] 评委需按 `docs/reproduction.md` 自建 `.envs`（含 pytest），首次装依赖数分钟；
- [ ] 如需 PDF，由 `report.md` 转换（本轮按要求只保留 Markdown）。
