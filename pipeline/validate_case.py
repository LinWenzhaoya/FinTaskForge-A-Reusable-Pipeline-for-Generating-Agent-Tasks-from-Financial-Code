#!/usr/bin/env python3
"""
通用 Case 验收 Runner (配置驱动, 与具体仓库/领域无关)。
【v0.2 已冻结】——负向自测 6/6 通过后冻结; 构造 skfolio_002 期间不得修改本文件。

用法:
    python pipeline/validate_case.py <case_dir>

Runner 自身依赖(pyyaml)与 Case 依赖(被测仓库)分离:
  - Runner 用运行它的解释器(需 pyyaml);
  - Case 测试用 metadata.environment.python 指定的独立解释器。

判分流程(全部由 metadata.yaml 的 validation 段驱动):
  安装环境(失败即 environment_install_failed 并终止)
  -> baseline: 返回码 + 必现/禁现输出特征 三重校验(证明是目标 bug, 非环境错误)
  -> git 识别 patch 实际改动文件, 校验 白名单内 且 黑名单外
  -> 应用 patch
  -> 公开测试应通过
  -> 注入(可多份)隐藏测试并运行, 应通过
  -> 输出人类可读 + 可审计 result.json; 无论成败清理临时目录

Runner 逻辑不含任何具体仓库/模型/文件名。
"""
import argparse
import fnmatch
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Runner 需要 pyyaml(装在 Runner 环境, 与 case 环境分离): pip install pyyaml", file=sys.stderr)
    sys.exit(2)

RUNNER_VERSION = "0.2"

REQUIRED_FIELDS = [
    "environment.python",
    "environment.install_command",
    "validation.patch_file",
    "validation.baseline",
    "validation.public_test_command",
    "validation.hidden_tests",
]


def validate_metadata(meta):
    """返回缺失字段列表(空=通过)。支持点号嵌套路径。"""
    missing = []
    for path in REQUIRED_FIELDS:
        node = meta
        for key in path.split("."):
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                missing.append(path)
                break
    return missing


