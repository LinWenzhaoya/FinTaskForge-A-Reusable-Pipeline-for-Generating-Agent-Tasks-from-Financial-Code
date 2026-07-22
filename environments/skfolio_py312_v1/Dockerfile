# 占位: 跨机器复现的目标形态(本轮未构建, 当前用本机 venv)。
FROM python:3.12-slim
WORKDIR /app
COPY requirements-pinned.txt .
RUN pip install --no-cache-dir -r requirements-pinned.txt pytest
# 具体 case 的 repo 快照在 grade 时挂载/解压进来
