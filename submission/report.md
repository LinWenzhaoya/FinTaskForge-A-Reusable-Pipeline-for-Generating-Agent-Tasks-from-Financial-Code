# 从真实金融代码材料构造可验证、有区分度的 Agent 任务
### —— 一条可复用造题管线原型，及最强 Agent（Claude Opus 4.8）的正式盲测

> 主案例：`skfolio_002`（加权方差 `sample_weight` 缺陷修复）
> 附录案例：`skfolio_001`（同仓库复用验证）
> 正式实测：Claude Opus 4.8，隔离环境，从零解题，最终 **6/7**

---

## 1. 任务理解

笔试要求可拆成三个目标：

1. 从**高质量专业材料**中寻找可靠任务；
2. 基于材料构造**有标准答案、对 Agent 有一定难度**的题；
3. 用**最强 Agent** 实测并提交完整交互记录。

我没有"手工发明一道 bug 题"，而是把它理解为一个**造题方法论**问题：目标是从专业材料出发，构造一条**可复用、可进一步规模化**的造题流程——先用一道完整跑通的题证明流程可行，再用同仓库第二道题证明环境与验收组件可复用。因此本报告的主角是**造题管线**，两道题是它的产物与验证。

---

## 2. 专业材料选择：skfolio 风险度量代码

**skfolio** 是一个开源的投资组合优化库（scikit-learn 风格 API，基于 cvxpy）。但选它作材料的**关键不在"库有多好"，而在它天然提供了可靠的"输入—答案对"**：

- **有"修复前代码 → 官方修复 → 回归测试"的完整链条**：每个真实 bug 都带修复前版本（Base）、官方修复 commit（Fix）、以及验证修复的测试。这三者恰好构成造题所需的"缺陷输入 + 标准答案 + 可判定 Oracle"。
- **答案可执行、可判定**：由测试与数学定义验证，而非主观判断；
- **领域明确**：投资组合优化、风险度量属金融工程核心。

主案例材料具体是 `skfolio.measures` 模块的**加权方差**缺陷及其官方修复（commit `e7e60cb`, "fix(measures): variance with sample_weight"）：

- **Base（修复前）**：`variance(returns, sample_weight=w)` 计算加权方差时，离差中心错误地用了**无权重算术均值** `mean(returns)`，而非**加权均值**。
- **数学定义（Oracle 依据）**：加权方差 = Σᵢ wᵢ(rᵢ − r̄_w)²，其中 r̄_w = Σᵢ wᵢrᵢ。权重非均匀时无权重均值 ≠ 加权均值，结果即偏离定义。
- **官方修复**：将 `variance` 与**同源的** `semi_variance` 两处的默认中心都改为加权均值。

---

## 3. 可复用造题管线

```text
真实专业材料 (skfolio 仓库 + 历史修复)
   │
   ├─(1) 候选缺陷筛选     从 Issue/Fix commit 中挑选有领域价值、可复现、Oracle 明确的
   ├─(2) 修复前 Base 恢复  git checkout 到 base_commit，作为被测 Base
   ├─(3) Gold Oracle 提取  官方 fix patch 作参考答案（不进 Agent 可见范围）
   ├─(4) 公开测试构造      复现用户报告现象的最小测试（Base fail）
   ├─(5) 隐藏测试构造      target / completeness / regression 三类行为 Oracle
   ├─(6) 去泄漏           题面/公开测试中删除根因与修法，中性化断言消息
   ├─(7) Base fail / Gold pass 门禁   Validator 验证 Base 复现缺陷、Gold 修复通过
   ├─(8) 强 Agent 盲测     隔离环境、去泄漏题面、最强模型从零解题
   └─(9) 独立评分与轨迹留存 从冻结 Base 独立套 patch 评分，保存完整交互记录
```

**每一步的自动化程度与专家参与点**（诚实标注，避免夸大为"全自动"）：

| 环节 | 自动化程度 | 说明 |
|---|---|---|
| (1) Commit/Issue 候选收集 | 可半自动 | 可脚本扫 fix commit，但**领域价值判断需人工** |
| (2) Base 恢复 | 半自动 | git 操作可脚本化 |
| (3) Gold 提取 | 自动 | 直接取 fix commit 的 diff |
| (4)(5) 测试生成 | **人工为主** | 需领域知识设计行为 Oracle |
| (6) 去泄漏扫描 | 半自动 | 关键词扫描 + 人工复核 |
| (7) Base fail/Gold pass 门禁 | 自动 | `validate_case.py` |
| (8) Agent 盲测 | 自动编排 | 隔离 workspace + CLI 无头模式 |
| (9) 独立评分 | 自动 | 复用同一 Validator |

**关键工程资产**（均在 `pipeline/`）：

