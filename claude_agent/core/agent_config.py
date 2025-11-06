"""
Agent Configuration - Configurador completo de agente Claude
"""

import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..config.mcp_setup import get_claude_mcp_config
from ..core.session_tracker import SessionTracker
from ..hooks.supervisor import SupervisorHook
from ..tools.datetime_tool import CURRENT_DATETIME_TOOL, execute_current_datetime


class ClaudeAgentConfig:
    """Configurador completo de agente Claude"""

    def __init__(self, project_name: str, project_path: str):
        self.project_name = project_name
        self.project_path = Path(project_path)
        self.session_id = f"{project_name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
        self.sessions_dir = Path("sessions")
        self.session_path = self.sessions_dir / self.session_id

        # Crear directorios necesarios
        self.session_path.mkdir(parents=True, exist_ok=True)
        (self.session_path / "supervisor_logs").mkdir(exist_ok=True)

        print(f"📁 Sesión creada: {self.session_id}")
        print(f"📁 Path: {self.session_path}")

    def get_approved_tools(self) -> List[str]:
        """Tools aprobadas para el agente"""
        return [
            "Read",
            "Write",
            "Bash",
            "Edit",
            "Glob",
            "Grep",
            # Tool de ejemplo (no-MCP): fecha/hora actual
            "current_datetime",
        ]

    def create_session_tracker(self) -> SessionTracker:
        """Crea tracker de sesión"""
        return SessionTracker(
            session_id=self.session_id,
            cwd=str(self.project_path)
        )

    def create_supervisor_hook(self) -> SupervisorHook:
        """Crea hook de supervisor"""
        return SupervisorHook(self.session_id)

    def get_agent_options(self, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Configuración completa del agente Claude"""

        # Crear supervisor hook
        supervisor = self.create_supervisor_hook()

        # Cargar supervisor previo si existe
        supervisor_context = supervisor.load_supervisor_context()

        # Combinar system prompt con supervisor
        final_prompt = self._build_system_prompt(system_prompt, supervisor_context)

        # Crear tracker
        tracker = self.create_session_tracker()

        return {
            "system_prompt": final_prompt,
            "cwd": str(self.project_path),
            "allowed_tools": self.get_approved_tools(),
            "permission_mode": "bypassPermissions",  # Bypass completo para automatización
            "mcp_servers": get_claude_mcp_config(),
            "hooks": self._setup_hooks(supervisor, tracker),
            "continue_conversation": True,
            "session_id": self.session_id
        }

    def _build_system_prompt(self, base_prompt: Optional[str], supervisor: Optional[str]) -> str:
        """Construye el prompt completo con supervisor"""
        parts = []

        if supervisor:
            parts.append(f"# CONTEXTO PREVIO DE LA SESIÓN\n{supervisor}\n")

        if base_prompt:
            parts.append(base_prompt)
        else:
            parts.append(self._get_default_system_prompt())

        return "\n".join(parts)

    def _get_default_system_prompt(self) -> str:
        """System prompt por defecto"""
        return f"""
Eres un agente de desarrollo especializado trabajando en: {self.project_name}

Proyecto: {self.project_path}
Sesión: {self.session_id}

Características de esta sesión:
- Tools completamente habilitadas sin restricciones
- MCPs cargados automáticamente
- Tracking automático de todas las acciones
- Supervisor que mantiene contexto entre compactaciones

Trabaja de manera eficiente y mantén un registro claro de tus acciones.
"""

    def _setup_hooks(self, supervisor: SupervisorHook, tracker: SessionTracker) -> Dict[str, List]:
        """Configura hooks del agente"""
        return {
            "PreCompact": [supervisor.pre_compact_hook],
            "PostToolUse": [tracker.track_tool_use_hook]
        }

    def get_session_info(self) -> Dict[str, Any]:
        """Información de la sesión actual"""
        return {
            "session_id": self.session_id,
            "project_name": self.project_name,
            "project_path": str(self.project_path),
            "session_path": str(self.session_path),
            "tools_count": len(self.get_approved_tools()),
            "mcps_count": len(get_claude_mcp_config()),
        }


def setup_claude_agent(project_name: str, project_path: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Setup completo de agente Claude

    Args:
        project_name: Nombre del proyecto
        project_path: Ruta del proyecto
        system_prompt: Prompt personalizado (opcional)

    Returns:
        Configuración completa del agente
    """

    print(f"🚀 Inicializando agente Claude para: {project_name}")

    # Crear configurador
    config = ClaudeAgentConfig(project_name, project_path)

    # Obtener configuración completa
    agent_options = config.get_agent_options(system_prompt)

    # Información de sesión
    session_info = config.get_session_info()

    print(f"""
✅ Agente configurado:
   - Proyecto: {project_name}
   - Sesión: {config.session_id}
   - Tools: {len(agent_options['allowed_tools'])}
   - MCPs: {len(agent_options['mcp_servers'])}
   - Hooks: {len(agent_options['hooks'])}
   - Modo: {agent_options['permission_mode']}
""")

    return {
        "session_id": config.session_id,
        "agent_options": agent_options,
        "config": config,
        "session_info": session_info
    }