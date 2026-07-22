# 复现说明

> 所有命令在解压后的 `submission/` 目录内执行。`<PROJECT_ROOT>` = 解压后的 `submission/`。
> **原则：绝不在提交的冻结 Base 上直接改动**——所有打补丁/注入测试都在 `/tmp` 临时副本中进行。

## 0. 环境要求

- **Python 3.12**（skfolio 快照要求；cvxpy 对依赖版本敏感）。
- 联网仅用于 `pip install`（评测本身不需要联网）。
- 首次装依赖（cvxpy/scipy/scikit-learn 等）**耗时数分钟**，属正常。

## 1. 创建环境（按 metadata 预期位置，无需修改 metadata）

两题 `metadata.yaml` 的 `environment.python` 均指向 `.envs/skfolio/bin/python`；负向自测另用 `.envs/_runner/bin/python`。在 `<PROJECT_ROOT>` 内创建二者：

```bash
cd <PROJECT_ROOT>
# Case 环境：skfolio 依赖 + pytest（测试运行器）+ pyyaml（Runner 需要）
python3.12 -m venv .envs/skfolio
./.envs/skfolio/bin/pip install -U pip setuptools wheel
./.envs/skfolio/bin/pip install -r cases/skfolio_002/task/requirements-pinned.txt pytest pyyaml
# Runner 环境：仅 pyyaml
python3.12 -m venv .envs/_runner
./.envs/_runner/bin/pip install -q pyyaml
```

> `.envs/` 属本地环境，不随提交包分发；上面是评委本地重建步骤。

## 2. 主案例验收（正式 run 03 的 patch，预期 6/7）

`cases/skfolio_002/agent_run/patch.applyable.diff` 即正式 run 03 提取的 Agent 修复（= `official_run/agent.patch`）。直接跑通用 Runner：

```bash
cd <PROJECT_ROOT>
./.envs/_runner/bin/python pipeline/validate_case.py cases/skfolio_002
# 预期：FINAL RESULT: FAIL (6/7) —— 唯一失败为 Hidden tests(completeness)
# 结果写入 results/skfolio_002.json
```

Runner 内部已自动：复制 `task/repo` 到临时目录、安装、baseline 复现校验、应用 patch、跑公开+隐藏测试——**不触碰提交目录里的 Base**。

## 3. 负向自测（评分器不误判，预期 6/6）

```bash
cd <PROJECT_ROOT>
./.envs/_runner/bin/python pipeline/negative_selftest.py
# 预期：负向自测 6/6 符合预期
```

## 4. 手动分步复现（可选，全部在 /tmp 临时副本中，绝不改提交 Base）

### 4.1 先把 Base 复制到临时目录
```bash
cp -R <PROJECT_ROOT>/cases/skfolio_002/task/repo /tmp/skfolio_002_eval
cd /tmp/skfolio_002_eval
<PROJECT_ROOT>/.envs/skfolio/bin/pip install -e . --no-deps -q
```

### 4.2 Base 复现（应观察到缺陷）
```bash
cd /tmp/skfolio_002_eval
<PROJECT_ROOT>/.envs/skfolio/bin/python -m pytest tests/test_public_reproduction.py -q
# 预期：FAIL，断言 "weighted variance result mismatch"
```

### 4.3 Gold 验证（官方修复，预期全 PASS）
```bash
rm -rf /tmp/skfolio_002_gold && cp -R <PROJECT_ROOT>/cases/skfolio_002/task/repo /tmp/skfolio_002_gold
cd /tmp/skfolio_002_gold
git apply <PROJECT_ROOT>/cases/skfolio_002/grader/gold.patch
cp <PROJECT_ROOT>/cases/skfolio_002/grader/hidden_tests/test_hidden_regression.py tests/
<PROJECT_ROOT>/.envs/skfolio/bin/pip install -e . --no-deps -q
<PROJECT_ROOT>/.envs/skfolio/bin/python -m pytest tests/test_public_reproduction.py tests/test_hidden_regression.py -q
# 预期：全部 PASS（Gold 同时修 variance 与 semi_variance）
```

### 4.4 正式 Agent Patch 三项拆分（预期 target PASS / completeness FAIL / regression PASS）
```bash
rm -rf /tmp/skfolio_002_agent && cp -R <PROJECT_ROOT>/cases/skfolio_002/task/repo /tmp/skfolio_002_agent
cd /tmp/skfolio_002_agent
git apply <PROJECT_ROOT>/official_run/agent.patch
cp <PROJECT_ROOT>/cases/skfolio_002/grader/hidden_tests/test_hidden_regression.py tests/
<PROJECT_ROOT>/.envs/skfolio/bin/pip install -e . --no-deps -q
<PROJECT_ROOT>/.envs/skfolio/bin/python -m pytest tests/test_hidden_regression.py -v -p no:cacheprovider
# 预期：
#   test_target_...        PASSED
#   test_completeness_...  FAILED   ← 漏改 semi_variance
#   test_regression_...    PASSED
```

## 5. 预期结果汇总

| 步骤 | 预期 |
|---|---|
| Base 复现 | 公开测试 FAIL（`weighted variance result mismatch`） |
| Gold 验证 | 全 PASS（行为 Oracle 7/7） |
| 主案例 Runner / 正式 Agent Patch | 6/7；Target·Regression PASS，**Completeness FAIL** |
| 负向自测 | 6/6 |

> 校验和：`./.envs/_runner/bin/python pipeline/freeze_checksums.py` 重算 task/grader/agent_patch 三段 sha256，应与各 `checksums.json` 一致（幂等，范围排除缓存/环境/日志/metadata）。
