#!/usr/bin/env python3
"""
Ejemplo de gestión de MCPs
"""

import os
import sys

# Añadir el directorio padre al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from claude_agent.config.mcp_setup import (
    show_current_mcp_config,
    setup_claude_mcp_config,
    add_mcp_server,
    remove_mcp_server
)


def show_mcp_example():
    """Ejemplo de mostrar configuración MCP actual"""
    print("📋 Configuración MCP actual:")
    mcps = show_current_mcp_config()
    return mcps


def setup_mcp_example():
    """Ejemplo de setup básico de MCPs"""
    print("\n🔧 Configurando MCPs básicos...")
    result = setup_claude_mcp_config(force=False)
    return result


def add_mcp_example():
    """Ejemplo de añadir MCP personalizado"""
    print("\n➕ Añadiendo MCP personalizado...")

    # Ejemplo: añadir servidor de tiempo
    success = add_mcp_server(
        name="time-server",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-time"]
    )

    if success:
        print("✅ MCP personalizado añadido")
    else:
        print("❌ Error añadiendo MCP personalizado")

    return success


def remove_mcp_example():
    """Ejemplo de eliminar MCP"""
    print("\n➖ Eliminando MCP de ejemplo...")

    success = remove_mcp_server("time-server")

    if success:
        print("✅ MCP eliminado")
    else:
        print("⚠️  MCP no encontrado o error eliminando")

    return success


def full_mcp_management_example():
    """Ejemplo completo de gestión de MCPs"""
    print("🔧 GESTIÓN COMPLETA DE MCPs")
    print("="*50)

    # Mostrar configuración actual
    print("\n1. Configuración actual:")
    current_mcps = show_mcp_example()

    # Setup básico si es necesario
    print("\n2. Setup básico:")
    setup_result = setup_mcp_example()

    # Añadir MCP personalizado
    print("\n3. Añadir MCP personalizado:")
    add_result = add_mcp_example()

    # Mostrar configuración después de añadir
    if add_result:
        print("\n4. Configuración después de añadir:")
        show_mcp_example()

        # Eliminar MCP de prueba
        print("\n5. Eliminar MCP de prueba:")
        remove_result = remove_mcp_example()

        if remove_result:
            print("\n6. Configuración final:")
            show_mcp_example()

    print("\n✅ Gestión de MCPs completada!")


if __name__ == "__main__":
    full_mcp_management_example()