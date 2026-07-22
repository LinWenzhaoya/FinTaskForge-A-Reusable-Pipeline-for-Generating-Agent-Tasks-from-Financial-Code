#!/usr/bin/env python3
"""
第三阶段动态验收编排 (一次性运行脚本, 不属平台代码; 产物即 results/final_verification/)。

对 4 个目标各跑一次冻结的 Validator v0.2 / negative_selftest, 保存独立日志:
  1. skfolio_001 标准 Case          (Agent patch)                -> 001.log
  2. skfolio_002 Gold Patch          (临时副本, patch_file=gold)  -> gold.log
  3. skfolio_002 标准 Case           (Agent patch)                -> agent.log
  4. negative_selftest                                            -> negative.log

约束 (来自复审口径):
  - 不在标准 Case 上来回改 metadata; Gold 用独立临时副本, 只改副本的 validation.patch_file。
  - 002 标准 Case 的 patch_file 本就指向 Agent patch, 故直接跑标准 Case 即 Agent 验收,
    同时刷新 canonical results/skfolio_002.json; 无需再造 Agent 临时副本。
  - 临时副本放在 cases/ 下 (Validator 用 case_dir.parent.parent 定位 .envs), 跑完立即删除, 不进交付。
  - 临时副本 instance_id 改名, 避免覆盖标准 results/<id>.json。
"""
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

BENCH = Path(__file__).resolve().parents[2]
CASES = BENCH / "cases"
RUNNER = BENCH / "pipeline" / "validate_case.py"
RUNNER_PY = BENCH / ".envs" / "_runner" / "bin" / "python"
SELFTEST = BENCH / "pipeline" / "negative_selftest.py"
OUT = BENCH / "results" / "final_verification"


def run_and_log(argv, logpath, title):
    print(f"\n===== {title} =====")
    p = subprocess.run(argv, capture_output=True, text=True, timeout=1800)
    body = (f"$ {' '.join(str(a) for a in argv)}\n\n"
            f"--- STDOUT ---\n{p.stdout}\n--- STDERR ---\n{p.stderr}\n"
            f"--- EXIT: {p.returncode} ---\n")
    Path(logpath).write_text(body, encoding="utf-8")
    tail = [l for l in p.stdout.splitlines() if "FINAL RESULT" in l or "结果已写入" in l]
    print("\n".join(tail) or f"(exit={p.returncode})")
    return p.returncode


def make_variant(base_id, variant_id, patch_file):
    """复制标准 Case 为临时副本, 只改 validation.patch_file 与 instance_id。"""
    src = CASES / base_id
    dst = CASES / variant_id
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    meta = yaml.safe_load((dst / "metadata.yaml").read_text(encoding="utf-8"))
    meta["instance_id"] = variant_id
    meta["validation"]["patch_file"] = patch_file
    (dst / "metadata.yaml").write_text(
        yaml.safe_dump(meta, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return dst


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = []
    try:
        # 1. 001 标准 Case (Agent patch, metadata 已指向 agent_run/patch.applyable.diff)
        run_and_log([str(RUNNER_PY), str(RUNNER), str(CASES / "skfolio_001")],
                    OUT / "001.log", "1/4 skfolio_001 (Agent patch)")

        # 2. 002 Gold Patch (临时副本)
        gold = make_variant("skfolio_002", "_verify_002_gold", "grader/gold.patch")
        tmp.append(gold)
        run_and_log([str(RUNNER_PY), str(RUNNER), str(gold)],
                    OUT / "gold.log", "2/4 skfolio_002 Gold Patch")

        # 3. 002 标准 Case (Agent patch; 刷新 canonical results/skfolio_002.json)
        run_and_log([str(RUNNER_PY), str(RUNNER), str(CASES / "skfolio_002")],
                    OUT / "agent.log", "3/4 skfolio_002 (Agent patch, 标准 Case)")

        # 4. negative selftest
        run_and_log([str(RUNNER_PY), str(SELFTEST)],
                    OUT / "negative.log", "4/4 negative_selftest")
    finally:
        for d in tmp:
            if d.exists():
                shutil.rmtree(d)
                print(f"已删除临时副本 {d.relative_to(BENCH)}")
    # 移动 Gold 临时副本产生的 results json 到 final_verification, 避免污染标准 results/
    for vid in ("_verify_002_gold",):
        j = BENCH / "results" / f"{vid}.json"
        if j.exists():
            j.rename(OUT / f"{vid.replace('_verify_002_', '002_')}.result.json")


if __name__ == "__main__":
    main()
