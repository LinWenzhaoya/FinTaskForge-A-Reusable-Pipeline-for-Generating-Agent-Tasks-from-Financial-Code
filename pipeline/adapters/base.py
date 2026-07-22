"""
Agent 适配器接口。run_agent.py 只依赖本接口, 不关心具体模型/工具循环实现。
换模型 = 新增一个 Adapter, 不改主流程(GPT探讨15 的架构原则)。
"""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentConfig:
    name: str
    adapter: str
    model: str
    max_turns: int = 60
    timeout_seconds: int = 1800
    command: str = "claude"
    extra: dict = field(default_factory=dict)


@dataclass
class AgentRunResult:
    ok: bool                       # Agent 是否正常结束(非崩溃/超时)
    final_text: str                # Agent 最终回答
    trajectory_path: Path | None   # 完整轨迹落盘路径
    detail: str = ""               # 错误/备注


class AgentAdapter:
    """所有适配器的基类。子类实现 run()。"""

    name = "base"

    def run(self, prompt: str, workspace: Path, config: AgentConfig,
            env: dict) -> AgentRunResult:
        """在 workspace 内解题。
        约束:
          - 只允许在 workspace 内读写(调用方已通过目录隔离保证);
          - 不得访问 case 的 grader/;
          - env 含 ANTHROPIC_AUTH_TOKEN / ANTHROPIC_BASE_URL 等凭证。
        返回 AgentRunResult。
        """
        raise NotImplementedError


def load_adapter(adapter_name: str) -> AgentAdapter:
    """按名称加载适配器实例。"""
    if adapter_name == "external_cli":
        from .external_cli import ExternalCLIAdapter
        return ExternalCLIAdapter()
    if adapter_name == "claude_agent_sdk":
        from .claude_agent_sdk import ClaudeAgentSDKAdapter
        return ClaudeAgentSDKAdapter()
    if adapter_name == "anthropic_tool_loop":
        from .anthropic_tool_loop import AnthropicToolLoopAdapter
        return AnthropicToolLoopAdapter()
    raise ValueError(f"未知 adapter: {adapter_name}")
