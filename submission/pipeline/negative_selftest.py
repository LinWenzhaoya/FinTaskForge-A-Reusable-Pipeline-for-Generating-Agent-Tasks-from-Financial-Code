#!/usr/bin/env python3
"""
负向自测: 验证 Runner 在"该失败时确实失败", 防假阳性。
做法: 复制 skfolio_001 为临时畸变 case, 分别注入 5 种缺陷, 断言 Runner 判 FAIL。
用 Runner 环境的 python 运行本脚本。
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
RUNNER = BENCH / "pipeline" / "validate_case.py"
RUNNER_PY = BENCH / ".envs" / "_runner" / "bin" / "python"
SRC_CASE = BENCH / "cases" / "skfolio_001"


def run_runner(case_dir):
    p = subprocess.run([str(RUNNER_PY), str(RUNNER), str(case_dir)],
                       capture_output=True, text=True, timeout=900)
    return p.returncode


def make_case(tmp, mutate):
    """复制标准 case 到 tmp/cases/<id>, 应用 mutate(case_path), 返回 case 路径。"""
    case = tmp / "cases" / "mut"
    (tmp / "cases").mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC_CASE, case)
    # 让畸变 case 也能找到 .envs: metadata 里 python 是相对 bench_root 的,
    # 这里 bench_root=tmp, 故软链 .envs 过去
    (tmp / ".envs").symlink_to(BENCH / ".envs")
    mutate(case)
    return case


def meta_text(case):
    return (case / "metadata.yaml").read_text(encoding="utf-8")


def results():
    passed = []
    tmproot = Path(tempfile.mkdtemp(prefix="negtest_"))
    try:
        # 场景1: 安装命令故意失败
        def m1(c):
            t = meta_text(c).replace('install_command: "pip install -e . --no-deps -q"',
                                     'install_command: "pip install nonexistent-pkg-zzz==9.9.9"')
            (c / "metadata.yaml").write_text(t)
        # 场景2: 公开测试文件不存在(baseline 应判非目标 bug)
        def m2(c):
            (c / "task" / "repo" / "tests" / "test_public_reproduction.py").unlink()
        # 场景3: patch 删除 tests/ 下文件(应被 git 识别 + forbidden 命中 -> FAIL)
        def m3(c):
            repo = c / "task" / "repo"
            # 用 git 生成一个"删除 tests/__init__.py"的真实 diff
            subprocess.run("git init -q . && git add -A && "
                           "git -c user.email=a@a -c user.name=a commit -q -m base",
                           cwd=repo, shell=True, executable="/bin/bash")
            subprocess.run("git rm -q tests/__init__.py", cwd=repo, shell=True, executable="/bin/bash")
            p = subprocess.run("git diff --cached", cwd=repo, shell=True,
                               executable="/bin/bash", capture_output=True, text=True)
            # 恢复 repo 干净状态(撤销 git rm, 删掉 .git)
            subprocess.run("git reset -q --hard && rm -rf .git", cwd=repo, shell=True, executable="/bin/bash")
            # 把删除 diff 写成本 case 的 agent patch
            (c / "agent_run" / "patch.applyable.diff").write_text(p.stdout)

        # 场景4: patch 触碰白名单外文件
        def m4(c):
            t = meta_text(c).replace('- "src/skfolio/optimization/convex/_mean_risk.py"',
                                     '- "src/skfolio/NONEXISTENT_ONLY.py"')
            (c / "metadata.yaml").write_text(t)
        # 场景5: 隐藏测试注入到非 tests/ 目录(证明可配置, 且仍能跑)
        def m5(c):
            t = meta_text(c).replace("destination: tests/test_hidden_regression.py",
                                     "destination: src/skfolio/_hidden_probe.py")
            t = t.replace("command: \"python -m pytest tests/test_hidden_regression.py -q -p no:cacheprovider\"",
                          "command: \"python -m pytest src/skfolio/_hidden_probe.py -q -p no:cacheprovider\"")
            (c / "metadata.yaml").write_text(t)

        # 场景6: metadata 缺必填字段(应判 metadata_invalid -> FAIL)
        def m6(c):
            t = meta_text(c)
            # 删掉 baseline 段(用注释掉整段最简单: 改字段名使其缺失)
            t = t.replace("  baseline:", "  baseline_REMOVED:")
            (c / "metadata.yaml").write_text(t)

        cases = [
            ("1_install_fail", m1, "FAIL"),
            ("2_public_test_missing", m2, "FAIL"),
            ("3_patch_deletes_test", m3, "FAIL"),
            ("4_patch_out_of_allowlist", m4, "FAIL"),
            ("5_hidden_inject_nontests", m5, "PASS"),  # 应仍 PASS(证明可注入非tests)
            ("6_metadata_invalid", m6, "FAIL"),
        ]
        for name, mut, expect in cases:
            tmp = Path(tempfile.mkdtemp(prefix=f"neg_{name}_", dir=tmproot))
            case = make_case(tmp, mut)
            rc = run_runner(case)
            got = "PASS" if rc == 0 else "FAIL"
            ok = got == expect
            print(f"[{'OK' if ok else 'XX'}] {name}: expect={expect} got={got}")
            passed.append(ok)
    finally:
        shutil.rmtree(tmproot, ignore_errors=True)
    return passed


if __name__ == "__main__":
    res = results()
    print("-" * 40)
    print(f"负向自测: {sum(res)}/{len(res)} 符合预期")
    sys.exit(0 if all(res) else 1)
