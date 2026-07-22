# 无效运行 (invalid_infrastructure_run)
- run_id: skfolio_002_official_20260722_02
- reason: killed_by_orchestrator_gate_false_positive (/tmp vs /private/tmp symlink)
- 模型工作量: init 事件 1 条, assistant 事件 0, tool 调用 0 → 未开始解题
- 不计正式尝试: launch.sh v2 本身正确(cwd 实际正确, /tmp 是 /private/tmp 的符号链接);
  是我的内嵌门禁做了朴素字符串比较、误判并 kill。属编排错误, 非模型解题失败。
