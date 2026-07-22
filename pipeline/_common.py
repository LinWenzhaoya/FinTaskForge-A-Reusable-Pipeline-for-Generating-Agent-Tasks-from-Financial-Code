"""三阶段共用的工具函数。"""
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def load_dotenv(bench_root: Path) -> dict:
    """读 .env.local -> dict(仅注入所需凭证)。"""
    env = {}
    f = bench_root / ".env.local"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def resolve_case_python(bench_root: Path, meta: dict) -> Path:
    """按 environment_id 解析 case 的 python 解释器(不 resolve symlink, 保 venv)。"""
    env_id = meta.get("environment_id") or meta.get("environment", {}).get("id")
    if env_id:
        envf = bench_root / "environments" / env_id / "environment.yaml"
        edef = yaml.safe_load(envf.read_text(encoding="utf-8"))
        return (bench_root / edef["venv"] / "bin" / "python").absolute()
    # 兼容旧字段
    return (bench_root / meta["environment"]["python"]).absolute()


def run(cmd, cwd, timeout, env=None):
    try:
        p = subprocess.run(cmd, cwd=str(cwd), shell=True, executable="/bin/bash",
                           capture_output=True, text=True, timeout=timeout, env=env)
        return p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return 124, f"TIMEOUT after {timeout}s"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_tree(root: Path) -> str:
    """对目录下所有文件内容做稳定哈希(排除缓存)。"""
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(x in p.parts for x in
                                   ("__pycache__", ".pytest_cache", ".venv", ".git")):
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def archive_repo(repo_dir: Path, out_tar: Path):
    """把 repo 目录打包成 tar.zst(排除缓存/venv/git)。"""
    excl = {"__pycache__", ".pytest_cache", ".venv", ".git", "*.egg-info"}
    tmp_tar = out_tar.with_suffix(".tar")
    with tarfile.open(tmp_tar, "w") as tf:
        for p in sorted(repo_dir.rglob("*")):
            if p.is_file() and not any(
                any(part == e or (e.startswith("*") and part.endswith(e[1:]))
                    for e in excl) for part in p.parts):
                tf.add(p, arcname=str(p.relative_to(repo_dir)))
    # zstd 压缩
    run(f"zstd -q -f {tmp_tar} -o {out_tar}", cwd=out_tar.parent, timeout=120)
    tmp_tar.unlink(missing_ok=True)


def extract_repo(tar_zst: Path, dest: Path) -> Path:
    """解压 repo.tar.zst 到 dest/repo, 返回 repo 路径。"""
    dest.mkdir(parents=True, exist_ok=True)
    tmp_tar = dest / "repo.tar"
    run(f"zstd -q -d -f {tar_zst} -o {tmp_tar}", cwd=dest, timeout=120)
    repo = dest / "repo"
    repo.mkdir(exist_ok=True)
    with tarfile.open(tmp_tar) as tf:
        tf.extractall(repo)
    tmp_tar.unlink(missing_ok=True)
    return repo


def git_apply_changed(repo: Path, patch_file: Path, timeout=120):
    """临时 git 仓库应用 patch, 返回 (applied, changed_paths, detail)。"""
    run("git init -q . && git add -A && "
        "git -c user.email=a@a -c user.name=a commit -q -m base", repo, timeout)
    rc, out = run(f"git apply --index {patch_file}", repo, timeout)
    if rc != 0:
        run("rm -rf .git", repo, 60)
        return False, [], out.strip()[:200]
    _, names = run("git diff --cached --name-only", repo, timeout)
    changed = [l.strip() for l in names.splitlines() if l.strip()]
    run("rm -rf .git", repo, 60)
    return True, changed, ""


def baseline_verdict(rc, out, baseline_cfg):
    """baseline 三重校验: 返回码 + 必现 + 禁现。返回 (ok, detail)。"""
    code_ok = rc in baseline_cfg.get("expected_exit_codes", [1])
    req_ok = all(p in out for p in baseline_cfg.get("required_output_patterns", []))
    forb = [p for p in baseline_cfg.get("forbidden_output_patterns", []) if p in out]
    return (code_ok and req_ok and not forb,
            f"rc={rc} code_ok={code_ok} req_ok={req_ok} forbidden={forb}")


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
