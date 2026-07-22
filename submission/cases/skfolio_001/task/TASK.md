# 任务:修复一个组合优化模型的异常

## 背景

某用户在使用本库的 **最大分散化组合模型**(`MaximumDiversification`,位于 `skfolio.optimization`)时报告了一个问题:

当输入的所有资产在样本期内的历史平均收益都为负时,调用 `.fit(X)` 会抛出如下异常:

```
ValueError: Cannot optimize for Maximum Ratio with your current constraints and input.
This is because your assets' expected returns are all under-performing your risk-free rate 0.00%.
```

## 为什么这被认为是一个 bug

按照该模型的设计意图,**最大分散化组合在上述情形下应当能够正常求解并返回一组有效权重**——它不应该因为"资产历史平均收益为负"而拒绝求解。

用户期望的行为是:`MaximumDiversification().fit(X)` 成功返回,`model.weights_` 是一组和为 1 的有效权重。

## 你的任务

1. 在提供的仓库中**复现**该问题(可运行 `tests/test_public_reproduction.py`)。
2. **定位**问题的根本原因。
3. 实现**最小的、针对根因的**修复。
4. 确保修复**不会破坏**其他优化模型在同类情形下原本合理的行为。
5. 运行测试,报告你改动的文件和运行的测试。

请阅读 `README.md` 了解环境搭建、测试运行方式和提交约束。
