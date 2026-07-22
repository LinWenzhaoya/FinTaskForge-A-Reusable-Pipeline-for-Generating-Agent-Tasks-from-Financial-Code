# 无效运行 (invalid_infrastructure_run)

- run_id: skfolio_002_official_20260722_01
- 判定: **invalid_infrastructure_run**
- reason: incorrect_agent_cwd_and_benchmark_path_exposure
- 不计入唯一正式 Agent 尝试(问题发生在模型获得正确任务之前,属编排错误,非解题失败)

## 致命证据
init 事件 cwd = `financial-benchmark/runs/skfolio_002_official_20260722_01`
(预期应为 `/tmp/agent_ws_.../workspace`)

launch.sh 定义了 WS 但调用 claude 前未 `cd "$WS"`, 也未设子进程 cwd。
后果: Agent 启动在运行记录目录(无 TASK.md/README.md), 且身处 benchmark 内部,
可经 ../../ 触达 cases/grader/旧记录 → 盲测隔离失效。

## 保全
records/claude_stream.raw.jsonl (117 行) / claude_stderr.log / started_at / finished_at / exit_code
launch.sh(含 bug 的原始启动脚本) 一并保留。
