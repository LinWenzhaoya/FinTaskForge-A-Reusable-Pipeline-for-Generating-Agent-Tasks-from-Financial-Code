# 全项目状态审计（只读）

> 生成时间：2026-07-22 ｜ 模式：审计与收敛（未修改任何文件）
> 审计对象：`<PROJECT_ROOT>`
> 方法：目录遍历 + 源码行级核验 + patch 干跑 + 校验和重算，全程只读。

---

## 0. 结论速览

| 审计项 | 结论 |
|---|---|
| 两个 Case 是否仍是修复前 Base | ✅ 都是 Base（001/002 目标源码行仍为 buggy 形态） |
| Agent Patch 能否干净应用到 Base | ✅ 001/002 均 `patch --dry-run` exit=0 |
| 残留 `.git/.github/.venv/.pytest_cache/egg-info` | ✅ cases 内无；仅 `pipeline/__pycache__` 一处（gitignored，无害） |
| 运行残留（非答案） | ⚠️ `skfolio_002/task/repo/` 下有 2 个空目录 `valid/`、`nonexistent/`（agent 探索残留） |
| 答案泄漏 | 🔴 **skfolio_002 公开测试 docstring 直接写出修复代码**；TASK.md 强暗示根因 |
| 校验和一致性 | ⚠️ 002 `grader_tree` 已漂移（gold.patch 在冻结后 4 秒加入）；task_tree 仍一致 |
| Validator / 负向自测可运行性 | ✅ 语法编译通过、runner 环境含 pyyaml、两套 venv 存在（完整跑放第 3 步） |
| 平台化草稿是否混入主线 | ⚠️ adapters / agents.yaml / build_case.py / .env* / runs 属实验性，未隔离 |

**最重要的三件事**（详见第 5 节）：
1. 🔴 **skfolio_002 答案泄漏**——公开测试文件 docstring 第 3-4 行明写 `修复后: 用加权均值 mean(returns, sample_weight=w)`，等于把 Gold Patch 交给被测 Agent。这也是 `domain_necessity` 该从 D2 降到 D1 的根本原因。
2. ⚠️ **skfolio_002 运行残留**——`task/repo/` 下 `valid/`、`nonexistent/` 两个空目录，非源码、非测试，属 agent 直接改动后的残留，破坏 Base 洁净性。
3. ⚠️ **校验和已过期**——002 `grader_tree` 与 `checksums.json` 不符（gold.patch 后加入），且 001 根本没有 `checksums.json`；清理后需统一重算。

---

## 1. 实际目录树（核心层，已省略 `.envs/` site-packages 与 `task/repo/` 内部）

