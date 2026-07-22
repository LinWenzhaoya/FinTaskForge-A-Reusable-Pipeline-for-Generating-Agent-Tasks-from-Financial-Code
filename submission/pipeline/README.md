# pipeline/ — 造题与验收核心工具

三个文件，配置驱动，逻辑不含任何具体仓库/模型/文件名。

| 文件 | 作用 |
|---|---|
| `validate_case.py` | **通用验收 Runner（冻结 v0.2）**。读 `cases/<id>/metadata.yaml` 的 `validation` 段驱动判分：环境安装 → baseline 三重校验（返回码 + 必现/禁现输出特征）→ git 识别 patch 改动文件并校验白名单/黑名单 → 应用 patch → 公开测试 → 注入隐藏测试 → 输出可审计 `results/<id>.json`。全程在临时副本上操作，不污染 Base。 |
| `negative_selftest.py` | **负向自测**。复制 skfolio_001 为临时畸变 case，注入 6 种缺陷（安装失败/公开测试缺失/删测试/白名单越界/非测试注入/metadata 缺失），断言 Runner "该失败时确实失败"。当前 **6/6**。 |
| `freeze_checksums.py` | **标准资产冻结**。对两题统一计算 `task_tree_sha256 / grader_tree_sha256 / agent_patch_sha256`（`case-freeze-v1`），写入各 `cases/<id>/checksums.json`。范围排除 results/缓存/.envs/备份/metadata.yaml；幂等。 |
| `_common.py` | 共享工具（sha256_tree/sha256_file、run、git_apply 等）。 |

## 用法

```bash
python pipeline/validate_case.py cases/skfolio_002   # 单 case 验收
python pipeline/negative_selftest.py                 # 评分器负向自测
python pipeline/freeze_checksums.py                  # 重算并冻结两题校验和
```

> `validate_case.py` 通过 `metadata.yaml` 的 `environment.python` 指定被测 Case 用的解释器（与 Runner 自身环境分离）。复现时请把该字段指向一个装齐 skfolio 依赖的 Python，或参见 `docs/reproduction.md` 的手动最小复现。

## 未包含的实验性代码

原项目中的 Agent Harness / Adapter / 多模型调度（`adapters/`、`build_case.py`、`config/agents.yaml` 等）属**未完成的平台化草稿**，不是本笔试主线，未纳入提交包。正式 Agent 盲测通过成熟的 Claude Code CLI 无头模式完成，编排脚本与完整记录见 `official_run/`。
