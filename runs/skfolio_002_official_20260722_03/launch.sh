#!/bin/bash
# 正式盲测启动器 v2 —— 修正 GPT审核4 全部问题。一次性运行, Agent 自行建环境。
set -u

RUN_ID=skfolio_002_official_20260722_03
BENCH=<PROJECT_ROOT>
RUNDIR=$BENCH/runs/$RUN_ID
WS=/tmp/agent_ws_$RUN_ID/workspace                 # ★ Agent 的唯一工作目录
CFG=/tmp/agent_ws_$RUN_ID/empty_claude_config      # 空配置 -> 不加载全局 CLAUDE.md
REQUESTED_MODEL='claude-opus-4-8[1m]'
CLAUDE_BIN=<HOME>/.local/bin/claude

# 认证/代理从 .env.local 读取
set -a; source "$BENCH/.env.local"; set +a

STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "$STARTED_AT" > "$RUNDIR/records/started_at.txt"

# ★ 关键修正: 切到 workspace 再调用; 白名单环境(env -i 清空继承, 去除 CLAUDE_CODE_* 会话变量)
cd "$WS" || { echo "FATAL: cannot cd to WS"; exit 90; }

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

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$RUNDIR/records/finished_at.txt"
echo "$EXIT" > "$RUNDIR/records/exit_code.txt"
echo "exit=$EXIT raw_lines=$(wc -l < "$RUNDIR/records/claude_stream.raw.jsonl")"
