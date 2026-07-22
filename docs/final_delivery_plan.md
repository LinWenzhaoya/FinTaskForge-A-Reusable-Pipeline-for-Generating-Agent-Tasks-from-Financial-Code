# 最终收敛与交付计划

> 生成时间：2026-07-22 ｜ 状态：审计 + 清理冻结 + 动态验收均已完成
> 关联文档：[current_state_audit.md](current_state_audit.md)（审计）｜本文件（收敛建议）
> 本轮范围：审计 → 清理冻结两个 Case → 重跑验收 → 收敛建议。**未新增 Case、未开发 Harness/Adapter、未调用 API、未 Docker 化。**

---

## 0. 本轮已完成的变更（对照复审口径 7 条）

| # | 复审口径要求 | 落实情况 |
|---|---|---|
| 1 | 去泄漏属清理，冻结前完成 | ✅ 002 公开测试 docstring/assert/函数名、TASK.md 根因提示全部去除；同步改 metadata `required_output_patterns` |
| — | assert 消息也泄漏 | ✅ 改中性 `weighted variance result mismatch`，baseline 复现仍 `req_ok=True` |
| 2 | D1 理由独立于泄漏 | ✅ 写"加权方差为基础统计概念，金融语义有帮助但非必要" |
| 3 | 验收前状态设 pending | ✅ 先置 `pending_verification/pending/pending`，跑完按日志回填 |
| 4 | Gold/Agent 各用临时副本 | ✅ Gold 用临时副本改 `patch_file`；Agent 走标准 Case；分别存 `gold.log`/`agent.log`，副本跑完即删 |
| 5 | 备份放项目外 | ✅ `../audit_backups/20260722/`，不在交付目录内 |
| 6 | `valid/nonexistent` 写"疑似" | ✅ 审计文档已用"疑似运行残留（agent 或负向自测）" |
| 7 | 统一两题 checksum | ✅ `case-freeze-v1`：`task_tree/grader_tree/agent_patch` 三字段，两题同规则 |
| — | 001 保留 anti-hack、002 改 completeness | ✅ 001 术语未动；002 全部改 completeness/related-behavior |
| — | `repo.tar.zst` 移出 | ✅ 已删，两题统一以 `task/repo/` 为唯一 Base |

**动态验收结果（`results/final_verification/`）**

| 目标 | 结果 | 日志 |
|---|---|---|
| skfolio_001（Agent patch） | **PASS 7/7** | `001.log` |
| skfolio_002 **Gold** Patch | **PASS 7/7** | `gold.log` + `002_gold.result.json` |
| skfolio_002 **Agent** Patch | **FAIL 6/7**（仅 Hidden/completeness 失败） | `agent.log` |
| negative_selftest | **6/6 符合预期** | `negative.log` |

---

## 1. 最终应提交的文件（核心交付）

```text
financial-benchmark/
├── cases/
│   ├── skfolio_001/              # ✅ Base 洁净 + Agent PASS 7/7
│   │   ├── metadata.yaml
│   │   ├── checksums.json        # case-freeze-v1
│   │   ├── task/{TASK.md,README.md,requirements-pinned.txt,repo/}
│   │   ├── grader/{reference.patch,hidden_tests/}
│   │   ├── agent_run/{patch.applyable.diff,patch.diff,prompt.md,trajectory.md}
│   │   └── 盲测判分记录.md
│   └── skfolio_002/              # ✅ 去泄漏 + Base 洁净 + Gold PASS / Agent FAIL(6/7)
│       ├── metadata.yaml         # D1；case_status/gold/agent 三态已回填
│       ├── checksums.json        # case-freeze-v1（与 001 同 schema）
│       ├── task/{TASK.md,README.md,requirements-pinned.txt,repo/}
│       ├── grader/{gold.patch,reference.patch,hidden_tests/}
│       └── agent_run/patch.applyable.diff
├── pipeline/
│   ├── validate_case.py          # 冻结 v0.2 通用 Validator（核心）
│   ├── negative_selftest.py      # 负向自测 6/6（核心）
│   ├── _common.py                # 共享工具（核心）
│   └── freeze_checksums.py       # 本轮新增：统一冻结工具（轻量，随交付）
├── environments/skfolio_py312_v1/{Dockerfile,create_env.sh,environment.yaml,requirements-pinned.txt}
├── templates/case_template/      # 造题模板
├── results/
│   ├── skfolio_001.json          # 最新：PASS
│   ├── skfolio_002.json          # 最新：FAIL(6/7)
│   └── final_verification/       # 本轮四项验收日志 + gold 结果 json
└── docs/
    ├── pipeline.md               # 报告主体：管线设计 + 方法论
    ├── current_state_audit.md    # 审计（本轮）
    ├── final_delivery_plan.md    # 本文件
    ├── 复用性实验_两题成本对比.md
    ├── 验收001_empyrical60_淘汰.md
    └── 验收002_skfolio196_可用.md
```

---

