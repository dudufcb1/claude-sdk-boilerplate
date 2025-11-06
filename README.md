# Claude Agent Boilerplate

Boilerplate completo para agente Claude con SDK real, tracking automático y supervisor inteligente.

## 🚀 Uso

```bash
python start_agent.py /ruta/del/proyecto
```

## ⚙️ Configuración

### System Prompt
Crea `prompt.txt` para personalizar el comportamiento del agente:
```
Eres un especialista en...
```

Si no existe, usa prompt por defecto.

### MCPs
El agente carga automáticamente todos los MCPs desde `~/.claude.json`.

## 🎯 Características

✅ **SDK Real**: Conexión directa al Claude Agent SDK
✅ **Tools Sin Restricciones**: Bypass mode activado
✅ **Tracking Automático**: Registro de mensajes, tools y archivos
✅ **Supervisor Inteligente**: Contexto persistente entre compactaciones
✅ **Sesiones Persistentes**: Cada ejecución crea sesión única con ID
✅ **Comandos Integrados**: `exit`, `status`, `save`, `cancel`

## 📊 Sesiones

Cada sesión se guarda en:
```
claude_agent/sessions/{session-id}/
├── audit.json              # Tracking completo
├── last_supervisor.txt     # Contexto del supervisor
└── supervisor_logs/        # Histórico
```

## 💬 Comandos

Durante el chat:
- `exit` - Salir y guardar
- `status` - Ver estadísticas de la sesión
- `save` - Guardar contexto del supervisor
- `cancel` - Cancelar operación actual

## 🛠️ Estructura

```
claude_agent/
├── core/           # Configuración y tracking
├── hooks/          # Supervisor automático
├── config/         # Setup de MCPs
└── sessions/       # Data de sesiones
```

---

**Basado en el orquestador de Eduardo - Setup completo de agente Claude**