```text
financial-benchmark/
├── .env.example                 # 实验性（Agent Harness 用）
├── .env.local                   # 实验性 + 敏感：含 ANTHROPIC_AUTH_TOKEN（gitignored）
├── .gitignore
├── cases/
│   ├── skfolio_001/
│   │   ├── metadata.yaml         # 含 source_issue196 / base 5d673e7 / fix c2cc1ad（在 task/ 外，设计如此）
│   │   ├── task/
│   │   │   ├── TASK.md           # ✅ 无泄漏
│   │   │   ├── README.md
│   │   │   ├── requirements-pinned.txt
│   │   │   └── repo/             # Base 快照（buggy）
│   │   ├── grader/
│   │   │   ├── reference.patch   # 官方 fix（含 commit/issue，出题方保留）
│   │   │   └── hidden_tests/test_hidden_regression.py
│   │   ├── agent_run/
│   │   │   ├── patch.applyable.diff   # 被 validator 使用
│   │   │   ├── patch.diff             # 原始（冗余）
│   │   │   ├── prompt.md
│   │   │   └── trajectory.md
│   │   └── 盲测判分记录.md
│   └── skfolio_002/
│       ├── metadata.yaml         # domain_necessity=D2（应降 D1）；注释仍用 "anti-hack"
│       ├── checksums.json        # ⚠️ grader_tree 已过期
│       ├── task/
│       │   ├── TASK.md           # 🔴 line13 强暗示根因
│       │   ├── README.md
│       │   ├── requirements-pinned.txt
│       │   ├── repo.tar.zst      # 归档（build_case 产物）
│       │   └── repo/             # Base 快照（buggy）
│       │       ├── valid/        # 🔴 运行残留（空目录）
│       │       └── nonexistent/  # 🔴 运行残留（空目录）
│       ├── grader/
│       │   ├── gold.patch        # 冻结后 4s 加入 → grader_tree 漂移
│       │   ├── reference.patch
│       │   └── hidden_tests/test_hidden_regression.py  # 注释用 "anti-hack"，应改 completeness
│       └── agent_run/
│           └── patch.applyable.diff   # ⚠️ 仅此一份，缺 prompt.md/trajectory.md（与 001 不对称）
├── config/agents.yaml            # 实验性（Agent Harness）
├── docs/
│   ├── pipeline.md               # 核心：管线设计与方法论（报告主体）
│   ├── 复用性实验_两题成本对比.md    # 核心
│   ├── 验收001_empyrical60_淘汰.md  # 核心（决策记录）
│   └── 验收002_skfolio196_可用.md   # 核心（决策记录）
├── environments/skfolio_py312_v1/
│   ├── Dockerfile / create_env.sh / environment.yaml / requirements-pinned.txt
├── pipeline/
│   ├── validate_case.py          # 🟢 核心：冻结 v0.2 通用 Validator（251 行）
│   ├── negative_selftest.py      # 🟢 核心：负向自测（114 行）
│   ├── _common.py                # 🟢 核心：共享工具（哈希/归档/apply）
│   ├── build_case.py             # ⚠️ 实验性：归档+checksum 构建器（002 用过）
│   ├── adapters/base.py          # ⚠️ 实验性：Agent Adapter 接口
│   ├── adapters/external_cli.py  # ⚠️ 实验性：CLI 适配器
│   └── __pycache__/              # 无害缓存
├── results/
│   ├── skfolio_001.json          # 上轮：final=PASS
│   ├── skfolio_002.json          # 上轮：final=FAIL（漏改 semi_variance）
│   └── build/skfolio_002.json
├── runs/                         # 空（Harness 输出目录，实验性）
├── templates/case_template/      # 🟢 核心：造题模板
└── .envs/{skfolio,_runner}/      # 两套 venv（gitignored，不提交）
```

---

## 2. 文件分类：核心交付 vs 实验性平台草稿

### 2.1 核心交付（应提交）
- **Validator 三件套**：`pipeline/validate_case.py`（冻结 v0.2）、`pipeline/negative_selftest.py`、`pipeline/_common.py`
- **两个 Case 的 task/grader/agent_run/metadata**（内容详见第 3-5 节）
- **环境定义**：`environments/skfolio_py312_v1/*`
- **方法论文档**：`docs/pipeline.md`、`docs/复用性实验_两题成本对比.md`、`docs/验收001_*`、`docs/验收002_*`
- **验收结果**：`results/*.json`
- **造题模板**：`templates/case_template/*`

### 2.2 实验性平台草稿（本轮明确禁止推进，应移至 `experimental/`）
- `pipeline/adapters/base.py`、`pipeline/adapters/external_cli.py`（Agent Adapter —— 任务禁止项）
- `config/agents.yaml`（Agent Harness 配置）
- `.env.example`、`.env.local`（仅 Harness/API 需要；`.env.local` 含 token，**禁止入任何提交包**）
- `runs/`（空的 Harness 输出目录）
- `pipeline/build_case.py`（归档+校验构建器——介于核心与平台之间；建议保留但标注为"打包工具"，非评测主流程）

> 注：任务清单里点名的 `run_agent.py` / `grade_run.py` **在仓库中并不存在**（`config/agents.yaml` 引用了 `run_agent.py`，但文件从未创建）。即：Harness 主流程只有草稿接口，没有落地实现——符合"未推进平台化"的现状。

---

## 3. 两个 Case 是否仍是修复前 Base