## 2. 应移到 `experimental/` 的文件（平台化草稿，非主线交付）

本轮明确禁止推进的 Agent Harness / Adapter 相关草稿，建议整体移入 `experimental/` 并在报告中标为"未来工作"：

| 文件/目录 | 原因 |
|---|---|
| `pipeline/adapters/base.py`、`adapters/external_cli.py` | Agent Adapter 接口——平台化草稿，`run_agent.py` 主流程从未落地 |
| `config/agents.yaml` | Agent Harness 配置（引用了不存在的 `run_agent.py`） |
| `.env.example` | 仅 Harness/API 需要 |
| `runs/` | 空的 Harness 输出目录 |
| `pipeline/build_case.py` | 归档+旧 checksum 构建器；已被 `freeze_checksums.py` 取代校验和职责，且产出的 `repo.tar.zst` 已移除。可移入 experimental 或删除 |

> 建议操作：`mkdir experimental && git mv`（若纳入 git）或普通移动；移动后确认 `pipeline/validate_case.py`、`negative_selftest.py`、`freeze_checksums.py` 不 import 上述模块（当前不 import，安全）。

---

## 3. 应写入最终报告的内容

1. **方法论主线**（已在 `docs/pipeline.md`）：Issue→Fix→Test→去泄漏→封装→盲测的可规模化造题管线；两条造题范式的权衡与选择。
2. **两道完整实例**：
   - skfolio_001（MaximumDiversification 负收益，D2）：Agent **完整解出 7/7**——展示"能造出可解、Oracle 明确的题"。
   - skfolio_002（加权方差 sample_weight，D1）：Agent **6/7，唯一失败在 completeness 测试**——展示"隐藏完整性测试能抓住'对了一半'的不完整修复"，比满分通过更有说服力。
3. **验收体系三层结构**（务必在报告中明确区分，避免读者误解）：
   - **Case 有效性**：baseline 能复现 + Gold Patch 能通过；
   - **Gold 结果**：官方修复 7/7；
   - **Agent 结果**：被测 Agent 的真实表现（001 通过 / 002 不完整）。
4. **Validator 可信度证据**：negative_selftest 6/6（安装失败/测试缺失/删测试/白名单越界/非测试注入/metadata 缺失），证明"该失败时确实失败"。
5. **复用性**：002 复用 001 的环境与 Validator，零改 `validate_case.py`（见 `复用性实验_两题成本对比.md`）。
6. **去泄漏的方法论价值**：001 与 002 去泄漏程度的对比，以及 assert 消息也可能泄漏根因这一细节——体现对"公开信号面"的控制。

---

## 4. 提交前必须修复/确认的事项

| 优先级 | 事项 | 说明 |
|---|---|---|
| 🔴 必做 | **排除 `.env.local`** | 含 `ANTHROPIC_AUTH_TOKEN`。已 gitignore，但整包 zip 会带出。打包前显式删除/排除，并轮换该 token（已进过备份目录） |
| 🔴 必做 | **备份目录不进交付包** | `../audit_backups/20260722/` 含去泄漏前的旧答案版本，绝不可混入提交 |
| 🟡 建议 | 移动 experimental/ | 见第 2 节，避免评审者误以为 Harness 已实现 |
| 🟡 建议 | agent_run 不对称说明 | 001 有 prompt.md/trajectory.md，002 只有 patch。报告中说明 002 盲测轨迹见 `盲测判分记录.md`；或补齐 002 的 prompt/trajectory |
| 🟢 可选 | grader 命名统一 | 001 仅 `reference.patch`，002 有 `gold.patch`+`reference.patch`（内容相同）。统一说明"reference=gold=官方 fix" |

---

## 5. 列为未来工作的平台化内容（本轮明确不做）

- `run_agent.py` / `grade_run.py`：Agent 运行与判分主流程（当前只有 Adapter 接口草稿）；
- 多模型调度、Adapter 体系（claude_sdk / anthropic_tool_loop 等备选适配器）；
- SWE-bench 兼容层、Docker 化环境分发；
- 规模化造题（>2 Case）与批量盲测。

> 这些均属"平台化"，与本笔试核心交付（证明造题管线可行 + 两道验证实例）正交。报告中作为"可扩展方向"陈述即可，不应作为交付主体。

---

## 6. 冻结基线（case-freeze-v1，用于校验交付未被篡改）

| Case | task_tree_sha256(前16) | grader_tree_sha256(前16) | agent_patch_sha256(前16) |
|---|---|---|---|
| skfolio_001 | `6d549c1b87522c79` | `f6e44086cbb5b647` | `8b3136ab123221d3` |
| skfolio_002 | `b33d790497ffa65c` | `0af331745234dcd3` | `581e3b17ce308973` |

> 复算命令：`.envs/_runner/bin/python pipeline/freeze_checksums.py`（幂等；范围含 task/+grader/+agent patch，排除 results/缓存/.envs/备份/metadata.yaml）。metadata 状态字段回填不影响上述哈希。
