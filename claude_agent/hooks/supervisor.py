"""
Supervisor Hook - Hook para supervisor automático
"""

from pathlib import Path
from datetime import datetime
from typing import Optional


class SupervisorHook:
    """Hook para supervisor automático"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_path = Path("sessions") / session_id

        # Crear directorios necesarios
        self.session_path.mkdir(parents=True, exist_ok=True)
        (self.session_path / "supervisor_logs").mkdir(exist_ok=True)

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

    def load_supervisor_context(self) -> Optional[str]:
        """Carga contexto del supervisor previo"""
        supervisor_file = self.session_path / "last_supervisor.txt"

        if supervisor_file.exists():
            try:
                content = supervisor_file.read_text()
                print(f"✅ Supervisor cargado desde sesión previa: {len(content)} caracteres")
                return content
            except Exception as e:
                print(f"⚠️  Error cargando supervisor: {e}")

        return None

    def save_supervisor_context(self, context: str):
        """Guarda contexto del supervisor"""
        supervisor_file = self.session_path / "last_supervisor.txt"
        try:
            supervisor_file.write_text(context)
            print(f"✅ Supervisor guardado: {len(context)} caracteres")
        except Exception as e:
            print(f"⚠️  Error guardando supervisor: {e}")

    def _analyze_transcript(self, transcript: str) -> str:
        """Analiza transcript y genera contexto del supervisor"""

        # Análisis básico del transcript
        lines = transcript.split('\n')
        user_messages = [line for line in lines if line.startswith('Human:')]
        assistant_messages = [line for line in lines if line.startswith('Assistant:')]

        # Detectar patrones
        files_mentioned = []
        commands_run = []
        errors_found = []

        for line in lines:
            line_lower = line.lower()

            # Detectar archivos
            if any(ext in line for ext in ['.py', '.js', '.json', '.md', '.txt', '.yml', '.yaml']):
                files_mentioned.append(line.strip()[:100])

            # Detectar comandos
            if any(cmd in line_lower for cmd in ['bash', 'command', 'run', 'execute']):
                commands_run.append(line.strip()[:100])

            # Detectar errores
            if any(error in line_lower for error in ['error', 'failed', 'exception', 'traceback']):
                errors_found.append(line.strip()[:100])

        # Generar contexto estructurado
        context = f"""
<SUPERVISOR_CONTEXT session="{self.session_id}" generated="{datetime.now().isoformat()}">

<SESSION_SUMMARY>
- Total de líneas analizadas: {len(lines)}
- Mensajes del usuario: {len(user_messages)}
- Respuestas del asistente: {len(assistant_messages)}
- Archivos mencionados: {len(files_mentioned)}
- Comandos ejecutados: {len(commands_run)}
- Errores detectados: {len(errors_found)}
</SESSION_SUMMARY>

<KEY_USER_ACTIVITIES>
{chr(10).join(f"- {msg[:150]}..." for msg in user_messages[-5:] if msg.strip())}
</KEY_USER_ACTIVITIES>

<FILES_WORKED_ON>
{chr(10).join(f"- {file}" for file in files_mentioned[-10:] if file.strip())}
</FILES_WORKED_ON>

<RECENT_COMMANDS>
{chr(10).join(f"- {cmd}" for cmd in commands_run[-5:] if cmd.strip())}
</RECENT_COMMANDS>

{f'''<ERRORS_ENCOUNTERED>
{chr(10).join(f"- {error}" for error in errors_found[-3:] if error.strip())}
</ERRORS_ENCOUNTERED>''' if errors_found else ''}

<CONTEXT_INSTRUCTION>
Esta es la continuación de una sesión anterior. El usuario ha estado trabajando en:

1. ARCHIVOS: {len(files_mentioned)} archivos mencionados/modificados
2. COMANDOS: {len(commands_run)} comandos ejecutados
3. CONVERSACIÓN: {len(user_messages)} intercambios con el usuario
{f"4. ERRORES: Se encontraron {len(errors_found)} errores que pueden necesitar seguimiento" if errors_found else ""}

Mantén coherencia con el trabajo previo. Haz referencia a estos archivos y comandos cuando sea relevante.
El usuario espera que recuerdes el contexto de esta sesión y continues desde donde se quedó.
</CONTEXT_INSTRUCTION>

</SUPERVISOR_CONTEXT>
"""

        return context.strip()

    def get_supervisor_stats(self) -> dict:
        """Obtiene estadísticas del supervisor"""
        supervisor_file = self.session_path / "last_supervisor.txt"
        logs_dir = self.session_path / "supervisor_logs"

        stats = {
            "session_id": self.session_id,
            "has_current_supervisor": supervisor_file.exists(),
            "supervisor_size": supervisor_file.stat().st_size if supervisor_file.exists() else 0,
            "total_supervisor_logs": len(list(logs_dir.glob("*.txt"))) if logs_dir.exists() else 0
        }

        if supervisor_file.exists():
            stats["last_updated"] = datetime.fromtimestamp(supervisor_file.stat().st_mtime).isoformat()

        return stats