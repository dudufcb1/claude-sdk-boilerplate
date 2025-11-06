"""
Claude Agent Boilerplate - Setup completo para agente Claude
"""

from .core.agent_config import ClaudeAgentConfig, setup_claude_agent
from .core.session_tracker import SessionTracker
from .hooks.supervisor import SupervisorHook
from .config.mcp_setup import setup_claude_mcp_config, show_current_mcp_config

__version__ = "1.0.0"
__all__ = [
    "ClaudeAgentConfig",
    "setup_claude_agent",
    "SessionTracker",
    "SupervisorHook",
    "setup_claude_mcp_config",
    "show_current_mcp_config"
]