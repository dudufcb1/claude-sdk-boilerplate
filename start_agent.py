#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# IMPORTANTE: Ejecutar con: source .venv/bin/activate && python start_agent.py
"""
Claude Agent CLI - Chat interactivo con agente Claude
Uso: python start_agent.py /ruta/del/proyecto
"""

import argparse
import asyncio
import json
import os
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Importar configuración de agente
from claude_agent import setup_claude_agent
from claude_agent.core.session_tracker import SessionTracker
from claude_agent.hooks.supervisor import SupervisorHook

# SDK de Claude
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, HookMatcher
from claude_agent_sdk.types import AssistantMessage, TextBlock, ToolUseBlock


class ClaudeAgentCLI:
    """CLI completo de agente Claude con chat interactivo"""

    def __init__(self, project_path: str, system_prompt: Optional[str] = None, settings_path: Optional[str] = None, no_hooks: bool = False, verbose: bool = False):
        self.project_path = Path(project_path).resolve()
        self.project_name = self.project_path.name
        self.no_hooks = no_hooks
        self.verbose = verbose
        # Ruta de settings (proxy Claude Code) priorizando .claude-sdk del proyecto
        if settings_path:
            self.settings_path = Path(settings_path).expanduser().resolve()
        else:
            project_sdk_settings = self.project_path / ".claude-sdk" / "settings.json"
            home_sdk_settings = Path.home() / ".claude-sdk" / "settings.json"
            if project_sdk_settings.exists():
                self.settings_path = project_sdk_settings
            elif home_sdk_settings.exists():
                self.settings_path = home_sdk_settings
            else:
                self.settings_path = Path.home() / ".claude" / "settings.json"

        # Configurar agente
        setup = setup_claude_agent(
            project_name=self.project_name,
            project_path=str(self.project_path),
            system_prompt=system_prompt
        )

        self.session_id = setup['session_id']
        self.agent_options = setup['agent_options']
        self.tracker = SessionTracker(self.session_id, str(self.project_path))
        self.supervisor = SupervisorHook(self.session_id)

        # Cliente SDK
        self.client = None
        self.connected = False
        # Control de logs de sistema
        self._printed_init = False
        # Evento de readiness (init)
        self._init_event = asyncio.Event()
        # Evento de respuesta a una query
        self._response_event = asyncio.Event()
        # Evento de fin de turno
        self._turn_event = asyncio.Event()
        # Último timestamp de mensaje
        self._last_message_at = 0.0

    def load_system_prompt(self) -> Optional[str]:
        """Carga system prompt desde archivo prompt.txt"""
        prompt_file = Path("prompt.txt")

        if prompt_file.exists():
            try:
                prompt = prompt_file.read_text(encoding='utf-8').strip()
                print(f"📄 System prompt cargado desde: {prompt_file}")
                return prompt
            except Exception as e:
                print(f"⚠️ Error leyendo prompt.txt: {e}")
        else:
            print("📄 No se encontró prompt.txt, usando prompt por defecto")

        return None

    def _load_env_from_settings(self) -> Dict[str, str]:
        """Carga variables de entorno relevantes desde settings.json.
        Soporta dos formatos:
        - {"env": {"ANTHROPIC_API_KEY": "...", "ANTHROPIC_BASE_URL": "..."}}
        - {"ANTHROPIC_API_KEY": "...", "ANTHROPIC_BASE_URL": "..."}
        """
        env_vars: Dict[str, str] = {}
        try:
            if not self.settings_path or not Path(self.settings_path).exists():
                return env_vars
            data = json.loads(Path(self.settings_path).read_text())
            # Preferir bloque 'env'
            candidate = data.get("env") if isinstance(data, dict) else None
            if isinstance(candidate, dict):
                for k, v in candidate.items():
                    if isinstance(v, (str, int, float, bool)):
                        env_vars[k] = str(v)
            # Además, tomar claves conocidas en top-level si existen
            for k in [
                "ANTHROPIC_API_KEY",
                "ANTHROPIC_AUTH_TOKEN",
                "ANTHROPIC_BASE_URL",
                "API_TIMEOUT_MS",
                "ANTHROPIC_DEFAULT_HAIKU_MODEL",
                "ANTHROPIC_DEFAULT_SONNET_MODEL",
                "ANTHROPIC_DEFAULT_OPUS_MODEL",
            ]:
                if isinstance(data, dict) and k in data and k not in env_vars:
                    val = data[k]
                    if isinstance(val, (str, int, float, bool)):
                        env_vars[k] = str(val)
        except Exception as e:
            if self.verbose:
                print(f"⚠️ No se pudieron cargar env desde settings: {e}")
        # Compat: si sólo viene ANTHROPIC_AUTH_TOKEN, mapear a ANTHROPIC_API_KEY
        if "ANTHROPIC_API_KEY" not in env_vars and "ANTHROPIC_AUTH_TOKEN" in env_vars:
            env_vars["ANTHROPIC_API_KEY"] = env_vars["ANTHROPIC_AUTH_TOKEN"]
        return env_vars

    async def _wait_quiet(self, quiet_sec: float = 0.3, overall_timeout: float = 2.0):
        """Espera a que no lleguen mensajes durante quiet_sec (con timeout total)."""
        start = time.monotonic()
        last = self._last_message_at
        while time.monotonic() - start < overall_timeout:
            await asyncio.sleep(0.05)
            # si hubo nueva actividad, reiniciar ventana de quiet
            if self._last_message_at != last:
                last = self._last_message_at
            # ventana quiet alcanzada
            if last and (time.monotonic() - last) >= quiet_sec:
                return True
        return False

    async def connect_agent(self):
        """Conecta el agente Claude SDK"""
        try:
            print("🔗 Conectando agente Claude...")

            # Crear tracking hook con debug
            def tracking_hook(tool_name: str, args: dict, result: Any):
                print(f"📊 HOOK: Tool usada: {tool_name}")
                if args and len(str(args)) < 200:
                    print(f"   Args: {args}")
                self.tracker.track_tool_use_hook(tool_name, args, result)

            # Cargar variables de entorno desde settings.json si existen
            env_vars = self._load_env_from_settings()
            if self.verbose and env_vars:
                masked = {k: ("***" if "KEY" in k or "TOKEN" in k else v) for k, v in env_vars.items()}
                print(f"🧩 ENV desde settings: {masked}")

            # Configurar opciones del SDK
            hooks_cfg = {}
            if not self.no_hooks:
                hooks_cfg = {
                    "PreCompact": [HookMatcher(matcher=None, hooks=[self.supervisor.pre_compact_hook])],
                    "PostToolUse": [HookMatcher(matcher=None, hooks=[tracking_hook])]
                }

            # Inyectar definición de tool de ejemplo (no-MCP)
            example_tools = [
                {
                    "name": "current_datetime",
                    "description": (
                        "Devuelve la fecha/hora actuales. Úsala para contextualizar tiempo. "
                        "Acepta un parámetro opcional 'format': 'iso'|'iso_utc'|'unix'|'human'."
                    ),
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "format": {
                                "type": "string",
                                "enum": ["iso", "iso_utc", "unix", "human"],
                                "description": "Formato opcional del resultado"
                            }
                        }
                    }
                }
            ]

            options = ClaudeAgentOptions(
                system_prompt=self.agent_options['system_prompt'],
                cwd=str(self.project_path),
                allowed_tools=self.agent_options['allowed_tools'],
                permission_mode=self.agent_options['permission_mode'],
                mcp_servers=self.agent_options['mcp_servers'],
                hooks=hooks_cfg,
                settings=str(self.settings_path),  # ajustes CLI
                env=env_vars,  # credenciales/base url para CLI
                continue_conversation=True,
            )

            # Crear y conectar cliente SDK
            self.client = ClaudeSDKClient(options=options)
            await self.client.connect()
            self.connected = True
            # Considerar conectado == listo para enviar queries (handshake interno completo)
            try:
                self._init_event.set()
            except Exception:
                pass

            if self.verbose:
                print("✅ Agente Claude conectado y listo")
            else:
                print("✅ Agente Claude conectado y listo")

        except Exception as e:
            print(f"❌ Error conectando agente: {e}")
            raise

    async def _handle_message(self, message):
        """Maneja mensajes del agente Claude SDK"""
        try:
            if self.verbose:
                print(f"🔍 DEBUG: Mensaje recibido tipo: {type(message)}")

            # Caso 1: AssistantMessage (respuestas normales con bloques)
            if isinstance(message, AssistantMessage):
                response_text = ""
                content = getattr(message, "content", [])

                if self.verbose:
                    try:
                        print(f"📥 {type(message).__name__} con {len(content)} bloques")
                    except Exception:
                        pass

                for block in content:
                    # Bloques de pensamiento internos
                    if hasattr(block, "thinking") or getattr(block, "type", "") == "thinking":
                        if self.verbose:
                            think = getattr(block, "thinking", None)
                            if think:
                                preview = think[:120].replace("\n", " ")
                                print(f"🧠 thinking[{len(think)}]: {preview}...")
                            else:
                                print("🧠 thinking block")
                        continue

                    # Bloques de texto
                    if isinstance(block, TextBlock) or hasattr(block, "text"):
                        text = getattr(block, "text", "")
                        if text:
                            response_text += text
                            print(f"🤖 {text}")
                    # Uso de herramientas
                    elif isinstance(block, ToolUseBlock) or getattr(block, "type", "") == "tool_use":
                        tool_name = getattr(block, "name", "<unknown>")
                        tool_input = getattr(block, "input", None)
                        print(f"🛠️ Tool: {tool_name}")
                        if tool_input is not None and len(str(tool_input)) < 150:
                            print(f"   └─ Args: {tool_input}")
                    # Resultado de herramienta
                    elif getattr(block, "type", "") == "tool_result" or block.__class__.__name__ == "ToolResultBlock" or (hasattr(block, "tool_use_id") and hasattr(block, "content")):
                        result = getattr(block, "content", None)
                        if result is not None:
                            preview = str(result)
                            if len(preview) > 1200:
                                preview = preview[:1200] + "..."
                            print(f"🧪 Tool result:\n{preview}")
                    else:
                        # Fallback: bloque desconocido (silencioso excepto en verbose)
                        if self.verbose:
                            print(f"🔎 Bloque no reconocido: {block}")
                        continue

                # Registrar respuesta completa
                if response_text:
                    self.tracker.add_agent_message(response_text)
                    print(f"📊 Respuesta registrada: {len(response_text)} caracteres")
                    try:
                        self._response_event.set()
                    except Exception:
                        pass
                else:
                    if self.verbose:
                        print("⚠️ No se encontró texto en la respuesta")

            # Caso 1b: Mensajes con 'content' que no son AssistantMessage (p.ej. ToolResult en otros envoltorios)
            elif hasattr(message, "content"):
                content = getattr(message, "content", [])
                if self.verbose:
                    try:
                        print(f"📥 {type(message).__name__} con {len(content)} bloques")
                    except Exception:
                        pass
                for block in content:
                    if getattr(block, "type", "") == "tool_result" or block.__class__.__name__ == "ToolResultBlock" or (hasattr(block, "tool_use_id") and hasattr(block, "content")):
                        result = getattr(block, "content", None)
                        if result is not None:
                            preview = str(result)
                            if len(preview) > 1200:
                                preview = preview[:1200] + "..."
                            print(f"🧪 Tool result:\n{preview}")
                            try:
                                self._response_event.set()
                            except Exception:
                                pass
                    elif isinstance(block, TextBlock) or hasattr(block, "text"):
                        text = getattr(block, "text", "")
                        if text:
                            print(f"🤖 {text}")
                            try:
                                self._response_event.set()
                            except Exception:
                                pass
                    elif isinstance(block, ToolUseBlock) or getattr(block, "type", "") == "tool_use":
                        tool_name = getattr(block, "name", "<unknown>")
                        print(f"🛠️ Tool: {tool_name}")

            # Caso 2: mensajes de sistema u otros (mostrar para debug)
            elif hasattr(message, "subtype"):
                subtype = getattr(message, "subtype", "<sin-subtipo>")
                # Mostrar 'init' una sola vez por defecto; en verbose, incluir data
                if subtype == "init":
                    if not self._printed_init:
                        self._printed_init = True
                        if self.verbose:
                            data = getattr(message, "data", None)
                            print(f"[SystemMsg]: init - {data}")
                        else:
                            print("[SystemMsg]: init")
                        # marcar agente listo
                        try:
                            self._init_event.set()
                        except Exception:
                            pass
                elif subtype == "success":
                    if self.verbose:
                        print("[SystemMsg]: success")
                    try:
                        self._turn_event.set()
                    except Exception:
                        pass
                else:
                    if self.verbose:
                        print(f"[SystemMsg]: {subtype}")

            else:
                # Fallback genérico
                # Detectar ResultMessage como fin de turno
                if message.__class__.__name__ == "ResultMessage":
                    if self.verbose:
                        print("[ResultMessage]: end-of-turn signal")
                    try:
                        self._turn_event.set()
                    except Exception:
                        pass
                else:
                    print(f"🔎 Mensaje no reconocido: {message}")

        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
            import traceback
            traceback.print_exc()

    def print_welcome(self):
        """Mensaje de bienvenida"""
        print("\n" + "="*60)
        print("💬 CLAUDE AGENT - CHAT INTERACTIVO")
        print("="*60)
        print(f"📁 Proyecto: {self.project_name}")
        print(f"📂 Path: {self.project_path}")
        print(f"🆔 Sesión: {self.session_id}")
        print(f"🛠️ Tools: {', '.join(self.agent_options['allowed_tools'])}")
        print(f"🔌 MCPs: {len(self.agent_options['mcp_servers'])}")
        # Mostrar settings path efectivo
        try:
            print(f"⚙️ Settings: {self.settings_path}")
            if self.verbose:
                print("🪪 Verbose: ON")
        except Exception:
            pass
        print("="*60)
        print("Comandos: 'exit', 'status', 'save', 'cancel'")
        print("="*60)
        print()

    async def _listen_for_messages(self):
        """Escucha mensajes del agente en background"""
        try:
            print("🔍 DEBUG: Iniciando listener de mensajes...")
            async for message in self.client.receive_messages():
                print(f"🔍 DEBUG: ¡Mensaje recibido en listener!")
                self._last_message_at = time.monotonic()
                await self._handle_message(message)
        except asyncio.CancelledError:
            print("🔍 DEBUG: Listener cancelado")
        except Exception as e:
            print(f"❌ Error escuchando mensajes: {e}")
            import traceback
            traceback.print_exc()

    async def run_chat(self):
        """Ejecuta el chat interactivo"""

        # Conectar agente
        await self.connect_agent()
        self.print_welcome()

        # Iniciar listener de mensajes en background
        message_task = asyncio.create_task(self._listen_for_messages())
        # Ceder el control para permitir que el listener arranque antes del input/envío
        await asyncio.sleep(0)

        # Esperar readiness (conectado == listo por diseño del SDK)
        if self.verbose:
            print("⏳ Esperando inicialización (init) del agente...")
        try:
            await self._init_event.wait()
            if self.verbose:
                print("✅ Agente listo (init recibido)\n")
        except Exception:
            # En caso de error no esperado, continuar igualmente
            if self.verbose:
                print("⚠️ No se pudo confirmar init; continuando bajo riesgo")

        try:
            while True:
                try:
                    # Input del usuario
                    user_input = input(f"🧑 [{self.session_id[:8]}] > ").strip()

                    if not user_input:
                        continue

                    # Comandos especiales
                    if user_input.lower() in ['exit', 'quit']:
                        print("👋 Guardando sesión y saliendo...")
                        message_task.cancel()
                        await self.disconnect_agent()
                        self.save_session()
                        break

                    elif user_input.lower() == 'status':
                        self.show_status()
                        continue

                    elif user_input.lower() == 'save':
                        self.save_supervisor_context()
                        continue

                    elif user_input.lower() == 'cancel':
                        print("🛑 Cancelando operación...")
                        await self.client.interrupt()
                        continue

                    if not self.connected:
                        print("❌ Agente no conectado")
                        continue

                    # Asegurar readiness si por alguna razón no se ha marcado aún
                    if not self._init_event.is_set():
                        if self.verbose:
                            print("⏳ Aguardando init antes de enviar...")
                        await self._init_event.wait()

                    # Registrar mensaje del usuario
                    self.tracker.add_user_message(user_input)

                    # Enviar a Claude SDK real
                    print("🤖 Claude está procesando...")

                    # Debug del envío
                    print(f"🔍 DEBUG: Enviando a sesión {self.session_id}")

                    # Enviar query y bloquear prompt hasta fin de turno + quiet period
                    self._response_event.clear()
                    self._turn_event.clear()
                    await self.client.query(user_input)

                    print("🔍 DEBUG: Mensaje enviado, esperando respuesta...")

                    # Esperar señal de fin de turno (ResultMessage o System:success)
                    try:
                        await asyncio.wait_for(self._turn_event.wait(), timeout=15.0)
                    except asyncio.TimeoutError:
                        if self.verbose:
                            print("⏱️ Timeout esperando fin de turno (Result/Success)")
                    # Esperar quiet period para drenar mensajes rezagados
                    await self._wait_quiet(quiet_sec=0.4, overall_timeout=3.0)
                    print()

                except KeyboardInterrupt:
                    print("\n👋 Sesión interrumpida. Guardando...")
                    message_task.cancel()
                    if self.connected:
                        await self.disconnect_agent()
                    self.save_session()
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")

        except Exception as e:
            print(f"💥 Error fatal en chat: {e}")
        finally:
            if not message_task.cancelled():
                message_task.cancel()

    async def disconnect_agent(self):
        """Desconecta el agente Claude"""
        if self.client and self.connected:
            try:
                await self.client.disconnect()
                self.connected = False
                print("🔌 Agente desconectado")
            except Exception as e:
                print(f"⚠️ Error desconectando: {e}")

    def show_status(self):
        """Muestra estado de la sesión"""
        audit_summary = self.tracker.get_audit_summary()
        supervisor_stats = self.supervisor.get_supervisor_stats()

        print("\n📊 ESTADO DE LA SESIÓN")
        print("-" * 30)
        print(f"Sesión: {audit_summary['session_id']}")
        print(f"Mensajes: {audit_summary['total_messages']}")
        print(f"Tools usadas: {audit_summary['total_tools_used']}")
        print(f"Archivos creados: {audit_summary['total_files_created']}")
        print(f"Archivos modificados: {audit_summary['total_files_modified']}")
        print(f"Supervisor: {'✅' if supervisor_stats['has_current_supervisor'] else '❌'}")
        print("-" * 30)

    def save_supervisor_context(self):
        """Guarda contexto del supervisor manualmente"""
        # Simular transcript de la conversación
        user_msgs = [m['message'] for m in self.tracker.audit_data['user_messages'][-5:]]
        agent_msgs = [m['message'] for m in self.tracker.audit_data['agent_messages'][-5:]]

        transcript_lines = []
        for msg in user_msgs:
            transcript_lines.append(f"Human: {msg}")
        for msg in agent_msgs:
            transcript_lines.append(f"Assistant: {msg}")

        transcript = "\n".join(transcript_lines)
        context = self.supervisor.pre_compact_hook(transcript)
        print("💾 Contexto del supervisor guardado")

    def save_session(self):
        """Guarda estado de la sesión al salir"""
        self.save_supervisor_context()
        print(f"✅ Sesión guardada: sessions/{self.session_id}/")


