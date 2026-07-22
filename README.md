# FinTaskForge — 从金融代码材料生成 Agent 任务的可复用造题管线

从真实金融开源库 **skfolio** 的「缺陷 → 官方修复 → 测试」链条中，构造有明确行为 Oracle、有区分度的代码修复任务，并用最强 Agent（**Claude Opus 4.8**）在隔离环境中正式盲测。

## 一句话结论

主案例 `skfolio_002`（加权方差 `sample_weight` 缺陷）：Opus 4.8 在无答案泄漏的隔离环境从零解题，正确修复了显式的 `variance` 问题（Public + Target + Regression 通过），但未同步修正同源 `semi_variance`（Completeness FAIL），最终 **6/7** —— 证明任务能区分「局部修复」与「完整修复」。

## 从哪里读起

| 想看什么 | 去哪 |
|---|---|
| **提交答卷（推荐入口）** | [`submission/README.md`](submission/README.md) |
| **主报告**（材料→造题管线→主案例→正式实测→分析→规模化→局限） | [`submission/report.md`](submission/report.md) |
| **正式盲测完整记录**（原始 stream / 轨迹 / patch / 评分） | [`submission/official_run/`](submission/official_run/) |
| **复现步骤** | [`submission/docs/reproduction.md`](submission/docs/reproduction.md) |
| **主案例（任务 + 隐藏测试 + 官方答案）** | [`cases/skfolio_002/`](cases/skfolio_002/) |
| **通用验收 Runner 与负向自测** | [`pipeline/`](pipeline/) |

## 仓库结构

```text
financial-benchmark/
├── submission/       ★ 收敛后的提交包(README/report/official_run/docs + 精简 cases/pipeline)
├── cases/            两道 Case(skfolio_001 附录 / skfolio_002 主案例): task/grader/metadata/checksums
├── pipeline/         validate_case.py(冻结 v0.2) / negative_selftest.py(6/6) / freeze_checksums.py
├── runs/             正式盲测 run 03(有效) + 两次基础设施无效运行(留证)
├── environments/     环境定义(Dockerfile / requirements)
├── docs/             造题管线设计与各阶段审计/交付文档
└── templates/        造题模板
```

## 说明

- 本仓库**不含**任何 API 密钥、虚拟环境或缓存（见 `.gitignore`）。复现需自建 Python 3.12 环境，见复现说明。
- 正式实验只认定 run 03；此前两次运行因编排问题被判无效，仅作留证，不计入正式结果。
- 隔离为独立 workspace + 上下文隔离，**非 OS 级文件隔离**；禁网为 Prompt/工具层约束。详见 [`submission/docs/limitations.md`](submission/docs/limitations.md)。