**结论：都是 Base（未被 Gold/Agent 修复过）。**

| Case | 目标文件 | 核验行 | 现状 | 判定 |
|---|---|---|---|---|
| 001 | `src/skfolio/optimization/convex/_mean_risk.py` | 1082-1083 | 仍是旧的嵌套 `if np.isscalar(...)` → `if np.max(mu)-rf<=0` 双层结构 | ✅ buggy Base |
| 002 | `src/skfolio/measures/_measures.py` | 139 | `biased_var = sample_weight @ (returns - mean(returns)) ** 2`（缺 sample_weight） | ✅ buggy Base |
| 002 | 同上 | 180 | `min_acceptable_return = mean(returns)`（semi_variance，缺 sample_weight） | ✅ buggy Base |

> 佐证：两个 Case 的 Agent Patch 与 002 的 Gold Patch 均以 `-p1 --dry-run` **干净应用成功（exit=0）**——若源码已被修复，上下文将不匹配、apply 失败。
> 外部源仓 `../external_workspaces/skfolio` 当前 HEAD=`82f029e`，正是 skfolio_002 的 `base_commit`。

---

## 4. 残留 / 洁净性

| 类型 | 结果 |
|---|---|
| `.git` / `.github` | cases 内 **无** |
| `.venv` / `.pytest_cache` / `__pycache__` / `*.egg-info` | cases 内 **无**；仅 `pipeline/__pycache__/`（runner 字节码缓存，gitignored，无害） |
| 散落 `*.pyc` | cases 内 **无** |
| **空目录残留** | 🔴 `skfolio_002/task/repo/valid/`、`skfolio_002/task/repo/nonexistent/`——两个空目录，非源码/非测试，疑似 agent 曾直接在 002 repo 内跑命令（如路径校验）留下。**需删除。** |

> Validator 洁净性核实：`validate_case.py` 全程 `shutil.copytree` 到 `tempfile.mkdtemp` 的临时副本上操作（临时 `git init` → `git apply` → `rm -rf .git`），成败都清理 tempdir。**跑验收不会污染 Base。** 故上述空目录不是 validator 造成，而是更早的 agent 直接改动残留（与"skfolio_002 曾被 Agent 直接修改过"的记录一致）。

---

## 5. 答案泄漏审计

### 5.1 skfolio_001 —— ✅ 干净
- `task/TASK.md`、`task/README.md`：只描述**现象**（负收益下抛 ValueError）与**期望行为**，不涉及根因位置或修法。
- `task/repo/CHANGELOG.md`：grep `#196/#197/maximum diversification with negative/c2cc1ad` **无命中**（Base 快照早于该 fix 条目）。
- issue/commit（196/197/5d673e7/c2cc1ad）只存在于 `metadata.yaml` 与 `grader/reference.patch`——**都在 `task/` 之外**，属出题方保留，设计如此。
- 公开测试 docstring 只说"修复前抛 ValueError，修复后应正常求解"，**不泄漏修法**。

### 5.2 skfolio_002 —— 🔴 存在实质泄漏
1. **公开测试文件直接写出修复代码**（Agent 可见）：
   `task/repo/tests/test_public_reproduction.py` docstring 第 3-4 行：
   ```
   修复前: 用普通均值 mean(returns) 作中心 -> 结果偏大, 测试失败。
   修复后: 用加权均值 mean(returns, sample_weight=w) -> 与手工正确值一致。
   ```
   这等于把 Gold Patch 的核心改动（`mean(returns, sample_weight=w)`）直接交给被测 Agent。
2. **TASK.md 强暗示根因**：line13 `当前实现的结果偏离了这个定义,说明离差中心用错了。`——明确指向"中心用错"这一根因。
3. 综合 1+2，被测者几乎无需金融知识即可照抄——**这正是 `domain_necessity` 应从 D2 下调为 D1 的证据**。
4. 校验和 / commit（82f029e/e7e60cb）只在 `metadata.yaml` 与 `grader/` 内，未泄漏进 task/。

