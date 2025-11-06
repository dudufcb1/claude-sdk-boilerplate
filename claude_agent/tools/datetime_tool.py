"""
Datetime Tool - Tool de ejemplo (no-MCP) para el boilerplate

Expone una tool simple para devolver la fecha/hora actual. Útil como
plantilla/ejemplo de Tool del SDK (Anthropic Tools API), NO un MCP server.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, Any


CURRENT_DATETIME_TOOL: Dict[str, Any] = {
    "name": "current_datetime",
    "description": (
        "Devuelve la fecha y hora actuales. Úsala para contextualizar tiempo y "
        "zona horaria. No requiere parámetros, pero acepta un 'format' opcional: "
        "'iso' (local, default), 'iso_utc', 'unix', 'human'."
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


def _now_iso_local() -> str:
    return datetime.now().astimezone().isoformat()


def _now_iso_utc() -> str:
    # ISO 8601 con 'Z' al final
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _now_unix() -> str:
    return str(int(datetime.now().timestamp()))


def _now_human() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


_FORMAT_MAP = {
    "iso": _now_iso_local,
    "iso_utc": _now_iso_utc,
    "unix": _now_unix,
    "human": _now_human,
}


def execute_current_datetime(tool_input: Dict[str, Any] | None = None) -> str:
    """Ejecutor de la tool 'current_datetime'.

    Devuelve SIEMPRE un string (JSON serializado), conforme a la guía de tools.
    Estructura:
    {
      "success": true,
      "now": "...",
      "format": "iso|iso_utc|unix|human"
    }
    """
    fmt = "iso"
    if isinstance(tool_input, dict) and isinstance(tool_input.get("format"), str):
        if tool_input["format"] in _FORMAT_MAP:
            fmt = tool_input["format"]

    try:
        value = _FORMAT_MAP[fmt]()
        return json.dumps({"success": True, "now": value, "format": fmt})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
