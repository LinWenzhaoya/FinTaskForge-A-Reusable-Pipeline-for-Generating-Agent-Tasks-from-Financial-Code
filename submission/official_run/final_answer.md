All work complete. Here is my report.

---

## 问题根因

`skfolio/measures/_measures.py` 中 `variance()` 在处理**非均匀** `sample_weight` 时，把偏差中心（center）错误地取为**无权重均值**，而不是**加权均值**：

```python
# 原代码 (line 139)
biased_var = sample_weight @ (returns - mean(returns)) ** 2
#                                        ^^^^^^^^^^^^^ 未传 sample_weight → 用了普通算术平均
```

`mean(returns)`（不带权重）走的是 `np.mean(returns)` 分支，返回算术平均 `ū`。而加权方差的参考定义要求围绕**加权均值** `w·r` 中心化：

$$\mathrm{Var}_w = \sum_i w_i\,(r_i - \bar r_w)^2,\quad \bar r_w = \sum_i w_i r_i$$

只要权重非均匀，`w·r ≠ ū`，返回值即偏离参考定义。均匀权重时二者相等，所以此前无人察觉。

## 修改的文件与逻辑

**唯一改动**：`repo/src/skfolio/measures/_measures.py`，`variance()` 的加权分支（第 139 行），把中心从无权重均值改为加权均值：

```python
biased_var = (
    sample_weight @ (returns - mean(returns, sample_weight=sample_weight)) ** 2
)
```

无权重分支（`np.var`）、无偏修正（`n_eff` Kish 有效样本量）均未触碰。

## 为什么该修复正确且一般化

1. **符合参考定义**：与公开测试独立计算的 `expected = Σ w·(r - Σw·r)²` 完全一致。
2. **符合本模块自身约定**：模块内 `correlation()` 用 `np.cov(X, aweights=sample_weight)`，其加权协方差正是围绕加权均值中心化；修复后 `variance` 与 `np.cov(aweights, ddof=0)` 逐位吻合。
3. **模块内一致性**：`third_central_moment`、`fourth_central_moment` 早已用 `mean(returns, sample_weight=...)` 中心化。修复前 `variance` 是唯一一个用无权重均值中心化的中心矩——它才是异类。修复统一了全模块的中心矩定义。
4. **不针对输入硬编码、无 try/except**：只改中心量，对任意 returns/weights 一般成立。
5. **不破坏无权重行为**：所有失败用例都是 `-True-`（非均匀权重）用例；全部 `-False-`（无权重）及 `*_sample_weight`（均匀权重恒等）用例通过。均匀权重下 `w·r = ū`，结果与 `np.var(ddof=0)` 一致（已数值验证）。

## 运行过的测试及结果

- `tests/test_public_reproduction.py` — 修复前 **FAILED**（got=0.000347 vs expected=0.00034475），修复后 **PASSED**。
- `tests/test_measures/` — **170 passed, 12 failed**。
- 回归：`test_portfolio` `test_utils` `test_metrics` **352 passed**（另有若干 `urllib` 超时 ERROR，为离线环境无法下载数据集所致，与本改动无关）。`test_prior/test_distance/test_model_selection` **174 passed, 4 failed**（均在 `test_entropy_pooling.py`）。

## 仍存在的风险 / 未能运行的测试

**关键冲突（必须如实报告）**：有 15 个已存在的用例失败，且**无法通过合规修复消除**：

- `test_measures.py` 12 个：`variance/standard_deviation/skew/kurtosis` 的**加权**（`-True-`）golden 值，是从**有 bug 的旧行为**（无权重中心化）快照出来的。
- `test_entropy_pooling.py` 3 个：`test_mean_correlation_views[TNC/CLARABEL]`、`test_complex_views` 的 `relative_entropy_` golden 值，同样依赖旧的加权方差数值。

这些 golden 值与公开测试要求的正确定义在数学上**互斥**（只要加权均值 ≠ 算术均值，二者不可能同时成立）。因为约束**禁止修改/削弱测试**，我保留了最小的源码修复、未改动任何测试文件；正确的做法应是重新生成这些 golden 值（例如 `variance[1d-True-True]` 应为 `0.0007406331` 而非 `0.0007406478`）。

**非本改动引起的失败**：`test_entropy_pooling.py::test_cvar_variance_views[TNC]` 在**未修复的基线代码上也失败**（TNC 求解器 `Linear search failed`，属既有的求解器波动）。

**未运行/未完成**：依赖联网下载数据集的用例（`test_dataset`、`test_implied_covariance`、部分 metadata-routing）在离线环境下 ERROR，按任务约束未联网，故无法运行——与本修复无关。`semi_variance` 的默认 MAR 仍用无权重 `mean(returns)`（第 180 行），这是独立的设计选择、其 golden 测试通过、且不在本任务范围内，未改动。