> **影响**：001 的去泄漏做得干净，002 没做到。若原样提交，002 的难度与"需要金融知识"这一卖点都会被质疑。
> **最小修复（留待第 2 步/提交前，本轮不擅自改题）**：删除 `test_public_reproduction.py` docstring 第 3-4 行的"修复前/修复后"两句；`assert` 消息 `加权方差应以加权均值为中心`（被 metadata 用作 `required_output_patterns`）可保留，但它本身也偏强，建议在报告中如实标注 002 为 D1。

### 5.3 敏感信息
- `.env.local` 含 `ANTHROPIC_AUTH_TOKEN`（长度 15，非 `sk-` 前缀）。已被 `.gitignore` 忽略，但**若整包 zip 提交会连同泄漏**——须在提交前排除。

---

## 6. Agent Patch 能否干净应用到当前 Base

| Patch | 命令 | 结果 |
|---|---|---|
| 001 agent | `patch -p1 --dry-run -d skfolio_001/task/repo < agent_run/patch.applyable.diff` | ✅ exit=0 |
| 002 agent | `patch -p1 --dry-run -d skfolio_002/task/repo < agent_run/patch.applyable.diff` | ✅ exit=0 |
| 002 gold  | `patch -p1 --dry-run -d skfolio_002/task/repo < grader/gold.patch` | ✅ exit=0 |

**002 Agent Patch 内容核实**：只把 `variance` 改为加权均值中心，**未触碰 `semi_variance`**（gold.patch 同时改了两处）。故 002 Agent Patch 会：公开测试 PASS、隐藏 target/regression PASS，但**隐藏"completeness"测试（semi_variance）FAIL**——与 `results/skfolio_002.json` 的 `final=FAIL` 及盲测记录一致。这是设计预期的"部分通过"。

---

## 7. Validator 与负向自测可运行性（本轮先只做静态确认，完整跑在第 3 步）

- ✅ `validate_case.py` / `negative_selftest.py` / `_common.py` `py_compile` 通过。
- ✅ Runner 环境 `.envs/_runner/bin/python` 存在且含 `pyyaml 6.0.3`。
- ✅ Case 环境 `.envs/skfolio/bin/python`（→ python3.12）存在。
- ✅ Validator 逻辑与仓库无 git 依赖（临时 git init 于副本），不污染 Base。

---

## 8. 一致性 / 完整性问题（供收敛）

| # | 问题 | 影响 | 最小修复 |
|---|---|---|---|
| A | 002 `grader_tree` 校验和过期（gold.patch 14:59:57 晚于 checksums.json 14:59:53 加入） | 校验和不可信 | 清理后重算 checksums.json |
| B | 001 无 `checksums.json`（002 有） | 两 Case 冻结方式不对称 | 为 001 也生成 checksums（可选，统一即可） |
| C | agent_run 不对称：001 有 patch.diff+prompt.md+trajectory.md；002 只有 patch.applyable.diff | 002 缺盲测轨迹/prompt 存证 | 补齐或在报告中说明 002 轨迹见 `盲测判分记录.md` |
| D | grader 产物不对称：001 只有 reference.patch；002 有 gold.patch+reference.patch | 术语/命名不统一 | 统一"reference vs gold"命名 |
| E | 002 隐藏测试与 metadata 注释称 `semi_variance` 为 **anti-hack** | 措辞不准（它测的是"同源函数完整性"，非防作弊） | 改称 completeness / related-behavior test（仅文档措辞，不改断言） |
| F | 002 `domain_necessity: D2` | 因 5.2 泄漏，实际只需 D1 | 提交前改为 D1 并在报告说明 |

> 说明：A/B 属"重算校验信息"，在第 2 步清理后处理；E/F 属"题面措辞与标签"，按本轮"不重新设计题目"原则**不擅自改**，列入 `final_delivery_plan.md` 的"提交前必修"。

---

## 9. 本轮不做（遵守禁止事项）
未新增 Case；未开发 `run_agent.py`/`grade_run.py`/Adapter；未调用 API；未 Docker 化；未重构目录；未重新设计题目。审计阶段**未修改任何文件**。
