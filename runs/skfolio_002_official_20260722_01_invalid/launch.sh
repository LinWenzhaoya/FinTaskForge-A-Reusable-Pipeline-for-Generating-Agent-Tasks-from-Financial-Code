#!/bin/bash
# 正式盲测启动器 —— 一次性运行, 严格按 GPT审核3 的隔离与证据要求。
# 不预建环境: Agent 自行按 README 建 venv。仅采集原始证据流。
set -u

RUN_ID=skfolio_002_official_20260722_01
BENCH=<PROJECT_ROOT>
RUNDIR=$BENCH/runs/$RUN_ID
WS=/tmp/agent_ws_$RUN_ID/workspace
CFG=/tmp/agent_ws_$RUN_ID/empty_claude_config      # 空配置目录 -> 不加载全局 CLAUDE.md
mkdir -p "$CFG"

REQUESTED_MODEL='claude-opus-4-8[1m]'
CLAUDE_BIN=<HOME>/.local/bin/claude

# 认证/代理从 .env.local 读取(不硬编码 token 进脚本)
set -a; source "$BENCH/.env.local"; set +a

STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "$STARTED_AT" > "$RUNDIR/records/started_at.txt"

# 白名单环境: env -i 清空继承, 只注入必要变量; 不带任何 CLAUDE_CODE_* 会话变量
env -i \
  PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin" \
  HOME="$HOME" \
  TMPDIR="/tmp/agent_ws_$RUN_ID/tmp" \
  USER="$USER" \
  LANG="en_US.UTF-8" \
  CLAUDE_CONFIG_DIR="$CFG" \
  ANTHROPIC_AUTH_TOKEN="$ANTHROPIC_AUTH_TOKEN" \
  ANTHROPIC_BASE_URL="$ANTHROPIC_BASE_URL" \
  ANTHROPIC_DEFAULT_OPUS_MODEL="$REQUESTED_MODEL" \
  "$CLAUDE_BIN" \
    -p "$(cat "$RUNDIR/records/prompt.md")" \
    --model "$REQUESTED_MODEL" \
    --output-format stream-json --verbose \
    --allowedTools Read Edit Write Bash Glob Grep \
    --disallowedTools WebSearch WebFetch Task \
    --permission-mode bypassPermissions \
    --max-turns 200 \
    >"$RUNDIR/records/claude_stream.raw.jsonl" \
    2>"$RUNDIR/records/claude_stderr.log"
EXIT=$?

FINISHED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "$FINISHED_AT" > "$RUNDIR/records/finished_at.txt"
echo "$EXIT" > "$RUNDIR/records/exit_code.txt"
echo "=== 正式运行结束 exit=$EXIT ==="
echo "start=$STARTED_AT finish=$FINISHED_AT"
echo "raw stream 行数: $(wc -l < "$RUNDIR/records/claude_stream.raw.jsonl")"
echo "stderr 字节: $(wc -c < "$RUNDIR/records/claude_stderr.log")"