def _iter_project_sessions(project_name: str):
    sessions_dir = Path("sessions")
    if not sessions_dir.exists():
        return []
    prefix = project_name.lower().replace(' ', '-') + "-"
    return [p for p in sessions_dir.glob(prefix + "*") if p.is_dir()]


def purge_project_sessions(project_name: str):
    """Elimina todas las sesiones previas de un proyecto."""
    for p in _iter_project_sessions(project_name):
        shutil.rmtree(p, ignore_errors=True)


def _load_latest_audit_for_project(project_name: str) -> Optional[Dict[str, Any]]:
    latest = None
    latest_mtime = -1.0
    for sess in _iter_project_sessions(project_name):
        audit = sess / "audit.json"
        if audit.exists():
            mtime = audit.stat().st_mtime
            if mtime > latest_mtime:
                try:
                    data = json.loads(audit.read_text())
                    latest = data
                    latest_mtime = mtime
                except Exception:
                    continue
    return latest


def _build_transcript_from_audit(audit: Dict[str, Any]) -> str:
    """Construye transcript ordenado por timestamp de user/agent messages."""
    msgs = []
    for m in audit.get("user_messages", []):
        msgs.append((m.get("timestamp", ""), f"Human: {m.get('message','')}"))
    for m in audit.get("agent_messages", []):
        msgs.append((m.get("timestamp", ""), f"Assistant: {m.get('message','')}"))
    # ordenar por timestamp ISO
    try:
        msgs.sort(key=lambda x: x[0])
    except Exception:
        pass
    return "\n".join(text for _, text in msgs)


