# Case 验收记录 002 — skfolio #196 (最大分散化负预期收益)

## 结论:可用(通过完整 base-fail → fix-pass 验证)

## Case 概况

| 项 | 内容 |
|---|---|
| 仓库 | skfolio/skfolio (组合优化, 基于 scikit-learn) |
| base commit(修复前) | 5d673e7 |
| fix commit(修复后) | c2cc1ad `fix: maximum diversification with negative expected returns (#197)` |
| 关联 Issue | #196 |
| 改动文件 | src/skfolio/optimization/convex/_mean_risk.py (仅源码, 未附新测试) |

## Bug 本质(继承 + 金融语义双重)

`MaximumDiversification` 继承 `MeanRisk`,复用其 `MAXIMIZE_RATIO`(最大化夏普比率)分支。该分支有一段"防呆检查":若所有资产预期收益都 ≤ 无风险利率,则抛 ValueError(因为最大化夏普比率此时无意义)。

**但最大分散化根本不以预期收益为目标**——它通过 `overwrite_expected_return` 把 mu 覆盖成资产波动率,目标是最大化"加权平均波动率/组合波动率"。所以这个基于预期收益的防呆检查不应对它生效。

修复:检查加上 `overwrite_expected_return is None` 条件,使得当子类覆盖了预期收益时跳过该检查。

**Agent 要理解:** ①类继承关系(子类复用父类的哪段逻辑) ②最大分散化 vs 夏普比率的目标函数差异——纯 coding 背景难解,必须懂金融含义。

## 验证结果(可执行 oracle)

构造最小复现:4 个资产、300 天、全部负漂移收益(预期收益全 < 0 < 无风险利率),跑 `MaximumDiversification().fit(X)`。

| 版本 | 行为 |
|---|---|
| BASE(修复前) | 抛 `ValueError: Cannot optimize for Maximum Ratio...` ❌ |
| FIX(修复后) | 正常求解, 权重 [0.42, 0.21, 0.24, 0.13], sum=1.0 ✅ |

Oracle 定义:**MaximumDiversification 在全负预期收益输入下应成功求解、不抛错。** (自构造, 属 GPT探讨5 允许的第5类 oracle)

## 验收维度打分

| 维度 | 结论 |
|---|---|
| 专业性(金融语义) | 高 —— 最大分散化目标函数 + 类继承 |
| GT 可靠性 | 高 —— 维护者合并的修复 |
| Oracle 清晰度 | 中高 —— 需自构造(fix未附测试), 但判据明确(抛错/求解) |
| 离线性 | 高 —— 纯计算, 无网络 |
| 环境健康度 | 中 —— 见下 |
| Agentic 难度 | 高 —— 需定位继承链 + 理解金融目标 |
| 最终判定 | **可用** |

## 环境备注(第二条筛选规则的来源)

skfolio 是 2025 活跃库,但 pyproject 只写依赖**下限**(`cvxpy-base>=1.5.0`)。直接 `pip install -e .` 装了**最新**依赖(cvxpy 1.9.2 / pandas 3.0 / numpy 2.5),而 2025-11 的 commit 源码针对当时 cvxpy(cp.trace 是类)编写,新版把 cp.trace 改成函数 → 旧 commit 的 typing.py 崩溃(`TypeError: unsupported operand |`)。

**解法:** 手动降级到同期版本 cvxpy-base==1.6.0 / numpy==1.26.4 / pandas==2.2.3 / scipy==1.15.2 / scikit-learn==1.6.1 → import 通过 → 验证成功。全部有 py3.12 wheel,无编译,约1分钟。

## 提炼的第二条【环境筛选规则】

> 光看"库活跃/有 pyproject.toml"不够。真正的门槛是**能否重建 commit 同期的可运行环境**:
> - 仓库只写依赖下限(无 lockfile)时,checkout 历史 commit 后必须手动 pin 同期依赖版本,否则最新依赖会破坏旧源码;
> - **优先带 `uv.lock` / `poetry.lock` / `requirements.txt` 精确版本的仓库**(如 exchange_calendars),它们直接给出同期依赖,边际成本最低。

## 对照:001(empyrical)vs 002(skfolio)

| | empyrical #60 | skfolio #196 |
|---|---|---|
| 库年代 | 2019(老) | 2025(新) |
| 环境问题 | 旧依赖无wheel、要编译、缺setuptools | 无lockfile、默认装了过新依赖 |
| 能否解决 | 否(编译连锁失败) | 是(降级同期版本, 有wheel) |
| 结论 | 淘汰 | 可用 |
