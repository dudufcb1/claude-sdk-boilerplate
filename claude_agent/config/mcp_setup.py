"""
MCP Configuration Setup - Configurador automático de MCPs para Claude
"""

import json
from pathlib import Path
from typing import Dict, Any


def get_claude_mcp_config() -> Dict[str, Any]:
    """Carga automática de MCPs desde ~/.claude.json"""
    claude_config_path = Path.home() / ".claude.json"

    if not claude_config_path.exists():
        print("⚠️  ~/.claude.json no encontrado. Usa setup_claude_mcp_config() para crear configuración básica")
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


def setup_claude_mcp_config(force: bool = False) -> bool:
    """
    Crea configuración MCP básica si no existe

    Args:
        force: Si True, sobrescribe configuración existente

    Returns:
        True si se creó/actualizó la configuración
    """
    claude_config_path = Path.home() / ".claude.json"

    if claude_config_path.exists() and not force:
        print(f"✅ ~/.claude.json ya existe en: {claude_config_path}")
        print("   Usa setup_claude_mcp_config(force=True) para sobrescribir")
        return False

    # Configuración MCP esencial
    mcp_config = {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", str(Path.home())]
            },
            "brave-search": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"]
            },
            "sqlite": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-sqlite"]
            },
            "git": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-git"]
            }
        }
    }

    # Crear archivo
    try:
        with open(claude_config_path, 'w') as f:
            json.dump(mcp_config, f, indent=2)

        action = "actualizada" if force else "creada"
        print(f"✅ Configuración MCP {action} en: {claude_config_path}")
        print("\n📋 MCPs configurados:")
        for name, config in mcp_config["mcpServers"].items():
            print(f"  - {name}: {config['command']} {' '.join(config['args'])}")

        return True

    except Exception as e:
        print(f"❌ Error creando configuración MCP: {e}")
        return False


def show_current_mcp_config() -> Dict[str, Any]:
    """
    Muestra configuración MCP actual

    Returns:
        Diccionario con la configuración MCP
    """
    claude_config_path = Path.home() / ".claude.json"

    if not claude_config_path.exists():
        print("⚠️  ~/.claude.json no existe")
        return {}

    try:
        with open(claude_config_path, 'r') as f:
            config = json.load(f)

        mcps = config.get("mcpServers", {})

        print(f"📋 MCPs configurados ({len(mcps)}):")
        for name, server_config in mcps.items():
            command = server_config.get("command", "N/A")
            args = server_config.get("args", [])
            print(f"  - {name}: {command} {' '.join(args)}")

        return mcps

    except Exception as e:
        print(f"❌ Error leyendo configuración: {e}")
        return {}


def add_mcp_server(name: str, command: str, args: list) -> bool:
    """
    Añade un nuevo servidor MCP a la configuración

    Args:
        name: Nombre del servidor MCP
        command: Comando para ejecutar el servidor
        args: Argumentos del comando

    Returns:
        True si se añadió correctamente
    """
    claude_config_path = Path.home() / ".claude.json"

    # Cargar configuración existente o crear nueva
    if claude_config_path.exists():
        try:
            with open(claude_config_path, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"❌ Error leyendo configuración existente: {e}")
            return False
    else:
        config = {"mcpServers": {}}

    # Añadir nuevo servidor
    config["mcpServers"][name] = {
        "command": command,
        "args": args
    }

    # Guardar configuración
    try:
        with open(claude_config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✅ MCP '{name}' añadido: {command} {' '.join(args)}")
        return True

    except Exception as e:
        print(f"❌ Error guardando configuración: {e}")
        return False


def remove_mcp_server(name: str) -> bool:
    """
    Elimina un servidor MCP de la configuración

    Args:
        name: Nombre del servidor MCP a eliminar

    Returns:
        True si se eliminó correctamente
    """
    claude_config_path = Path.home() / ".claude.json"

    if not claude_config_path.exists():
        print("⚠️  ~/.claude.json no existe")
        return False

    try:
        with open(claude_config_path, 'r') as f:
            config = json.load(f)

        mcps = config.get("mcpServers", {})

        if name not in mcps:
            print(f"⚠️  MCP '{name}' no encontrado")
            return False

        # Eliminar servidor
        del config["mcpServers"][name]

        # Guardar configuración
        with open(claude_config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"✅ MCP '{name}' eliminado")
        return True

    except Exception as e:
        print(f"❌ Error eliminando MCP: {e}")
        return False