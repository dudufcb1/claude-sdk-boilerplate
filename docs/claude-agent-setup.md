# Boilerplate del Agente Claude (CLI)

Guía de configuración, decisiones, problemas resueltos y uso práctico del CLI de agente Claude para proyectos locales con proxy.

---

## Quick Start

1) Crear y activar entorno virtual
```
python3 -m venv .venv
source .venv/bin/activate
```

2) Instalar dependencias
```
pip install -r requirements.txt
```

3) Configurar settings (proxy + token)
- Preferido: `~/.claude-sdk/settings.json` con al menos:
```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4141/",
    "ANTHROPIC_AUTH_TOKEN": "***"
  }
}
```
- El CLI mapeará `ANTHROPIC_AUTH_TOKEN` → `ANTHROPIC_API_KEY` automáticamente y pasará `ANTHROPIC_BASE_URL` a la CLI de Claude Code.

4) Probar el CLI (depuración)
```
python start_agent.py /ruta/al/proyecto --no-hooks --verbose
```
- Verás `⚙️ Settings: ...`, `🪪 Verbose: ON`, y respuestas del asistente.

5) Opcional: contexto limpio o condensado
- Contexto limpio: `--new-session`
- Condensar última sesión e inyectar supervisor: `--condense`

---

## 1) Objetivo
Dejar un agente CLI reutilizable que:
- Se ejecute en cualquier directorio de proyecto (sin hardcodes)
- Use proxy/credenciales desde settings.json
- Imprima correctamente texto, uso de tools y resultados de tools
- Administre los turnos para evitar rezagos entre mensajes

---

## 2) Rutas y resolución de settings
Orden de resolución cuando NO se pasa `--settings`:
1. `<proyecto>/.claude-sdk/settings.json`
2. `~/.claude-sdk/settings.json`
3. `~/.claude/settings.json`

Archivo: `start_agent.py:35-46`

---

## 3) Variables de entorno soportadas (inyectadas al CLI)
Se leen desde `settings.json` tanto en un bloque `env` como en top-level:
- `ANTHROPIC_API_KEY`
- `ANTHROPIC_AUTH_TOKEN` (si existe y falta `ANTHROPIC_API_KEY`, se mapea automáticamente)
- `ANTHROPIC_BASE_URL`
- `API_TIMEOUT_MS`
- `ANTHROPIC_DEFAULT_HAIKU_MODEL`
- `ANTHROPIC_DEFAULT_SONNET_MODEL`
- `ANTHROPIC_DEFAULT_OPUS_MODEL`

Carga + mapeo y paso a SDK (`ClaudeAgentOptions.env`): `start_agent.py:86-128`, `151-161`

---

## 4) Conexión y handshake
- `await client.connect()` realiza el handshake; es seguro hacer `query()` inmediatamente.
- El receiver (stream) se inicia antes del primer `query()` para no perder mensajes.

Entradas relevantes:
- Iniciar receiver antes de query: `start_agent.py:374-381`
- `connect()` y readiness: `start_agent.py:164-176`

---

## 5) Manejo de mensajes
Tipos procesados por el handler:
- `AssistantMessage`
  - Texto (`TextBlock`) → se imprime
  - Tool use (`ToolUseBlock`) → se imprime nombre + args resumidos
  - Tool result (`ToolResultBlock` o equivalentes) → se imprime el resultado (truncado si largo)
- `SystemMessage`
  - `init` → mostrado una sola vez (completo si `--verbose`)
  - `success` → se usa como señal explícita de fin de turno
- Otros con `content` → se imprimen resultados si aplica
- `ThinkingBlock` → oculto por defecto; con `--verbose` muestra preview

Archivo/líneas clave: `start_agent.py:188-236`, `250-281`, `288-326`

---

## 6) Turnos y bloqueo del prompt
Para evitar “rezago” (que el usuario escriba mientras el asistente aún está respondiendo):
- Señales de fin de turno:
  - `ResultMessage` (detectado por nombre de clase)
  - `SystemMessage: success`
- El prompt de usuario se desbloquea sólo tras recibir fin de turno.

Archivo/líneas clave:
- Señal de fin de turno: `start_agent.py:304-323`
- Espera de fin de turno en el loop principal: `start_agent.py:450-458`

Nota: se añadió una espera corta de drenaje para mensajes que llegan inmediatamente después de `success/Result`. Si se prefiere CERO heurística, ver “Modo estricto (opcional)”.

---

## 7) Flags del CLI

- `--new-session` → elimina todas las sesiones previas del proyecto (en `sessions/`) y arranca con contexto limpio
- `--condense` → condensa la última sesión del proyecto (en `sessions/`) en un supervisor y lo inyecta en el system prompt de una nueva sesión

- `--settings /ruta/a/settings.json` → fuerza settings a usar
- `--no-hooks` → deshabilita hooks (útil al depurar AbortError del CLI Node)
- `--verbose` → logs detallados (init completo, tipos de bloques, preview de thinking, resultados de tools)

Archivo/líneas clave: `start_agent.py:404-469`

---

## 8) Hooks
- Se permiten desactivar con `--no-hooks`.
- Recomendación al activarlos: siempre con `try/except` y `return {}` para no abortar el flujo.

Wiring actual: `start_agent.py:92-110`

---

## 9) Tool results visibles
Problema: los resultados de tools (p. ej. Bash, semantic-search) llegaban pero NO se imprimían.
Solución: detección explícita de `ToolResultBlock` (y equivalentes) + impresión truncada.

