"""
Claude Agent Setup - Boilerplate completo
Configuración de agente Claude con tools, MCPs, sesiones y supervisor automático
"""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

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

    def get_claude_mcp_config(self) -> Dict[str, Any]:
        """Carga automática de MCPs desde ~/.claude.json"""
        claude_config_path = Path.home() / ".claude.json"

        if not claude_config_path.exists():
            print("⚠️  ~/.claude.json no encontrado. Creando configuración básica...")
            self._create_default_claude_config(claude_config_path)
            return {}

        try:
            with open(claude_config_path, 'r') as f:
                config = json.load(f)
                mcp_servers = config.get("mcpServers", {})
                print(f"✅ MCPs cargados: {list(mcp_servers.keys())}")
                return mcp_servers
        except Exception as e:
            print(f"❌ Error cargando ~/.claude.json: {e}")
            return {}

    def _create_default_claude_config(self, path: Path):
        """Crea configuración básica de Claude si no existe"""
        default_config = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
                }
            }
        }

        with open(path, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"✅ Configuración básica creada en {path}")

    def get_approved_tools(self) -> List[str]:
        """Tools aprobadas para el agente"""
        return [
            "Read",
            "Write",
            "Bash",
            "Edit",
            "Glob",
            "Grep"
        ]

    def create_session_tracker(self) -> 'SessionTracker':
        """Crea tracker de sesión"""
        return SessionTracker(
            session_id=self.session_id,
            cwd=str(self.project_path)
        )

    def get_agent_options(self, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Configuración completa del agente Claude"""

        # Cargar supervisor previo si existe
        supervisor_context = self.load_supervisor_context()

        # Combinar system prompt con supervisor
        final_prompt = self._build_system_prompt(system_prompt, supervisor_context)

        return {
            "system_prompt": final_prompt,
            "cwd": str(self.project_path),
            "allowed_tools": self.get_approved_tools(),
            "permission_mode": "bypassPermissions",  # Bypass completo para automatización
            "mcp_servers": self.get_claude_mcp_config(),
            "hooks": self._setup_hooks(),
            "continue_conversation": True
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

    def _setup_hooks(self) -> Dict[str, List]:
        """Configura hooks del agente"""
        tracker = self.create_session_tracker()
        supervisor = SupervisorHook(self.session_id)

        return {
            "PreCompact": [supervisor.pre_compact_hook],
            "PostToolUse": [tracker.track_tool_use_hook]
        }

    def load_supervisor_context(self) -> Optional[str]:
        """Carga contexto del supervisor previo"""
        supervisor_file = self.session_path / "last_supervisor.txt"

        if supervisor_file.exists():
            try:
                content = supervisor_file.read_text()
                print(f"✅ Supervisor cargado desde sesión previa")
                return content
            except Exception as e:
                print(f"⚠️  Error cargando supervisor: {e}")

        return None

    def save_supervisor_context(self, context: str):
        """Guarda contexto del supervisor"""
        supervisor_file = self.session_path / "last_supervisor.txt"
        supervisor_file.write_text(context)
        print(f"✅ Supervisor guardado: {len(context)} caracteres")


class SessionTracker:
    """Tracker de sesión en tiempo real"""

    def __init__(self, session_id: str, cwd: str):
        self.session_id = session_id
        self.cwd = cwd
        self.session_path = Path("sessions") / session_id
        self.audit_file = self.session_path / "audit.json"

        # Inicializar audit
        self.audit_data = {
            "session_id": session_id,
            "cwd": cwd,
            "created_at": datetime.now().isoformat(),
            "user_messages": [],
            "agent_messages": [],
            "files_created": [],
            "files_modified": [],
            "files_viewed": [],
            "tools_used": {},
            "terminal_commands": [],
            "problems_discussed": [],
            "last_diffs": [],
            "last_writes": []
        }

        self._save_audit()

    def track_tool_use_hook(self, tool_name: str, args: Dict[str, Any], result: Any):
        """Hook para tracking automático de tools"""

        # Incrementar contador de tool
        if tool_name not in self.audit_data["tools_used"]:
            self.audit_data["tools_used"][tool_name] = 0
        self.audit_data["tools_used"][tool_name] += 1

        # Tracking específico por tool
        if tool_name == "Write":
            file_path = args.get("file_path", "")
            self.audit_data["files_created"].append({
                "file": file_path,
                "timestamp": datetime.now().isoformat()
            })
            self.audit_data["last_writes"].append({
                "file": file_path,
                "content_preview": args.get("content", "")[:200]
            })

        elif tool_name == "Edit":
            file_path = args.get("file_path", "")
            self.audit_data["files_modified"].append({
                "file": file_path,
                "timestamp": datetime.now().isoformat()
            })
            self.audit_data["last_diffs"].append({
                "file": file_path,
                "old_string": args.get("old_string", "")[:100],
                "new_string": args.get("new_string", "")[:100]
            })

        elif tool_name == "Read":
            file_path = args.get("file_path", "")
            self.audit_data["files_viewed"].append({
                "file": file_path,
                "timestamp": datetime.now().isoformat()
            })

        elif tool_name == "Bash":
            command = args.get("command", "")
            self.audit_data["terminal_commands"].append({
                "command": command,
                "timestamp": datetime.now().isoformat()
            })

        self._save_audit()
        print(f"📊 Tracked: {tool_name} - Total tools used: {sum(self.audit_data['tools_used'].values())}")

    def add_user_message(self, message: str):
        """Registra mensaje del usuario"""
        self.audit_data["user_messages"].append({
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        self._save_audit()

    def add_agent_message(self, message: str):
        """Registra mensaje del agente"""
        self.audit_data["agent_messages"].append({
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        self._save_audit()

    def _save_audit(self):
        """Guarda audit data"""
        with open(self.audit_file, 'w') as f:
            json.dump(self.audit_data, f, indent=2)


class SupervisorHook:
    """Hook para supervisor automático"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_path = Path("sessions") / session_id

    def pre_compact_hook(self, transcript: str):
        """Genera supervisor antes de compactar"""
        print("🧠 Generando supervisor automático...")

        # Analizar transcript y generar contexto
        supervisor_context = self._analyze_transcript(transcript)

        # Guardar supervisor
        supervisor_file = self.session_path / "last_supervisor.txt"
        supervisor_file.write_text(supervisor_context)

        # Log del supervisor
        log_file = self.session_path / "supervisor_logs" / f"supervisor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        log_file.write_text(supervisor_context)

        print(f"✅ Supervisor generado: {len(supervisor_context)} caracteres")
        return supervisor_context

    def _analyze_transcript(self, transcript: str) -> str:
        """Analiza transcript y genera contexto del supervisor"""

        # Análisis básico del transcript
        lines = transcript.split('\n')
        user_messages = [line for line in lines if line.startswith('Human:')]
        assistant_messages = [line for line in lines if line.startswith('Assistant:')]

        # Detectar patrones
        files_mentioned = []
        commands_run = []

        for line in lines:
            if 'file_path' in line or '.py' in line or '.js' in line:
                files_mentioned.append(line.strip())
            if 'bash' in line.lower() or 'command' in line.lower():
                commands_run.append(line.strip())

        # Generar contexto estructurado
        context = f"""
<SUPERVISOR_CONTEXT session="{self.session_id}">
<SESSION_SUMMARY>
- Mensajes del usuario: {len(user_messages)}
- Respuestas del asistente: {len(assistant_messages)}
- Archivos mencionados: {len(files_mentioned)}
- Comandos ejecutados: {len(commands_run)}
</SESSION_SUMMARY>

<KEY_ACTIVITIES>
{chr(10).join(f"- {msg[:100]}..." for msg in user_messages[-3:])}
</KEY_ACTIVITIES>

<FILES_WORKED_ON>
{chr(10).join(f"- {file[:100]}..." for file in files_mentioned[-5:])}
</FILES_WORKED_ON>

<RECENT_COMMANDS>
{chr(10).join(f"- {cmd[:100]}..." for cmd in commands_run[-3:])}
</RECENT_COMMANDS>

<CONTEXT_INSTRUCTION>
Continuando desde la sesión anterior. El usuario ha estado trabajando en el proyecto con las actividades mostradas arriba.
Mantén coherencia con el trabajo previo y referencia estos archivos y comandos cuando sea relevante.
</CONTEXT_INSTRUCTION>
</SUPERVISOR_CONTEXT>
"""

        return context.strip()


# Función principal para inicializar agente
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
        "config": config
    }


if __name__ == "__main__":
    # Ejemplo de uso
    setup = setup_claude_agent(
        project_name="Marketing SDK",
        project_path="/media/eduardo/56087475087455C9/Dev/Python/marketing_sdk",
        system_prompt="Especialista en desarrollo de SDKs de marketing"
    )

    print(f"Sesión creada: {setup['session_id']}")