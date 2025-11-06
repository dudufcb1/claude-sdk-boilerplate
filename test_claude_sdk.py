#!/usr/bin/env python3
"""
Test básico del Claude SDK para debug
"""

import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def test_sdk(cwd: str, settings: str | None = None):
    """Test simple del SDK"""
    print("🔍 TEST: Iniciando test básico del SDK...")

    try:
        opts = dict(
            system_prompt="Eres un asistente útil. Responde de manera concisa.",
            cwd=cwd,
            allowed_tools=["Read", "Write"],
            permission_mode="bypassPermissions"
        )
        if settings:
            opts["settings"] = settings
        options = ClaudeAgentOptions(**opts)

        print("🔍 TEST: Creando cliente...")
        client = ClaudeSDKClient(options=options)

        print("🔍 TEST: Conectando...")
        await client.connect()

        print("🔍 TEST: ✅ Conectado! Enviando mensaje de prueba...")

        # Primero escuchar mensajes en background
        async def listen_messages():
            message_count = 0
            async for response in client.receive_messages():
                message_count += 1
                print(f"🔍 TEST: Mensaje #{message_count} - Tipo: {type(response).__name__}")

                # Si es SystemMessage, es inicialización
                if hasattr(response, 'subtype'):
                    print(f"🔍 TEST: SystemMessage subtype: {response.subtype}")
                    continue

                # Si es AssistantMessage, es respuesta real
                if hasattr(response, 'content'):
                    print(f"🔍 TEST: ¡RESPUESTA DE CLAUDE! Contenido:")
                    for block in response.content:
                        if hasattr(block, 'text'):
                            print(f"🔍 TEST: '{block.text}'")
                    break

                print(f"🔍 TEST: Otro tipo de mensaje: {response}")

                # Limitar a 5 mensajes para no quedarse colgado
                if message_count >= 5:
                    break

        # Iniciar listener
        listener_task = asyncio.create_task(listen_messages())

        # Dar tiempo para que se inicialice
        await asyncio.sleep(1)

        # Enviar mensaje de prueba
        message = "Responde solo 'TEST OK' sin más explicación"
        print(f"🔍 TEST: Enviando: '{message}'")

        await client.query(message)

        print("🔍 TEST: Mensaje enviado, esperando respuesta...")

        # Esperar hasta 10 segundos por respuesta
        try:
            await asyncio.wait_for(listener_task, timeout=10.0)
        except asyncio.TimeoutError:
            print("🔍 TEST: ⏱️ Timeout - no hubo respuesta en 10 segundos")
            listener_task.cancel()

        print("🔍 TEST: Desconectando...")
        await client.disconnect()

        print("🔍 TEST: ✅ Test completado exitosamente")

    except Exception as e:
        print(f"🔍 TEST: ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse, os
    parser = argparse.ArgumentParser(description="Test básico del Claude SDK")
    parser.add_argument("--cwd", default=os.getcwd(), help="Ruta de trabajo (cwd) para el agente")
    parser.add_argument("--settings", help="Ruta de settings.json (proxy Claude Code)")
    args = parser.parse_args()
    asyncio.run(test_sdk(args.cwd, args.settings))