#!/usr/bin/env python3
"""
统一冻结两题的标准交付资产校验和 (case-freeze-v1)。

覆盖范围 (仅标准交付资产, 稳定可复算):
  - task_tree_sha256  : cases/<id>/task/   目录下全部文件内容 (Base 唯一来源)
  - grader_tree_sha256: cases/<id>/grader/  目录下全部文件内容 (隐藏测试 + 参考/gold patch)
  - agent_patch_sha256: cases/<id>/agent_run/patch.applyable.diff (被 Validator 使用的 patch)

明确排除: results/ 日志、__pycache__/.pytest_cache/.venv/.git 缓存、.envs 本地环境、
         audit_backups 备份、metadata.yaml (状态字段会在验收后回填, 不纳入冻结)。
sha256_tree 只哈希文件内容与相对路径, 忽略空目录, 排除上述缓存目录。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
import _common as C  # noqa: E402

BENCH = Path(__file__).resolve().parent.parent
SCHEMA = "case-freeze-v1"


def freeze(case_id):
    case = BENCH / "cases" / case_id
    checksums = {
        "schema": SCHEMA,
        "scope": "task/ + grader/ + agent_run/patch.applyable.diff; "
                 "excludes results, caches, .envs, backups, metadata.yaml",
        "task_tree_sha256": C.sha256_tree(case / "task"),
        "grader_tree_sha256": C.sha256_tree(case / "grader"),
        "agent_patch_sha256": C.sha256_file(case / "agent_run" / "patch.applyable.diff"),
    }
    C.write_json(case / "checksums.json", checksums)
    print(f"[{case_id}] frozen:")
    for k, v in checksums.items():
        print(f"    {k}: {v[:16] if k.endswith('sha256') else v}")
    return checksums


if __name__ == "__main__":
    for cid in ("skfolio_001", "skfolio_002"):
        freeze(cid)