class Report:
    def __init__(self):
        self.checks = []
        self.fatal = None

    def add(self, name, passed, detail=""):
        self.checks.append({"name": name, "pass": bool(passed), "detail": detail})
        print(f"[{'PASS' if passed else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))
        return passed

    def stop(self, err):
        self.fatal = err
        print(f"[ERROR] {err}")

    @property
    def ok(self):
        return self.fatal is None and all(c["pass"] for c in self.checks)


def run(cmd, cwd, timeout):
    try:
        p = subprocess.run(cmd, cwd=cwd, shell=True, executable="/bin/bash",
                           capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return 124, f"TIMEOUT after {timeout}s"


def git_changed_files(repo, patch_file, timeout):
    """在临时 git 仓库应用 patch, 用 git 识别实际改动文件(覆盖增/删/改/重命名)。
    返回 (applied_ok, changed_paths, detail)。"""
    run("git init -q . && git add -A && git -c user.email=a@a -c user.name=a commit -q -m base",
        cwd=repo, timeout=timeout)
    rc, out = run(f"git apply --index {patch_file}", cwd=repo, timeout=timeout)
    if rc != 0:
        return False, [], out.strip()[:200]
    _, names = run("git diff --cached --name-only", cwd=repo, timeout=timeout)
    changed = [l.strip() for l in names.splitlines() if l.strip()]
    return True, changed, ""


def match_any(path, patterns):
    return any(fnmatch.fnmatch(path, pat) or path.startswith(pat.rstrip("*/"))
               for pat in patterns)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir")
    args = ap.parse_args()

    case_dir = Path(args.case_dir).resolve()
    bench_root = case_dir.parent.parent
    meta = yaml.safe_load((case_dir / "metadata.yaml").read_text(encoding="utf-8"))
    instance_id = meta.get("instance_id", case_dir.name)

    missing = validate_metadata(meta)
    if missing:
        rep = Report()
        print(f"=== 验收 {instance_id} (runner v{RUNNER_VERSION}) ===")
        rep.stop(f"metadata_invalid: 缺少字段 {missing}")
        bench_root = case_dir.parent.parent
        return finish(rep, bench_root, instance_id, meta, {}, Path("/nonexistent"))

    v = meta["validation"]
    env = meta["environment"]
    bench_root = case_dir.parent.parent
    timeout = int(v.get("timeout_seconds", 600))

    # 注意: 不能 .resolve() —— 会把 venv 的 symlink 解析成真实解释器路径,
    # 导致 pip 用到系统 Python(PEP 668)。用 absolute() 保留 venv symlink。
    py = (bench_root / env["python"]).absolute()
    rep = Report()
    timings = {}
    print(f"=== 验收 {instance_id} (runner v{RUNNER_VERSION}) ===")

    if not py.exists():
        rep.stop(f"case_python_missing: {py}")
        return finish(rep, bench_root, instance_id, meta, timings, py)

    work = Path(tempfile.mkdtemp(prefix=f"vc_{instance_id}_"))
    cleaned = False
    try:
        repo = work / "repo"
        shutil.copytree(case_dir / "task" / "repo", repo)

        # 0. 安装环境 —— 失败即终止(修1)
        t = time.time()
        install = env["install_command"].replace("pip ", f"{py} -m pip ", 1)
        rc, out = run(install, cwd=repo, timeout=timeout)
        timings["install"] = round(time.time() - t, 1)
        if not rep.add("Environment installation succeeds", rc == 0, f"rc={rc}"):
            rep.stop("environment_install_failed")
            (work / "install.log").write_text(out)
            raise SystemExit  # 跳到 finally 清理

        def pytest(cmd):
            return run(cmd.replace("python ", f"{py} ", 1), cwd=repo, timeout=timeout)

        # 1. baseline: 返回码 + 必现/禁现特征 三重校验(修2)
        t = time.time()
        b = v["baseline"]
        rc, out = pytest(b["public_test_command"])
        timings["baseline"] = round(time.time() - t, 1)
        code_ok = rc in b.get("expected_exit_codes", [1])
        req_ok = all(p in out for p in b.get("required_output_patterns", []))
        forb_hit = [p for p in b.get("forbidden_output_patterns", []) if p in out]
        rep.add("Baseline reproduces target bug",
                code_ok and req_ok and not forb_hit,
                f"rc={rc} code_ok={code_ok} req_ok={req_ok} forbidden={forb_hit}")

        # 2. git 识别 patch 改动 + 白名单/黑名单(修3, 修4)
        patch_file = case_dir / v["patch_file"]
        applied, changed, detail = git_changed_files(repo, patch_file, timeout)
        run("rm -rf .git", cwd=repo, timeout=60)
        rep.add("Agent patch applies cleanly", applied, detail)
        allowed = v.get("allowed_patch_paths", [])
        forbidden = v.get("forbidden_patch_paths", [])
        out_of_allow = [p for p in changed if allowed and not match_any(p, allowed)]
        hit_forbid = [p for p in changed if match_any(p, forbidden)]
        rep.add("Patch touches only allowed paths", applied and not out_of_allow,
                f"changed={changed}" + (f" OUT_OF_ALLOW={out_of_allow}" if out_of_allow else ""))
        rep.add("Patch touches no forbidden paths", not hit_forbid,
                f"FORBIDDEN_HIT={hit_forbid}" if hit_forbid else "")

        # 3. 公开测试应通过
        t = time.time()
        rc, _ = pytest(v["public_test_command"])
        timings["public"] = round(time.time() - t, 1)
        rep.add("Public tests pass", rc == 0, f"rc={rc}")

        # 4. 注入(可多份)隐藏测试并运行(修5)
        for cp in v["hidden_tests"]["copies"]:
            dst = repo / cp["destination"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(case_dir / cp["source"], dst)
        t = time.time()
        rc, out = pytest(v["hidden_tests"]["command"])
        timings["hidden"] = round(time.time() - t, 1)
        rep.add("Hidden tests pass", rc == 0, f"rc={rc}")

    except SystemExit:
        pass
    finally:
        shutil.rmtree(work, ignore_errors=True)
        cleaned = not work.exists()

    return finish(rep, bench_root, instance_id, meta, timings, py, case_dir, cleaned)


def finish(rep, bench_root, instance_id, meta, timings, py, case_dir=None, cleaned=True):
    print("-" * 40)
    npass = sum(c["pass"] for c in rep.checks)
    print(f"FINAL RESULT: {'PASS' if rep.ok else 'FAIL'} ({npass}/{len(rep.checks)} checks)"
          + (f"  [fatal: {rep.fatal}]" if rep.fatal else ""))

    patch_sha = None
    if case_dir:
        pf = case_dir / meta["validation"]["patch_file"]
        if pf.exists():
            patch_sha = hashlib.sha256(pf.read_bytes()).hexdigest()[:16]
    rcpy, pyver = run(f"{py} --version", cwd=".", timeout=30) if py.exists() else (1, "")

    result = {
        "instance_id": instance_id,
        "runner_version": RUNNER_VERSION,
        "final": "PASS" if rep.ok else "FAIL",
        "fatal_error": rep.fatal,
        "checks": rep.checks,
        "timings_sec": timings,
        "patch_sha256_16": patch_sha,
        "case_python": str(py),
        "case_python_version": pyver.strip(),
        "temp_dir_cleaned": cleaned,
    }
    out_dir = bench_root / "results"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"{instance_id}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"结果已写入 results/{instance_id}.json")
    sys.exit(0 if rep.ok else 1)


if __name__ == "__main__":
    main()