Archivo/líneas clave: `start_agent.py:224-236`, `259-281`

---

## 10) Qdrant / Búsqueda semántica

### 10.1) Ubicación del almacenamiento de sesiones del CLI
Para no “contaminar” los proyectos, TODAS las sesiones se guardan en este repositorio (boilerplate), no en el proyecto objetivo:

- Directorio central: `sessions/`
- Estructura por sesión: `sessions/<project>-<id>/`
- Artefactos: `audit.json`, `supervisor_logs/`, `last_supervisor.txt`

Archivos actualizados:
- `claude_agent/core/session_tracker.py:17-23` → base `sessions/`
- `claude_agent/hooks/supervisor.py:15-20` → base `sessions/`
- `claude_agent/core/agent_config.py:21-26, 28-30` → muestra Path de nueva sesión en `sessions/`
- Helpers de condensación/limpieza en `start_agent.py:539-567` ahora buscan en `sessions/`

Error observado: `Not found: Collection codebase-default doesn't exist!` (404)
- El proxy de semantic-search requiere una colección indexada en Qdrant.
- Si no existe colección para el proyecto, el agente puede:
  - caer a exploración por tools estándar (Glob/Read), o
  - fallar la búsqueda semántica (se muestra como Tool result de error).

Impresión de error como `ToolResult`: `start_agent.py:259-268`

---

## 11) Hardcodes eliminados
- Hardcodes de paths removidos y CLI 100% dinámico por `project_path`.
- `test_claude_sdk.py` expuesto con `--cwd` y `--settings`:
  - `test_claude_sdk.py:89-95`

---

## 12) Errores y soluciones documentadas
- “Your account does not have access to Claude Code”
  - Solución: usar proxy via settings + `env` (mapear token a `ANTHROPIC_API_KEY`) y pasar `ANTHROPIC_BASE_URL`.
- Re-init al enviar query (respuesta anterior se mezclaba)
  - Solución: no pasar `session_id` en `query()` y usar señales de fin de turno para gating del prompt.
- Sólo aparece `SystemMessage:init` y no texto
  - Solución: iniciar receiver antes de query y activar `--verbose` para ver `AssistantMessage` y `ToolResult`.
- AbortError en hooks (Node CLI)
  - Solución: `--no-hooks` en depuración, reactivación gradual con try/except.

---

## 13) Ejemplos de ejecución

Con settings globales y depuración:
```
source .venv/bin/activate
python start_agent.py /ruta/al/proyecto --no-hooks --verbose
```

Forzando settings del proyecto:
```
python start_agent.py /ruta/al/proyecto --no-hooks --verbose \
  --settings /home/usuario/.claude-sdk/settings.json
```

Test SDK rápido:
```
python test_claude_sdk.py --cwd /ruta/al/proyecto --settings /home/usuario/.claude-sdk/settings.json
```

---

## 14) Modo estricto de turnos (opcional, pendiente de activación)
Sin heurísticas: desbloquear el prompt ÚNICAMENTE cuando el asistente emita un token de fin de turno.
- Flag propuesto: `--strict-turn`
- Instrucción de system prompt: “al terminar cada turno, emite exactamente `<<<EOT>>>` en una línea separada”.
- El receiver desbloquea sólo al ver `<<<EOT>>>` como `TextBlock` exacto.

---

## 15) Referencias rápidas (archivos:líneas)
- Resolución de settings: `start_agent.py:35-46`
- Carga/env mapeo y paso a SDK: `start_agent.py:86-128`, `151-161`
- Conexión y readiness: `start_agent.py:164-176`
- Receiver y timestamp: `start_agent.py:339-346`
- Clasificación de bloques y ToolResult: `start_agent.py:188-236`, `250-281`
- System + fin de turno: `start_agent.py:288-326`
- Loop principal y gating de turno: `start_agent.py:443-458`
- Helper quiet period: `start_agent.py:130-142`
- Test SDK flags: `test_claude_sdk.py:89-95`

---

## 16) Recomendaciones

### 16.1) Prerrequisitos
- Tener instalado el CLI de Claude Code (lado Node.js)
- Tener disponible el SDK Python `claude_agent_sdk` en el entorno `.venv`
- Configurar `settings.json` válido (con `ANTHROPIC_BASE_URL` y token)

### 16.2) Gitignore recomendado
Añadido `.gitignore` en la raíz para evitar subir artefactos locales:
- Python/venv: `__pycache__/`, `*.pyc`, `.venv/`, `.env`
- IDE/OS: `.vscode/`, `.idea/`, `.DS_Store`
- Tests/Coverage: `.pytest_cache/`, `.mypy_cache/`, `.coverage`
- Build: `build/`, `dist/`
- CLI runtime: `sessions/`, `claude_agent/sessions/`
- Logs: `*.log`

### 16.3) Flujo sugerido de trabajo
- Usar `--no-hooks` al depurar errores de integración
- Activar `--verbose` para inspeccionar tipos de bloques y resultados de tools
- Cuando quieras “reiniciar” contexto: `--new-session`
- Para llevarte contexto útil sin ruido: `--condense` y arrancar con supervisor

- Mantener `--no-hooks` al depurar y activar hooks sólo cuando sea necesario.
- Usar `--verbose` cuando quieras entender el flujo exacto de bloques (thinking/tool/result).
- Para análisis semántico avanzado, indexar el proyecto en Qdrant y configurar la colección correcta.
