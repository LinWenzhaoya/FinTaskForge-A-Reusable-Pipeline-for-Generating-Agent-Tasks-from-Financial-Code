# 被测 Agent 解题轨迹(摘要)

> 完整报告见本文件;patch 见 patch.diff;判分见 ../盲测判分记录.md。

## 解题步骤(被测 Agent 自主完成,38 次工具调用,约 11 分钟)

1. 读 TASK.md / README.md,理解任务
2. 激活 venv,`pip install -e repo --no-deps`,确认 import 指向 task/repo
3. 运行 `tests/test_public_reproduction.py` → 复现异常(ValueError at `_mean_risk.py:1084`)
4. 沿 traceback 阅读 `_mean_risk.py` 的 `MAXIMIZE_RATIO` 分支
5. 阅读 `_maximum_diversification.py`,发现它是 `MeanRisk` 子类,通过 `overwrite_expected_return` 把 ratio 分子从 mu 换成"加权波动率"
6. **关键推理**:防呆检查无条件用 mu 判断,但 MaximumDiversification 的分子已不是 mu → 检查前提不成立却仍执行
7. **额外佐证(超预期)**:发现同分支 843-864 行已对 `overwrite_expected_return is not None` 做过特殊处理(VARIANCE 场景),据此论证"这条 ValueError 检查漏判是疏忽性 bug,非设计意图"
8. 实施修复:检查条件加 `self.overwrite_expected_return is None`
9. 自我验证:重跑公开测试通过;还自主找到并运行原仓库 `test_max_ratio_with_neg_f1`,确认标准夏普场景防呆仍生效(自发的防投机自查)

## 根因定位(被测 Agent 结论,与官方一致)

`MAXIMIZE_RATIO` 分支的防呆检查错误假设 ratio 分子恒为资产历史平均收益 mu;未考虑 `overwrite_expected_return` 会替换分子语义。MaximumDiversification 的分子是加权波动率(与历史收益正负无关),故全负收益时该检查误触发。

## 修复方式

`_mean_risk.py` 防呆检查加条件 `self.overwrite_expected_return is None`,把检查限定在"分子确实是 mu"的经典场景。最小改动,未删检查、未吞异常、未硬编码、未改测试。

## 与官方 reference patch 的关系

思路完全一致(官方 commit c2cc1ad 亦为加 `overwrite_expected_return is None` 条件)。非逐字要求,行为等价。被测 Agent 是自主推理得出,非从 git 历史抄取(prompt 明确禁止联网、且 task/ 无 .git)。
