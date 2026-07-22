# 金融 Agent 造题笔试 · 提交包

> **一句话**：从真实金融开源库 skfolio 的"缺陷→官方修复→测试"链条中，构造一道有明确行为 Oracle、有区分度的代码修复任务，并用最强 Agent（Claude Opus 4.8）在隔离环境中正式盲测，结果 **6/7**。

## 30 秒速览

| 问题 | 答案 |
|---|---|
| **1. 用了什么材料？** | skfolio（金融组合优化库）风险度量模块的**加权方差缺陷**及其**官方修复** commit，含修复前代码、官方 Patch、可执行测试。真实、专业、可判定。 |
| **2. 怎么把材料变成题？** | 回退到修复前 Base → 隐藏官方 Patch → 中性化题面（去泄漏）→ 提供 1 个公开复现测试 + 3 个隐藏测试（target/completeness/regression）→ Base fail / Gold pass 门禁。 |
| **3. 标准答案与评分依据？** | 官方 Patch + 加权方差数学定义 + **Gold 验证 7/7**（行为 Oracle，不要求代码逐字一致）。评分器 `validate_case.py` + 负向自测 6/6 保证不误判。 |
| **4. 最强 Agent 实测结果？** | Claude Opus 4.8 隔离盲测：正确修复显式的 `variance` 问题（Public+Target+Regression 通过），但漏改同源 `semi_variance`（Completeness FAIL），最终 **6/7**。证明题目能区分**局部修复 vs 完整修复**。 |

## 文件入口

```text
submission/
├── README.md          ← 你在这里
├── report.md          ← 主报告(建议先读)：材料→造题管线→主案例→正式实测→分析→规模化→局限
├── pipeline/          ← 造题/验收核心工具
│   ├── validate_case.py     配置驱动的通用验收 Runner(冻结 v0.2)
│   ├── negative_selftest.py 负向自测(6/6，证明评分器不误判)
│   ├── freeze_checksums.py  标准资产冻结
│   ├── _common.py           共享工具
│   └── README.md
├── cases/
│   ├── skfolio_002/         ★ 主案例(task/grader/metadata/checksums)
│   └── skfolio_001/         附录：同仓库复用验证
├── official_run/      ← ★ 正式盲测 run 03 完整记录
│   ├── prompt.md / claude_stream.sanitized.jsonl(脱敏原始流) / trajectory.md / terminal.log / final_answer.md
│   ├── environment.txt / agent.patch / changed_files.txt / PROVENANCE.md(原始流 SHA256)
│   ├── grader.log / grader_result.json / hidden_split.log
│   └── run_metadata.json
└── docs/
    ├── reproduction.md    复现步骤(Base 复现 / Gold 验证 / 官方 patch 评分 / 负向自测)
    ├── limitations.md     局限性与诚实边界
    └── final_checklist.md 提交前自检
```

## 如何复现

需 **Python 3.12**。提交包不含虚拟环境，需先按 `metadata.yaml` 预期的位置创建（首次装依赖耗时数分钟）。完整步骤见 [`docs/reproduction.md`](docs/reproduction.md)，最小路径如下（在解压后的 `submission/` 内执行）：

```bash
# 1) 在 metadata 预期位置创建 Case 环境(含 skfolio 依赖 + pyyaml)
python3.12 -m venv .envs/skfolio
./.envs/skfolio/bin/pip install -U pip setuptools wheel
./.envs/skfolio/bin/pip install -r cases/skfolio_002/task/requirements-pinned.txt pytest pyyaml
# 2) 负向自测需要的 Runner 环境(仅 pyyaml)
python3.12 -m venv .envs/_runner && ./.envs/_runner/bin/pip install -q pyyaml

# 主案例验收(agent_run 即正式 run 03 的 patch，预期 6/7，唯一失败为 Hidden completeness)
./.envs/_runner/bin/python pipeline/validate_case.py cases/skfolio_002
# 评分器负向自测(预期 6/6)
./.envs/_runner/bin/python pipeline/negative_selftest.py
```

> `cases/skfolio_002/agent_run/patch.applyable.diff` **就是**正式 run 03 提取的 Agent 修复（与 `official_run/agent.patch` 逐字一致，sha256 前16位 `26830fed`）。因此上面的验收复现的正是正式盲测的 6/7。

## 关于 official_run 证据

- **原始 stream 未公开、脱敏版随仓库分发**：CLI 输出的原始 `claude_stream.raw.jsonl` 含本机运行元数据（主机名、宿主绝对路径、session_id、临时 workspace 路径），故**不进公开仓库**，仅保留在本地（其 SHA256 见 `PROVENANCE.md`，可按需私下核验）。公开仓库提供逐条脱敏的 `claude_stream.sanitized.jsonl`：**内容零改动**，仅把上述本机标识替换为占位符（`<HOST>`/`<HOME>`/`<PROJECT_ROOT>`/`<WORKSPACE>`/`<SESSION_ID>`/`<PROXY_HOST>`），不改动每条消息自带的随机 `uuid`。经检查脱敏版不含任何 API 密钥、认证信息、用户名或主机名。`trajectory.md`/`terminal.log`/`final_answer.md` 是从同一原始流派生并脱敏的可读版本。
- **正式实验只认定 run 03**。此前两次运行因编排问题（工作目录、路径符号链接归一）被判无效，不计入正式结果，未包含在本提交包中（说明见 `docs/limitations.md`）。

## 不含内容
本提交包**不含**：API Key / `.env.local` / 虚拟环境 / 缓存 / 未落地的 Adapter·Harness 实验代码 / 两次无效运行的大文件 / 外部备份。