- `validate_case.py`（冻结 v0.2）：**配置驱动的通用验收 Runner**，逻辑不含任何仓库/模型/文件名。判分链：安装 → baseline 三重校验（返回码+必现/禁现特征）→ git 识别 patch 改动文件（白名单/黑名单）→ 应用 patch → 公开测试 → 注入隐藏测试 → 输出可审计 result.json。
- `negative_selftest.py`：**负向自测**，用 6 种畸变（安装失败/公开测试缺失/删测试/白名单越界/非测试注入/metadata 缺失）验证"Runner 该失败时确实失败"，防假阳性。当前 **6/6**。
- `freeze_checksums.py`：冻结标准资产（task_tree/grader_tree/agent_patch 三段 sha256），两题统一 `case-freeze-v1` 规则。

---

## 4. 主案例设计：skfolio_002

### 4.1 输入材料与题面
交给 Agent 的是修复前 Base 源码快照 + 中性题面。题面（`task/TASK.md`）**只描述现象**：非均匀 `sample_weight` 下 `variance` 结果与加权方差参考定义不一致；不提"加权均值/普通均值/离差中心/具体 mean 调用"。

### 4.2 被隐藏的信息
- 官方 fix commit 与 issue 号（仅在 metadata，不进 task/）；
- Gold Patch（在 grader/，不进 Agent 可见范围）；
- 修法根因（去泄漏：删除公开测试 docstring 里"用加权均值 mean(returns, sample_weight=w)"、TASK 里"离差中心用错了"，并把 assert 消息从"加权方差应以加权均值为中心"改为中性的 `weighted variance result mismatch`）。

### 4.3 标准答案 = 行为 Oracle（不要求代码逐字一致）
标准答案由三部分共同定义：官方 Patch + 加权风险度量数学定义 + Gold Patch 通过全部公开/隐藏测试（**Gold 验证 7/7**）。评分看**行为**是否满足 Oracle，而非 diff 是否与官方逐字相同。

### 4.4 三类测试
```text
Target       : 加权 variance 与参考定义一致      —— 显式报告的问题是否修复
Completeness : 同源 semi_variance 采用一致加权中心 —— 同源逻辑是否一并处理
Regression   : 无 sample_weight 时 variance 不变   —— 原行为是否保持
```
其中 completeness 是"关联行为完整性"测试（检验修复是否推广到同源函数），**不是** anti-hack/防作弊断言。

---

## 5. 正式 Agent 实测（run 03）

> 注：本报告只认定 run 03 为正式实验。正式运行前有两次基础设施校验因编排问题（工作目录配置、路径符号链接归一）被判**无效运行**，模型未获得有效任务或隔离不成立，不计入正式结果（详见 `docs/limitations.md`）。

| 维度 | 配置 |
|---|---|
| 模型 | `claude-opus-4-8[1m]`（requested = resolved） |
| 运行时 | Claude Code CLI 无头模式（`-p`，stream-json） |
| 上下文 | 全新会话，空 `CLAUDE_CONFIG_DIR`（不加载任何全局记忆），白名单环境变量 |
| 工作目录 | 独立临时 workspace（`/tmp`），只含 `task/*`，cwd 门禁 realpath 校验通过 |
| 可见材料 | TASK.md / README.md / requirements-pinned.txt / 修复前 repo。**未提供** grader、Gold、隐藏测试、旧轨迹、issue/commit、任何 semi_variance 提示 |
| 工具 | 对 Read/Edit/Write/Bash/Glob/Grep 自动授权；显式禁用 WebSearch/WebFetch/Task |
| 时长/轮次 | ~1h55m，67 轮，exit=0，result=success |

**Agent 执行过程**（源自 `official_run/trajectory.md`，派生自未修改的 raw stream）：自行按 README 建独立 venv 并装依赖 → 运行公开测试复现问题 → 定位 `variance` 用无权重均值作中心 → 实施**通用**修复（非硬编码）→ 搜索同模块与下游调用 → 主动跑大量回归测试 → 最终只改一个白名单文件 `src/skfolio/measures/_measures.py`。

**独立评分结果**（从冻结 Base 独立套 patch，`official_run/grader_result.json` + `hidden_split.log`）：

| 评分项 | 结果 |
|---|---|
| Base 复现 | PASS |
| Patch 应用 | PASS |
| 路径约束（仅白名单） | PASS |
| Public | PASS |
| Hidden Target | PASS |
| **Hidden Completeness** | **FAIL** |
| Hidden Regression | PASS |
| **总结果** | **6/7** |

---

## 6. 结果分析

**准确结论**：

> Claude Opus 4.8 在无答案泄漏的隔离环境中，从零完成环境搭建、问题复现、根因定位与目标修复。其 Patch 通过公开测试、目标隐藏测试和无权重回归测试，但未同步修正同模块内具有相同加权中心问题的 `semi_variance`，最终为 6/7。

