# 提交资产审计(只读)

> 生成时间：2026-07-22 ｜ 模式：最终提交收敛（只读审计，未修改任何原始资产）
> 目的：确认哪些进入 `submission/`、哪些必须排除、有无密钥/本机路径泄漏、run 03 证据是否完整。

---

## 0. 结论速览

| 审计项 | 结论 |
|---|---|
| 主案例 | `skfolio_002`（`skfolio_001` 作附录） |
| run 03 正式记录完整性 | ✅ 18/18 文件齐全（prompt/raw/stderr/派生/环境/时间/patch/评分/metadata） |
| raw stream 含 API Token | ✅ **0 命中**（token 经 env 传入，未进流） |
| raw stream 含 `宿主用户绝对路径` | ✅ **0 命中**（Agent 全程在 `/tmp` 工作，从未见宿主用户路径） |
| raw stream 含 internal-proxy base_url | ✅ **0 命中** |
| raw stream 含 `/tmp/agent_ws` | ⚠️ 68 命中（不可避免的运行路径，保留原始+另出脱敏可读版） |
| raw stream 含 session_id | ⚠️ 231 命中（随机 UUID，非密钥；脱敏版移除） |
| pipeline 核心 3 文件 | ✅ 无绝对路径、无 token、无 internal-proxy |
| 标准 Case checksum | ✅ 已记录（见 §3），提交后须与冻结值一致 |

---

## 1. 主案例当前目录与关键文件（`cases/skfolio_002/`）

```text
cases/skfolio_002/
├── metadata.yaml        # D1；case_status=valid / gold=pass / agent=fail；三态已回填
├── checksums.json       # case-freeze-v1
├── task/                # 交给 Agent 的材料（已去泄漏）
│   ├── TASK.md          # 仅现象，无根因/修法泄漏
│   ├── README.md        # 已修正目录歧义（pip install -e ./repo; cd repo）
│   ├── requirements-pinned.txt
│   └── repo/            # 修复前 Base 快照（buggy）
├── grader/              # 出题方保留，不进 Agent 可见范围
│   ├── gold.patch       # 官方修复（variance + semi_variance 两处）
│   ├── reference.patch  # = 官方 fix commit e7e60cb
│   └── hidden_tests/test_hidden_regression.py   # target/completeness/regression
└── 盲测判分记录.md       # 旧盲测内部记录（术语已统一 completeness）
```

## 2. run 03 正式记录完整性（`runs/skfolio_002_official_20260722_03/`）

全部存在（18 项）：
- `records/`：prompt.md、**claude_stream.raw.jsonl（785 KB，唯一证据源）**、claude_stderr.log(空)、trajectory.md、terminal.log、final_answer.md、environment.txt、started_at/finished_at/exit_code
- `output/`：agent.patch、changed_files.txt、git_status.txt、untracked_files.txt(空)、grader.log、grader_result.json、hidden_split.log
- `run_metadata.json`（模型/会话/时间/隔离/工具/禁网口径/隐藏三项拆分）

**评分事实（来自 grader_result.json + hidden_split.log）**：

| 评分项 | 结果 |
|---|---|
| Base 复现 | PASS |
| Patch 应用 | PASS |
| 路径约束 | PASS |
| Public | PASS |
| Hidden Target | PASS |
| **Hidden Completeness** | **FAIL** |
| Hidden Regression | PASS |
| 总结果 | **6/7** |

- official agent.patch sha256(16)：`26830fed40bd54bb`（仅改 `src/skfolio/measures/_measures.py`，无未跟踪源码）
- 模型：`claude-opus-4-8[1m]`（requested=resolved）；num_turns=67；exit=0

## 3. 标准 Case checksum（提交后须一致）

| Case | task_tree(16) | grader_tree(16) | agent_patch(16) |
|---|---|---|---|
| skfolio_001 | `6d549c1b87522c79` | `f6e44086cbb5b647` | `8b3136ab123221d3` |
| skfolio_002 | `a7717398c52d2bb0` | `0af331745234dcd3` | `26830fed40bd54bb` |

> 注：标准 Case 内置的 agent patch 已统一为正式盲测 run 03 的提取物（`26830fed`，与 `official_run/agent.patch` 逐字一致）。

## 4. 应进入最终提交（`submission/`）

- `pipeline/`：`validate_case.py`、`negative_selftest.py`、`freeze_checksums.py`（+ 一份说明 README）
- `cases/skfolio_002/`：task/grader/metadata.yaml/checksums.json（主案例）
- `cases/skfolio_001/`：001 精简副本（证明同仓库复用）
- `official_run/`：run 03 的 prompt/raw jsonl/trajectory/terminal/final_answer/environment/agent.patch/changed_files/grader.log/grader_result.json/run_metadata.json
- `docs/`：reproduction.md、limitations.md、final_checklist.md
- `README.md`、`report.md`、`submission_manifest.txt`

## 5. 必须排除（确认均存在于原项目，不复制进 submission）

| 项 | 原因 |
|---|---|
| `.env.local` | 含 `ANTHROPIC_AUTH_TOKEN`（密钥，绝不提交） |
| `.env.example` | Harness 用 |
| `.envs/` | 本机 venv |
| `config/agents.yaml` | Agent Harness 配置（引用未落地的 run_agent.py） |
| `pipeline/adapters/` | Adapter 草稿（平台化，禁止推进项） |
| `pipeline/build_case.py` | 旧归档/校验构建器（已被 freeze_checksums 取代） |
| `runs/*_01_invalid`、`*_02_invalid` | 两次无效基础设施运行（仅在 limitations 一句话说明） |
| `../audit_backups/` | 外部备份，含去泄漏前旧答案 |
| `__pycache__`、`.pytest_cache` | 缓存 |

## 6. 平台化未完成代码现状

`run_agent.py` / `grade_run.py` **从未落地**（`config/agents.yaml` 引用但文件不存在）；Adapter 仅接口草稿。符合"未推进平台化"，这些不进主交付。

## 7. 隐私/可移植性处置方案（§见后续清理步骤）

- API Token：submission 全域 0 出现（已确认原项目 token 仅在被排除的 `.env.local`）。
- `/tmp/agent_ws` 与 session UUID：仅存在于 `official_run/claude_stream.raw.jsonl`。**原始 raw 不修改**（证据完整性），README 注明；另生成 `claude_stream.redacted.jsonl` 供阅读，将 `/private/tmp/agent_ws_.../` 与 session UUID 替换为占位符。
- 报告/README/复现说明中一律用相对路径或 `<PROJECT_ROOT>` 占位符，不含 `宿主用户绝对路径`。

---

## 8. 无效运行附注（不进主线）

run 01（漏 `cd` 工作目录 → cwd 错误、benchmark 路径暴露）、run 02（编排门禁把 `/tmp`↔`/private/tmp` 符号链接误判而中止，模型 0 工具调用）——均为**基础设施无效运行**，模型未获得有效任务或隔离不成立，不计入正式结果。原始证据保留在 `runs/*_invalid/`（不进 submission），最终报告仅在局限性中一句话说明。
