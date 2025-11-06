# Claude Agent Boilerplate

Configuración completa de agente Claude con tools aprobadas, MCPs, sesiones y supervisor automático.

## 🚀 Inicio Rápido

```bash
# 1. Configurar MCPs (solo la primera vez)
python setup_mcp_config.py

# 2. Inicializar agente
python init_agent.py
```

## ⚙️ Características

### ✅ Tools Aprobadas
- **Read**: Lectura de archivos
- **Write**: Creación de archivos
- **Edit**: Edición de archivos
- **Bash**: Comandos de terminal
- **Glob**: Búsqueda de archivos
- **Grep**: Búsqueda en contenido

**Modo**: `bypassPermissions` - Sin restricciones para máxima automatización

### 🔌 MCPs Automáticos
Carga automática desde `~/.claude.json`:
- **filesystem**: Acceso al sistema de archivos
- **brave-search**: Búsquedas web
- **sqlite**: Base de datos SQLite

### 📊 Tracking de Sesiones
Registro automático en `sessions/{session-id}/`:
- `audit.json`: Tracking completo de la sesión
- `last_supervisor.txt`: Contexto del supervisor
- `supervisor_logs/`: Histórico de supervisores

### 🧠 Supervisor Automático
- **Pre-compactación**: Genera contexto antes de compactar
- **Hot-reload**: Carga contexto de sesiones previas
- **Análisis inteligente**: Parsea transcripts automáticamente

## 📁 Estructura Generada

```
sessions/
├── {project-name}-{session-id}/
│   ├── audit.json              # Tracking completo
│   ├── last_supervisor.txt     # Último contexto
│   └── supervisor_logs/        # Histórico
│       └── supervisor_YYYYMMDD_HHMMSS.txt
```

## 🔧 Uso Programático

```python
from claude_agent_setup import setup_claude_agent

# Setup básico
setup = setup_claude_agent(
    project_name="Mi Proyecto",
    project_path="/path/to/project"
)

# Setup con prompt personalizado
setup = setup_claude_agent(
    project_name="Mi Proyecto",
    project_path="/path/to/project",
    system_prompt="Eres un especialista en..."
)

# Acceder a la configuración
session_id = setup['session_id']
agent_options = setup['agent_options']
config = setup['config']
```

## 📊 Tracking Manual

```python
from claude_agent_setup import SessionTracker

# Crear tracker
tracker = SessionTracker("mi-sesion", "/path/project")

# Tracking manual
tracker.add_user_message("Mi pregunta")
tracker.add_agent_message("Respuesta del agente")
tracker.track_tool_use_hook("Write", {"file_path": "test.py"}, None)
```

## 🧠 Supervisor Manual

```python
from claude_agent_setup import SupervisorHook

supervisor = SupervisorHook("mi-sesion")
context = supervisor.pre_compact_hook("transcript...")
```

## ⚡ Configuración MCP

El archivo `~/.claude.json` se crea automáticamente:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
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
```

## 🎯 Datos de Audit

El archivo `audit.json` contiene:

```json
{
  "session_id": "marketing-sdk-a1b2c3d4",
  "cwd": "/path/to/project",
  "created_at": "2024-01-01T12:00:00",
  "user_messages": [...],
  "agent_messages": [...],
  "files_created": [...],
  "files_modified": [...],
  "files_viewed": [...],
  "tools_used": {"Write": 15, "Read": 8, "Bash": 3},
  "terminal_commands": [...],
  "problems_discussed": [...],
  "last_diffs": [...],
  "last_writes": [...]
}
```

## 🔄 Flujo de Trabajo

1. **Inicialización**: `setup_claude_agent()` crea sesión y configuración
2. **Tracking**: Cada tool use se registra automáticamente
3. **Supervisor**: Antes de compactar, se genera contexto
4. **Persistencia**: Todo se guarda en `sessions/`
5. **Reanudación**: Sesiones futuras cargan el contexto previo

## 🎛️ Personalización

Edita `claude_agent_setup.py` para:
- Cambiar tools aprobadas
- Modificar configuración de MCPs
- Personalizar hooks
- Ajustar tracking de audit
- Customizar análisis del supervisor

---

**Basado en el orquestador de Eduardo - Setup completo de agente Claude**