- **核心正确性通过**：Agent 正确修复了用户**显式报告**的 `variance` 问题（Public + Hidden Target + Regression 全过）。**不能说它"答错"或"不会算加权方差"**。
- **关联行为完整性未通过**：它没有把修复扩展到官方 fix 中同源的 `semi_variance`。
- **题目有区分度**：公开测试 ≠ 完整行为 Oracle。若只看公开测试，此 Patch 会被判成功；加入 completeness 测试后，才能区分**局部修复**与**完整修复**。而且这不是"跑绿公开测试就收工"的粗心——Agent 花了大量时间检查调用方与回归模块，**已识别到关联的 `semi_variance` 逻辑，但将其判断为任务范围之外**而未改。因此失败点是**问题边界判断**，不是执行懒惰。

**completeness Oracle 的边界解释空间（诚实呈现）**：

- *支持隐藏测试合理性*：官方 fix 确实同步改了两处；两处是**完全相同的缺陷模式**（都传 `sample_weight` 却在默认中心调用无权重 `mean`）；TASK 要求"模块内同类度量的一致性"，正式 Prompt 要求"检查相同或高度相关的实现逻辑"。
- *Agent 反驳亦非无理*：用户报告的仅是 `variance`；`semi_variance` 是另一公开 API、公开测试未覆盖、其默认 `min_acceptable_return` 语义可视为独立行为。从"最小修复"角度只改一处并不荒谬。

因此该项被定义为 **completeness（关联行为完整性）测试，而非无争议的核心正确性**。这一诚实定性反而增强了题目的分析价值。

**一个额外的真实发现**：Agent 独立指出，仓库内 12 个 `test_measures` + 3 个 `test_entropy_pooling` 用例的 golden 值是**按 bug 行为硬编码**的、与正确定义数学互斥；它按约束拒绝修改测试并如实上报冲突。这印证了"测试可能固化 bug"，也是我们采用**独立 grader**（不依赖原仓库测试）判分的理由。

---

## 7. 可复用性与规模化

**已有证据（同仓库复用）**：

- `skfolio_001`（MaximumDiversification 负收益，另一代码路径）与 `skfolio_002` 使用**统一 Case 目录结构**（task/grader/agent_run/metadata/checksums）；
- 第二题**复用**第一题的仓库环境（`.envs/skfolio`）、同一 `validate_case.py`（**零修改**）、同一 Base fail/Gold pass 标准、同一评分方式；
- `negative_selftest` 6/6 证明评分器不会轻易误判；
- `freeze_checksums` 统一冻结两题标准资产；
- 第二题的边际成本明显低于第一题（环境与 Runner 已就绪）。

**成熟度定级（诚实）**：

| 级别 | 含义 | 状态 |
|---|---|---|
| L1 单题案例 | 手工构造并验证一道题 | ✅ 已完成 |
| L2 可复用流程 | 相同方法构造多道题 | ✅ 已完成 |
| L3 半自动管线 | 自动发现/封装/门禁 + 人工审核 | 🟡 部分具备 |
| L4 规模化生产 | 跨仓库批量、有质量与成本指标 | ❌ 未完成 |

**结论**：

> 已实现并验证一条面向金融代码材料的**可复用造题管线原型**，具备向规模化生产演进的基础；但候选发现与隐藏测试设计仍依赖领域专家，尚未形成跨仓库、全自动、批量化生产平台。

---

## 8. 局限性与后续工作

- **隔离边界**：run 03 采用独立 workspace + 空 Claude 配置 + 上下文隔离，**非 OS 级文件系统隔离**；禁止联网主要是 Prompt 与工具层限制（Bash 理论上仍可联网），**非强制技术断网**。报告不宣称"Agent 技术上无法访问其他宿主路径"。
- **正式运行耗时较长**：Agent 主动跑了大量 skfolio 回归测试（cvxpy 求解慢），约 1h55m。未来 Harness 应加：总墙钟限制、单测超时、推荐回归范围、超时后可审计的终止状态。本次不重跑，保留真实结果。
- **completeness 边界**：如 §6，属可讨论的完整性判断，非核心正确性。
- **规模化缺口**：候选发现仍以人工为主；隐藏测试设计依赖专家；仅验证同仓库复用；未做跨仓库批量自动生产、难度分层校准、多 Agent 通过率标定。
- **后续工作**：候选 commit 自动扫描与初筛、跨仓库/跨语言适配、批量质量门禁（泄漏扫描/覆盖评分/相似题检测）、规模化成本指标统计。

---

## 附：与笔试要求的对应关系

| 原题要求 | 本交付 |
|---|---|
| 高质量专业材料 | skfolio 风险度量源码、修复前 Base、官方修复 Patch、可执行测试 |
| 基于材料造题 | 回退 Base、隐藏 Patch、去泄漏题面、公开 + 三类隐藏测试 |
| 有标准答案 | 官方 Patch + 数学定义 + Gold 验证 7/7（行为 Oracle） |
| 对 Agent 有难度 | 最强 Opus 4.8 隔离盲测仅 6/7 |
| 最强 Agent 实测 | 隔离的 Claude Opus 4.8 正式 run 03 |
| 完整代码/交互记录 | task、grader、pipeline、agent.patch、raw JSONL、日志、result.json |
