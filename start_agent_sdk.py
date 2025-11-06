#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDK Runner (sin Claude Code) - Chat con tools definidas por el proyecto
- Usa Anthropic Python SDK directamente (messages.create)
- Permite pasar tools=[...] y manejar ToolUseBlocks manualmente
- Incluye tool de ejemplo: current_datetime
"""

from __future__ import annotations

import argparse
import os
import json
from pathlib import Path
from typing import Any, Dict, List

from anthropic import Anthropic

# Reusar la tool de ejemplo del boilerplate
from claude_agent.tools.datetime_tool import CURRENT_DATETIME_TOOL, execute_current_datetime


def load_env_from_settings(settings_path: str | None) -> Dict[str, str]:
    env_vars: Dict[str, str] = {}
    try:
        path = None
        if settings_path:
            path = Path(settings_path).expanduser()
        else:
            # Prefer ~/.claude-sdk/settings.json si existe
            home_sdk = Path.home() / ".claude-sdk" / "settings.json"
            fallback = Path.home() / ".claude" / "settings.json"
            path = home_sdk if home_sdk.exists() else fallback
        if path and path.exists():
            data = json.loads(path.read_text())
            candidate = data.get("env") if isinstance(data, dict) else None
            if isinstance(candidate, dict):
                for k, v in candidate.items():
                    if isinstance(v, (str, int, float, bool)):
                        env_vars[k] = str(v)
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
    except Exception:
        pass
    # Mapear AUTH_TOKEN → API_KEY si hace falta
    if "ANTHROPIC_API_KEY" not in env_vars and "ANTHROPIC_AUTH_TOKEN" in env_vars:
        env_vars["ANTHROPIC_API_KEY"] = env_vars["ANTHROPIC_AUTH_TOKEN"]
    return env_vars


def get_model(env_vars: Dict[str, str]) -> str:
    # Elegir modelo por prioridad: SONNET > HAIKU > OPUS > default
    return (
        env_vars.get("ANTHROPIC_DEFAULT_SONNET_MODEL")
        or env_vars.get("ANTHROPIC_DEFAULT_HAIKU_MODEL")
        or env_vars.get("ANTHROPIC_DEFAULT_OPUS_MODEL")
        or "gpt-4.1"
    )


def get_anthropic_client(env_vars: Dict[str, str]) -> Anthropic:
    client_params: Dict[str, Any] = {}
    if env_vars.get("ANTHROPIC_API_KEY"):
        client_params["api_key"] = env_vars["ANTHROPIC_API_KEY"]
    if env_vars.get("ANTHROPIC_BASE_URL"):
        client_params["base_url"] = env_vars["ANTHROPIC_BASE_URL"]
    return Anthropic(**client_params)


# Tools del proyecto (mínimo viable)
TOOLS: List[Dict[str, Any]] = [CURRENT_DATETIME_TOOL]


def execute_tool(tool_name: str, tool_input: Dict[str, Any] | None) -> str:
    if tool_name == CURRENT_DATETIME_TOOL["name"]:
        return execute_current_datetime(tool_input or {})
    # Extiende aquí con nuevas tools
    return json.dumps({"success": False, "error": f"Tool desconocida: {tool_name}"})


def extract_text(content_blocks: list[Any]) -> str:
    out = []
    for block in content_blocks or []:
        text = getattr(block, "text", None)
        if text:
            out.append(text)
    return "".join(out)


def run_chat(settings_path: str | None, cwd: str | None, verbose: bool) -> None:
    env_vars = load_env_from_settings(settings_path)
    client = get_anthropic_client(env_vars)
    model = get_model(env_vars)

    if verbose:
        masked = {k: ("***" if "KEY" in k or "TOKEN" in k else v) for k, v in env_vars.items()}
        print(f"🧩 ENV: {masked}")
        print(f"🧪 Modelo: {model}")
        print(f"📂 CWD: {cwd or os.getcwd()}")

    messages: List[Dict[str, Any]] = []

    while True:
        try:
            user_in = input("🧑 [sdk] > ").strip()
            if not user_in:
                continue
            if user_in.lower() in {"exit", "quit"}:
                print("👋 Bye")
                break

            # Agregar mensaje del usuario
            messages.append({"role": "user", "content": user_in})

            # Primer turno: Claude decide si usar tools
            resp = client.messages.create(
                model=model,
                max_tokens=1024,
                messages=messages,
                tools=TOOLS,
                # tool_choice={"type": "auto"}  # default
            )

            # Procesar bloques
            tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
            assistant_text = extract_text(resp.content)
            if assistant_text:
                print(f"🤖 {assistant_text}")

            if not tool_uses:
                # No hay tools; seguimos
                messages.append({"role": "assistant", "content": resp.content})
                continue

            # Hay ToolUse: añadir respuesta del asistente tal cual
            messages.append({"role": "assistant", "content": resp.content})

            # Ejecutar tools y preparar tool_result
            tool_results = []
            for tu in tool_uses:
                tname = getattr(tu, "name", "<unknown>")
                tinp = getattr(tu, "input", {})
                if verbose:
                    print(f"🛠️ ToolUse: {tname} input={tinp}")
                result_str = execute_tool(tname, tinp if isinstance(tinp, dict) else {})
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": getattr(tu, "id", None),
                    "content": result_str,
                })

            # Devolver los tool_result al modelo
            messages.append({"role": "user", "content": tool_results})

            # Segundo turno: respuesta final tras tool_result
            resp2 = client.messages.create(
                model=model,
                max_tokens=1024,
                messages=messages,
                tools=TOOLS,
            )
            assistant_text2 = extract_text(resp2.content)
            if assistant_text2:
                print(f"🤖 {assistant_text2}")
            messages.append({"role": "assistant", "content": resp2.content})

        except KeyboardInterrupt:
            print("\n👋 Bye")
            break
        except Exception as e:
            print(f"❌ Error en chat: {e}")


def main():
    parser = argparse.ArgumentParser(description="SDK Runner (Anthropic) con tools del proyecto")
    parser.add_argument("--settings", help="Ruta de settings.json (opcional)")
    parser.add_argument("--cwd", help="CWD lógico para contexto (opcional)")
    parser.add_argument("--verbose", action="store_true", help="Logs detallados")
    args = parser.parse_args()

    if args.cwd:
        try:
            os.chdir(args.cwd)
        except Exception as e:
            print(f"⚠️ No se pudo cambiar CWD: {e}")

    run_chat(args.settings, args.cwd, args.verbose)


if __name__ == "__main__":
    main()