def generate_condensed_supervisor(project_name: str) -> Optional[str]:
    audit = _load_latest_audit_for_project(project_name)
    if not audit:
        return None
    transcript = _build_transcript_from_audit(audit)
    try:
        sup = SupervisorHook(audit.get("session_id", project_name))
        context = sup.pre_compact_hook(transcript)
        return context
    except Exception:
        return None


def main():
    """Función principal del CLI"""

    parser = argparse.ArgumentParser(
        description="Claude Agent CLI - Chat interactivo con agente Claude",
        epilog="Ejemplo: python start_agent.py /ruta/al/proyecto"
    )

    parser.add_argument('project_path', help='Ruta del proyecto')
    parser.add_argument('--settings', dest='settings_path', help='Ruta de settings.json (proxy Claude Code). Default: <proyecto>/.claude-sdk/settings.json o ~/.claude/settings.json')
    parser.add_argument('--no-hooks', action='store_true', help='Deshabilita hooks (PreCompact/PostToolUse) para evitar aborts durante debug')
    parser.add_argument('--verbose', action='store_true', help='Habilita logs detallados (init completo, thinking preview, tipos de bloques)')
    parser.add_argument('--new-session', action='store_true', help='Eliminar sesiones previas del proyecto y comenzar con contexto limpio')
    parser.add_argument('--condense', action='store_true', help='Condensar la última sesión en un supervisor e inyectarlo en el system prompt de una nueva sesión')
    args = parser.parse_args()

    # Validar ruta
    if not os.path.exists(args.project_path):
        print(f"❌ Error: La ruta {args.project_path} no existe")
        sys.exit(1)

    project_name = Path(args.project_path).resolve().name

    # Preparar prompt final (condense + prompt.txt si existe)
    condensed = generate_condensed_supervisor(project_name) if args.condense else None

    # Crear CLI temporal para leer prompt.txt (sin conectar)
    cli_tmp = ClaudeAgentCLI(args.project_path, settings_path=args.settings_path, no_hooks=args.no_hooks, verbose=args.verbose)
    custom_prompt = cli_tmp.load_system_prompt()

    final_prompt = None
    if condensed and custom_prompt:
        final_prompt = f"{condensed}\n\n{custom_prompt}".strip()
    elif condensed:
        final_prompt = condensed
    elif custom_prompt:
        final_prompt = custom_prompt

    # Purga de sesiones previas si se solicita
    if args.new_session:
        purge_project_sessions(project_name)
        print(f"🧹 Sesiones previas de '{project_name}' eliminadas")

    # Crear CLI definitivo con el prompt calculado
    cli = ClaudeAgentCLI(args.project_path, final_prompt, settings_path=args.settings_path, no_hooks=args.no_hooks, verbose=args.verbose)

    # Ejecutar chat
    try:
        asyncio.run(cli.run_chat())
    except KeyboardInterrupt:
        print("\n👋 Adiós!")
    except Exception as e:
        print(f"💥 Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()