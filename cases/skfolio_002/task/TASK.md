# 任务:修复一个风险度量的计算错误

## 背景

本库的风险度量模块 `skfolio.measures` 提供了 `variance`(方差)等函数,支持传入 `sample_weight` 对不同观测样本加权(常用于对近期数据赋予更高权重)。

某用户报告:当传入**非均匀** `sample_weight` 时,`variance` 的计算结果不正确。以一组带非均匀权重的收益率为例,`variance(returns, sample_weight=w, biased=True)` 返回的数值,与按加权方差参考定义独立计算出的结果**不一致**。

公开测试 `tests/test_public_reproduction.py` 复现了这一差异。

## 为什么这被认为是一个 bug

带 `sample_weight` 的方差应当与加权方差的标准参考定义一致。当前实现在权重非均匀时的返回值偏离了该参考定义。

用户期望的行为是:`variance(returns, sample_weight=w, biased=True)` 的结果等于加权方差参考定义给出的数值(见公开测试中独立计算的 `expected`)。

## 你的任务

1. 复现问题(运行 `tests/test_public_reproduction.py`)。
2. 定位根本原因。
3. 实现最小的、针对根因的修复。
4. 确保修复不破坏:无权重时的方差行为、以及模块内其他同类度量的一致性。
5. 运行测试,报告改动的文件和运行的测试。

请阅读 `README.md` 了解环境搭建、测试运行方式和提交约束。
