"""
ExternalCLIAdapter: 用本机 claude CLI 的无头模式(-p)作为 agent runtime。
成熟工具循环 + 代理已配置, 避免自研 harness 污染评测变量(GPT探讨15)。
"""
import subprocess
from pathlib import Path

from .base import AgentAdapter, AgentConfig, AgentRunResult


class ExternalCLIAdapter(AgentAdapter):
    name = "external_cli"

    def run(self, prompt, workspace, config: AgentConfig, env) -> AgentRunResult:
        traj = workspace.parent / "trajectory" / "cli_stream.jsonl"
        traj.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            config.command,
            "-p", prompt,
            "--add-dir", str(workspace),
            "--dangerously-skip-permissions",   # run 在隔离一次性 workspace 内, 安全
            "--output-format", "stream-json",
            "--verbose",
        ]
        if config.model:
            cmd += ["--model", config.model]

        try:
            p = subprocess.run(
                cmd, cwd=str(workspace), env=env,
                capture_output=True, text=True,
                timeout=config.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return AgentRunResult(False, "", None, f"TIMEOUT {config.timeout_seconds}s")

        traj.write_text(p.stdout + "\n---STDERR---\n" + p.stderr, encoding="utf-8")
        # 取最后一段可读文本作为 final(stream-json 末尾通常是 result 事件)
        final = _extract_final(p.stdout)
        return AgentRunResult(p.returncode == 0, final, traj,
                              f"rc={p.returncode}")


def _extract_final(stream_stdout: str) -> str:
    import json
    final = ""
    for line in stream_stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "result" and "result" in ev:
            final = ev["result"]
    return final
