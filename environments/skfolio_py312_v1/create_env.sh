#!/bin/bash
# 重建本环境的 venv(本机级复现)。跨机器请改用 Dockerfile。
set -e
BENCH_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
python3.12 -m venv "$BENCH_ROOT/.envs/skfolio"
"$BENCH_ROOT/.envs/skfolio/bin/pip" install --upgrade pip
"$BENCH_ROOT/.envs/skfolio/bin/pip" install -r "$(dirname "$0")/requirements-pinned.txt" pytest
echo "环境就绪: $BENCH_ROOT/.envs/skfolio"
