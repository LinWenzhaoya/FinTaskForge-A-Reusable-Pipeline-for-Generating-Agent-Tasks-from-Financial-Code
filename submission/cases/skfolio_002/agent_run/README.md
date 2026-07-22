# agent_run/

`patch.applyable.diff` 即正式盲测 run 03(Claude Opus 4.8,隔离环境)提取的 Agent 修复,
与 `official_run/agent.patch` 逐字一致(sha256 前16位 `26830fed40bd54bb`)。
`metadata.yaml` 的 `validation.patch_file` 指向本文件,故 `validate_case.py cases/skfolio_002`
复现的即正式 run 03 的 6/7 结果。完整交互记录见提交包 `official_run/`。
