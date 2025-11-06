#!/usr/bin/env python3
"""
Configurador automático de MCPs para Claude
Crea ~/.claude.json con MCPs esenciales si no existe
"""

import json
from pathlib import Path

def setup_claude_mcp_config():
    """Crea configuración MCP básica si no existe"""

    claude_config_path = Path.home() / ".claude.json"

    if claude_config_path.exists():
        print(f"✅ ~/.claude.json ya existe en: {claude_config_path}")
        return

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
            }
        }
    }

    # Crear archivo
    try:
        with open(claude_config_path, 'w') as f:
            json.dump(mcp_config, f, indent=2)

        print(f"✅ Configuración MCP creada en: {claude_config_path}")
        print("\n📋 MCPs configurados:")
        for name, config in mcp_config["mcpServers"].items():
            print(f"  - {name}: {config['command']} {' '.join(config['args'])}")

    except Exception as e:
        print(f"❌ Error creando configuración MCP: {e}")

def show_current_mcp_config():
    """Muestra configuración MCP actual"""

    claude_config_path = Path.home() / ".claude.json"

    if not claude_config_path.exists():
        print("⚠️  ~/.claude.json no existe")
        return

    try:
        with open(claude_config_path, 'r') as f:
            config = json.load(f)

        mcps = config.get("mcpServers", {})

        print(f"📋 MCPs configurados ({len(mcps)}):")
        for name, server_config in mcps.items():
            command = server_config.get("command", "N/A")
            args = server_config.get("args", [])
            print(f"  - {name}: {command} {' '.join(args)}")

    except Exception as e:
        print(f"❌ Error leyendo configuración: {e}")

if __name__ == "__main__":
    print("🔧 Configurador MCP para Claude")
    print("="*40)

    # Mostrar configuración actual
    show_current_mcp_config()
    print()

    # Setup si es necesario
    setup_claude_mcp_config()
    print()

    # Mostrar configuración final
    show_current_mcp_config()