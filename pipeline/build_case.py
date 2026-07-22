#!/usr/bin/env python3
"""
build_case.py —— 生成不可变标准 Case。
  清理 task/repo(去 .github/缓存/venv 残留)
  -> 归档 task/repo.tar.zst + checksums.json
  -> 验 base-fail(修复前公开测试失败)
  -> 验 gold-pass(官方源码修复 -> 隐藏测试全过)
不启动被测 Agent。

用法: python pipeline/build_case.py cases/skfolio_002
需要 metadata 里有: base_commit, fix_commit, external_repo(相对 benchmark 根),
以及 validation 段(baseline / hidden_tests / allowed_patch_paths)。
"""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

import yaml
sys.path.insert(0, str(Path(__file__).parent))
import _common as C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir")
    args = ap.parse_args()
    case_dir = Path(args.case_dir).resolve()
    bench_root = case_dir.parent.parent
    meta = yaml.safe_load((case_dir / "metadata.yaml").read_text(encoding="utf-8"))
    v = meta["validation"]
    py = C.resolve_case_python(bench_root, meta)
    report = {"instance_id": meta.get("instance_id", case_dir.name), "steps": []}

    def step(name, ok, detail=""):
        report["steps"].append({"name": name, "ok": bool(ok), "detail": detail})
        print(f"[{'OK' if ok else 'XX'}] {name}" + (f"  ({detail})" if detail else ""))
        return ok

    repo = case_dir / "task" / "repo"

    # 1. 清理污染/泄漏
    removed = []
    for junk in [".git", ".github", ".venv", ".pytest_cache"]:
        for p in repo.rglob(junk):
            shutil.rmtree(p, ignore_errors=True); removed.append(junk)
    for p in repo.rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)
    for p in repo.rglob("*.egg-info"):
        shutil.rmtree(p, ignore_errors=True)
    step("清理污染/泄漏(.git/.github/缓存/venv)", True, f"removed={sorted(set(removed))}")

    # 2. 归档 + checksum
    tar = case_dir / "task" / "repo.tar.zst"
    C.archive_repo(repo, tar)
    checksums = {
        "repo.tar.zst": C.sha256_file(tar),
        "task_tree": C.sha256_tree(case_dir / "task"),
        "grader_tree": C.sha256_tree(case_dir / "grader"),
    }
    C.write_json(case_dir / "checksums.json", checksums)
    step("归档 repo.tar.zst + checksums.json", tar.exists(),
         f"sha={checksums['repo.tar.zst'][:12]}")

    # 3. 验 base-fail
    work = Path(tempfile.mkdtemp(prefix="build_base_"))
    try:
        r = C.extract_repo(tar, work)
        C.run(f"{py} -m pip install -e . --no-deps -q", r, 600)
        rc, out = C.run(v["baseline"]["public_test_command"].replace("python", str(py), 1),
                        r, v.get("timeout_seconds", 600))
        ok, det = C.baseline_verdict(rc, out, v["baseline"])
        step("base-fail(修复前公开测试失败且是目标bug)", ok, det)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    # 4. 验 gold-pass: 从 external fix commit 取源码修复 -> 应用 -> 隐藏测试全过
    ext = bench_root / meta["external_repo"]
    gold = case_dir / "grader" / "gold.patch"
    allowed = v.get("allowed_patch_paths", [])
    # 动态生成: fix_commit 对 base_commit, 仅限 allowed 路径
    paths = " ".join(f"'{p}'" for p in allowed) if allowed else ""
    rc, diff = C.run(
        f"git diff {meta['base_commit']} {meta['fix_commit']} -- {paths}", ext, 120)
    gold.write_text(diff, encoding="utf-8")
    work = Path(tempfile.mkdtemp(prefix="build_gold_"))
    try:
        r = C.extract_repo(tar, work)
        applied, changed, det = C.git_apply_changed(r, gold)
        if applied:
            # 重新应用(git_apply_changed 已 reset), 用 patch 直接打
            C.run(f"git init -q . && git apply {gold} && rm -rf .git", r, 120)
            C.run(f"{py} -m pip install -e . --no-deps -q", r, 600)
            for cp in v["hidden_tests"]["copies"]:
                dst = r / cp["destination"]
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(case_dir / cp["source"], dst)
            rc, out = C.run(v["hidden_tests"]["command"].replace("python", str(py), 1),
                            r, v.get("timeout_seconds", 600))
            step("gold-pass(官方修复 -> 隐藏测试全过)", rc == 0, f"rc={rc}")
        else:
            step("gold-pass(官方修复 -> 隐藏测试全过)", False, f"gold patch 应用失败: {det}")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    ok = all(s["ok"] for s in report["steps"])
    report["case_valid"] = ok
    C.write_json(bench_root / "results" / "build" / f"{report['instance_id']}.json", report)
    print("-" * 40)
    print(f"CASE BUILD: {'VALID' if ok else 'INVALID'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
