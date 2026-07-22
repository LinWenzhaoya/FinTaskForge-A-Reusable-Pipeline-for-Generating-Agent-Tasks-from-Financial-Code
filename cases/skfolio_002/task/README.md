# 环境与运行说明

本项目是一个投资组合优化库(基于 scikit-learn 风格 API)的源码快照。你的任务见 `TASK.md`。

## 环境搭建

要求 Python 3.12。本材料布局为:工作目录根下有 `requirements-pinned.txt` 与 `repo/`(源码及 `pyproject.toml` 在 `repo/` 内)。建议使用隔离虚拟环境,在**工作目录根**执行:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements-pinned.txt
pip install -e ./repo --no-deps
```

> 注意:请使用 `requirements-pinned.txt` 中锁定的依赖版本。仓库 `repo/pyproject.toml` 中的依赖只写了下限,直接安装最新依赖会导致底层凸优化库(cvxpy)API 不兼容而无法 import。`--no-deps` 用于避免 pip 覆盖已锁定的版本;可编辑安装的目标是 `./repo`。

## 运行公开测试

复现问题的公开测试位于 `repo/tests/`。进入 `repo/` 运行:

```bash
cd repo
python -m pytest tests/test_public_reproduction.py -v
```

在你修复之前,该测试应当失败(会观察到任务中描述的异常)。

## 你需要提交的内容

1. 你对源码的修改(patch / diff,或直接修改后的文件)。
2. 一段说明:你定位到的根因是什么、为什么这样修、改了哪些文件。
3. 你运行过的测试及其结果。

## 约束

- **不允许**通过修改、删除或跳过测试来让测试通过。
- **不允许**用 `try/except` 吞掉异常、或对特定输入硬编码返回值来蒙混。
- 修复应当是最小的、针对根因的改动,并且不能破坏其他优化模型原本合理的行为。
- 只使用本仓库内的代码与 `requirements-pinned.txt` 的依赖,不需要联网。
