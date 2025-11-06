#!/usr/bin/env python3
"""
Ejemplo básico de configuración de agente Claude
"""

import os
import sys

# Añadir el directorio padre al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from claude_agent import setup_claude_agent


def basic_example():
    """Ejemplo básico de setup"""

    # Configuración del proyecto
    project_name = "Marketing SDK"
    project_path = os.getcwd()  # Directorio actual

    # System prompt básico
    system_prompt = """
Eres un especialista en desarrollo de SDKs de marketing.

Características de esta sesión:
- Tools completamente habilitadas
- MCPs cargados automáticamente
- Tracking automático de acciones
- Supervisor con contexto persistente
"""

    # Setup del agente
    setup = setup_claude_agent(
        project_name=project_name,
        project_path=project_path,
        system_prompt=system_prompt
    )

    print("\n" + "="*60)
    print("🎯 AGENTE CLAUDE CONFIGURADO - EJEMPLO BÁSICO")
    print("="*60)
    print(f"Sesión ID: {setup['session_id']}")
    print(f"Proyecto: {setup['session_info']['project_name']}")
    print(f"Tools: {setup['session_info']['tools_count']}")
    print(f"MCPs: {setup['session_info']['mcps_count']}")
    print(f"Tracking: {setup['session_info']['session_path']}")
    print("="*60)

    return setup


def advanced_example():
    """Ejemplo avanzado con configuraciones personalizadas"""

    # Configuración avanzada
    project_name = "Advanced AI Project"
    project_path = "/tmp/advanced_project"  # Proyecto específico

    # System prompt especializado
    system_prompt = """
Eres un arquitecto de sistemas IA especializado en:
- Desarrollo de APIs complejas
- Integración de múltiples servicios
- Optimización de performance
- Arquitectura escalable

Esta sesión incluye:
- Herramientas sin restricciones (bypass mode)
- Múltiples MCPs para máxima funcionalidad
- Tracking detallado para auditoría
- Supervisor inteligente que mantiene contexto

Enfócate en soluciones robustas y bien documentadas.
"""

    # Setup avanzado
    setup = setup_claude_agent(
        project_name=project_name,
        project_path=project_path,
        system_prompt=system_prompt
    )

    # Acceder a componentes individuales
    config = setup['config']
    tracker = config.create_session_tracker()
    supervisor = config.create_supervisor_hook()

    print("\n" + "="*60)
    print("🎯 AGENTE CLAUDE CONFIGURADO - EJEMPLO AVANZADO")
    print("="*60)
    print(f"Sesión ID: {setup['session_id']}")
    print(f"Proyecto: {setup['session_info']['project_name']}")
    print(f"Path: {setup['session_info']['project_path']}")

    # Mostrar estadísticas del tracker
    audit_summary = tracker.get_audit_summary()
    print(f"Audit: {audit_summary}")

    # Mostrar estadísticas del supervisor
    supervisor_stats = supervisor.get_supervisor_stats()
    print(f"Supervisor: {supervisor_stats}")

    print("="*60)

    return setup, config, tracker, supervisor


if __name__ == "__main__":
    print("🚀 Ejecutando ejemplos de Claude Agent...")
    print("\n1. Ejemplo Básico:")
    basic_setup = basic_example()

    print("\n2. Ejemplo Avanzado:")
    advanced_setup, config, tracker, supervisor = advanced_example()

    print("\n✅ Ejemplos ejecutados correctamente!")
    print(f"   - Sesión básica: {basic_setup['session_id']}")
    print(f"   - Sesión avanzada: {advanced_setup['session_id']}")