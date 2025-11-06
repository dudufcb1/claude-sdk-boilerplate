"""
Session Tracker - Tracking de sesión en tiempo real
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class SessionTracker:
    """Tracker de sesión en tiempo real"""

    def __init__(self, session_id: str, cwd: str):
        self.session_id = session_id
        self.cwd = cwd
        self.session_path = Path("sessions") / session_id
        self.audit_file = self.session_path / "audit.json"

        # Crear directorio si no existe
        self.session_path.mkdir(parents=True, exist_ok=True)

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

    def get_audit_summary(self) -> Dict[str, Any]:
        """Obtiene resumen del audit"""
        return {
            "session_id": self.session_id,
            "total_messages": len(self.audit_data["user_messages"]) + len(self.audit_data["agent_messages"]),
            "total_files_created": len(self.audit_data["files_created"]),
            "total_files_modified": len(self.audit_data["files_modified"]),
            "total_tools_used": sum(self.audit_data["tools_used"].values()),
            "tools_breakdown": self.audit_data["tools_used"].copy()
        }

    def _save_audit(self):
        """Guarda audit data"""
        try:
            with open(self.audit_file, 'w') as f:
                json.dump(self.audit_data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error guardando audit: {e}")

    def load_existing_audit(self) -> bool:
        """Carga audit existente si existe"""
        if self.audit_file.exists():
            try:
                with open(self.audit_file, 'r') as f:
                    self.audit_data = json.load(f)
                print(f"✅ Audit existente cargado: {len(self.audit_data.get('user_messages', []))} mensajes")
                return True
            except Exception as e:
                print(f"⚠️  Error cargando audit existente: {e}")
        return False