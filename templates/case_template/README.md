# Case 模板使用说明 —— 可复用 vs 需专家逐题填

本模板从 `cases/skfolio_001` 抽象而来。用于把一个"真实 Issue→Fix→Test 链条"标准化成一道可一键验收的 Agent 题。

## 目录约定

```
case_template/
├── metadata.yaml          # 元数据(每题填)
├── task/                  # 给被测 Agent(无 .git / 无答案线索)
│   ├── TASK.md            # 题面: 只描述现象+期望, 不给根因
│   ├── README.md          # 环境/运行/提交约束(多数可复用)
│   ├── requirements-pinned.txt   # 同期依赖(每题按仓库确定)
│   └── repo/              # 修复前代码快照 + 公开复现测试
├── grader/
│   ├── hidden_tests/      # 至少 target + anti-hack + regression 三类
│   └── reference.patch    # 官方修复(参考, 不进 task/)
└── agent_run/             # 盲测产物(patch.applyable.diff / prompt / trajectory)
```

> 验收不再靠每 case 一份 shell,而是统一由 `pipeline/validate_case.py` 配置驱动:
> ```bash
> python pipeline/validate_case.py cases/<instance_id>
> ```
> Runner 读 `metadata.yaml` 的 `validation` 段完成全流程,输出 `results/<instance_id>.json`。

## 哪些可以跨 Case 复用(低边际成本)

| 项 | 复用程度 |
|---|---|
| `pipeline/validate_case.py` | **完全复用且零改动**——配置驱动,新题不许改 Runner(可复用性的判据) |
| 目录结构 & metadata schema | 完全复用 |
| README.md 骨架(环境搭建/提交约束) | 大部分复用,仅 python 版本、依赖文件、特殊环境注记按仓库微调 |
| task/repo 与 patch 分离的封装方式 | 完全复用 |
| 隐藏测试的三类框架(target/anti-hack/regression) | 结构复用,具体断言每题重写 |
| **同一仓库的环境**(venv/依赖pin) | **同仓库第二题直接复用**——这是"可规模化"最直接的证据 |

## 哪些必须由领域专家逐题填(不可自动化)

| 项 | 为什么需要专家 |
|---|---|
| 选哪个 Issue / 是否真依赖金融知识(domain_necessity) | 判断 bug 是纯工程还是需领域理解,决定入库价值 |
| TASK.md 题面措辞 | 给多少线索、是否点破根因,直接决定难度与公平性 |
| 隐藏测试具体断言(尤其 anti-hack) | 要预判"投机修复"长什么样,针对性设防——最考专家 |
| 环境陷阱判断 | 该仓库是否需 pin 同期依赖、有无 API 漂移 |
| 难度定位 | 诚实标注,不夸大 |

## 从同一仓库增加第二个 Case 时,预计省掉的成本

1. **环境恢复**(§最重的一步):skfolio 的 Python 3.12 + 同期依赖 pin 已确定,第二题**直接复用 venv,零成本**。
2. **仓库结构熟悉**:调用关系、测试目录布局已知。
3. **封装流程 & 验收脚本**:`validate_case.sh` 直接拷用。
4. 仍需逐题做的:选 Issue、验证 base-fail/gold-pass、写题面、写隐藏测试。

> 这正是 SWE-bench "三层镜像"边际成本下降的道理:**同仓库多 case 摊薄环境层**。第二题若能按同模板跑通,即用证据证明"管线可复用、成本确实下降"。
