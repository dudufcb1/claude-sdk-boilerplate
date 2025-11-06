# 🏆 The Ultimate Guide to Claude Tools
## El Grial de la Integración de Herramientas con Claude

> **Guía definitiva y abstracta** para implementar, usar y dominar las Tools del SDK de Anthropic Claude.  
> Basada en aprendizajes reales de un proyecto de producción.

---

## 📚 Tabla de Contenidos

1. [Conceptos Fundamentales](#conceptos-fundamentales)
2. [Anatomía de una Tool](#anatomía-de-una-tool)
3. [Implementación End-to-End](#implementación-end-to-end)
4. [Tool Choice: El Arte del Control](#tool-choice-el-arte-del-control)
5. [El Bucle de Herramientas](#el-bucle-de-herramientas)
6. [Patrones Avanzados](#patrones-avanzados)
7. [Errores Comunes y Soluciones](#errores-comunes-y-soluciones)
8. [Best Practices](#best-practices)

---

## 🎯 Conceptos Fundamentales

### ¿Qué es una Tool?

Una **Tool** (herramienta) es una función que Claude puede **invocar** durante una conversación para:

- 🔍 Obtener información externa (búsquedas, APIs, bases de datos)
- 🛠️ Ejecutar acciones (crear archivos, enviar emails, hacer cálculos)
- 📊 Devolver datos estructurados (JSON con esquema definido)

### Diferencia clave: Tools vs MCP

| Aspecto | **Tools (SDK)** | **MCP (Model Context Protocol)** |
|---------|-----------------|-----------------------------------|
| **Definición** | Funciones definidas en tu código | Servidor externo con protocolo estándar |
| **Ejecución** | En tu aplicación (Python/JS) | Proceso separado (puede ser remoto) |
| **Complejidad** | Simple, directo | Más complejo, más escalable |
| **Uso ideal** | Lógica de negocio específica | Herramientas reutilizables entre apps |

**Esta guía se enfoca en Tools del SDK**, que son más directas y fáciles de implementar.

---

## 🔧 Anatomía de una Tool

### Estructura básica

```python
{
    "name": "search_in_perplexity",
    "description": "Busca información actualizada en internet usando Perplexity AI",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "La consulta de búsqueda"
            },
            "focus": {
                "type": "string",
                "enum": ["web", "academic", "news"],
                "description": "Tipo de búsqueda a realizar"
            },
            "max_results": {
                "type": "integer",
                "description": "Número máximo de resultados",
                "default": 5
            }
        },
        "required": ["query"]
    }
}
```

### Componentes esenciales

1. **`name`**: Identificador único (snake_case recomendado)
2. **`description`**: Explica a Claude CUÁNDO y CÓMO usar la tool
3. **`input_schema`**: Esquema JSON Schema que define los parámetros
   - `properties`: Cada parámetro con su tipo y descripción
   - `required`: Lista de parámetros obligatorios
   - `enum`: Valores permitidos (opcional pero muy útil)

### 💡 Tip: La descripción es CRÍTICA

```python
# ❌ MAL: Descripción vaga
"description": "Busca en internet"

# ✅ BIEN: Descripción específica
"description": "Busca información actualizada en internet usando Perplexity AI. Úsala cuando necesites datos recientes, noticias, o información que no esté en tu conocimiento base. NO la uses para preguntas generales que puedas responder directamente."
```

---

## 🚀 Implementación End-to-End

### Paso 1: Definir la Tool

```python
from anthropic import Anthropic

# Definir la herramienta
tools = [
    {
        "name": "search_in_perplexity",
        "description": "Busca información actualizada en internet usando Perplexity AI",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "La consulta de búsqueda"
                },
                "focus": {
                    "type": "string",
                    "enum": ["web", "academic", "news"],
                    "description": "Tipo de búsqueda"
                }
            },
            "required": ["query"]
        }
    }
]
```

### Paso 2: Implementar la función ejecutora

```python
def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Ejecuta la herramienta solicitada por Claude.
    Esta función es el PUENTE entre Claude y tu lógica de negocio.
    """
    if tool_name == "search_in_perplexity":
        return search_in_perplexity(
            query=tool_input.get("query"),
            focus=tool_input.get("focus", "web")
        )
    
    return json.dumps({"error": f"Tool {tool_name} no encontrada"})


def search_in_perplexity(query: str, focus: str = "web") -> str:
    """
    Implementación MOCK de búsqueda en Perplexity.
    En producción, aquí harías la llamada real a la API.
    """
    # MOCK: Simular respuesta de Perplexity
    mock_results = {
        "query": query,
        "focus": focus,
        "results": [
            {
                "title": f"Resultado 1 para: {query}",
                "snippet": "Lorem ipsum dolor sit amet...",
                "url": "https://example.com/1",
                "relevance": 0.95
            },
            {
                "title": f"Resultado 2 para: {query}",
                "snippet": "Consectetur adipiscing elit...",
                "url": "https://example.com/2",
                "relevance": 0.87
            }
        ],
        "timestamp": "2025-11-05T10:30:00Z"
    }
    
    return json.dumps(mock_results, ensure_ascii=False)
```

### Paso 3: Llamar a Claude con la Tool

```python
client = Anthropic(api_key="tu-api-key")

# Mensaje inicial del usuario
messages = [
    {"role": "user", "content": "¿Cuáles son las últimas noticias sobre IA en 2025?"}
]

# Primera llamada: Claude decide si usar la tool
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,  # ← Pasar las tools disponibles
    messages=messages
)

print(f"Stop reason: {response.stop_reason}")
print(f"Content: {response.content}")
```

**Salida esperada:**

```python
Stop reason: tool_use  # (o 'end_turn' en algunos proxies)
Content: [
    TextBlock(text="Necesito buscar información actualizada sobre IA en 2025."),
    ToolUseBlock(
        id="toolu_123abc",
        name="search_in_perplexity",
        input={
            "query": "últimas noticias inteligencia artificial 2025",
            "focus": "news"
        }
    )
]
```

### Paso 4: Ejecutar la Tool y devolver resultados

```python
# Detectar si Claude quiere usar una tool
tool_use_blocks = [
    block for block in response.content
    if getattr(block, "type", None) == "tool_use"
]

if tool_use_blocks:
    # Agregar la respuesta de Claude a los mensajes
    messages.append({
        "role": "assistant",
        "content": response.content
    })

    # Ejecutar cada tool que Claude solicitó
    tool_results = []
    for tool_block in tool_use_blocks:
        print(f"Ejecutando: {tool_block.name}")

        # Ejecutar la función real
        result = execute_tool(tool_block.name, tool_block.input)

        # Preparar el resultado para Claude
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": tool_block.id,  # ← IMPORTANTE: mismo ID
            "content": result
        })

    # Enviar los resultados de vuelta a Claude
    messages.append({
        "role": "user",
        "content": tool_results
    })

    # Segunda llamada: Claude procesa los resultados
    final_response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=tools,
        messages=messages
    )

    # Extraer la respuesta final
    final_text = ""
    for block in final_response.content:
        if hasattr(block, "text"):
            final_text += block.text

    print(f"Respuesta final: {final_text}")
```

**Salida esperada:**

```
Respuesta final: Basándome en la búsqueda realizada, las últimas noticias sobre IA en 2025 incluyen:

1. **Resultado 1 para: últimas noticias inteligencia artificial 2025**
   Lorem ipsum dolor sit amet...
   [Fuente](https://example.com/1)

2. **Resultado 2 para: últimas noticias inteligencia artificial 2025**
   Consectetur adipiscing elit...
   [Fuente](https://example.com/2)

Estos resultados fueron obtenidos el 2025-11-05T10:30:00Z.
```

---

## 🎮 Tool Choice: El Arte del Control

### Los 4 modos de `tool_choice`

```python
# 1. AUTO (default): Claude decide si usar tools o no
response = client.messages.create(
    tools=tools,
    tool_choice={"type": "auto"},  # ← Puede omitirse, es el default
    messages=messages
)

# 2. ANY: Claude DEBE usar alguna tool (cualquiera)
response = client.messages.create(
    tools=tools,
    tool_choice={"type": "any"},  # ← Fuerza uso de tools
    messages=messages
)

# 3. TOOL: Claude DEBE usar una tool específica
response = client.messages.create(
    tools=tools,
    tool_choice={"type": "tool", "name": "search_in_perplexity"},  # ← Fuerza tool específica
    messages=messages
)

# 4. NONE: Claude NO PUEDE usar tools (solo texto)
response = client.messages.create(
    tools=tools,
    tool_choice={"type": "none"},  # ← Prohibe tools
    messages=messages
)
```

### Cuándo usar cada modo

| Modo | Cuándo usarlo | Ejemplo |
|------|---------------|---------|
| `auto` | Conversación natural, Claude decide | Chatbot general |
| `any` | Necesitas garantizar datos estructurados | Análisis que debe devolver JSON |
| `tool` | Workflow específico, paso obligatorio | "Primero busca, luego analiza" |
| `none` | Síntesis final, no más búsquedas | "Resume todo lo encontrado" |

### 💡 Patrón: Workflow multi-etapa

```python
# Etapa 1: FORZAR búsqueda
response_1 = client.messages.create(
    tools=tools,
    tool_choice={"type": "tool", "name": "search_in_perplexity"},
    messages=[{"role": "user", "content": "Investiga sobre X"}]
)

# ... ejecutar tool y agregar resultados ...

# Etapa 2: PERMITIR análisis adicional si es necesario
response_2 = client.messages.create(
    tools=tools,
    tool_choice={"type": "auto"},  # Claude decide si necesita más búsquedas
    messages=messages
)

# ... procesar si hay más tools ...

# Etapa 3: PROHIBIR tools, solo síntesis
response_3 = client.messages.create(
    tools=tools,
    tool_choice={"type": "none"},  # Solo texto final
    messages=messages + [{"role": "user", "content": "Resume todo"}]
)
```

---

## 🔄 El Bucle de Herramientas

### Problema: Claude puede llamar múltiples tools

Claude puede decidir usar **varias tools en secuencia** o **múltiples tools en paralelo**.

### Solución: Implementar un bucle

```python
def chat_with_tools(user_message: str, max_iterations: int = 5):
    """
    Bucle completo de conversación con tools.
    Maneja múltiples llamadas a tools automáticamente.
    """
    messages = [{"role": "user", "content": user_message}]

    for iteration in range(max_iterations):
        print(f"\n--- Iteración {iteration + 1} ---")

        # Llamar a Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            tools=tools,
            messages=messages
        )

        print(f"Stop reason: {response.stop_reason}")

        # Detectar si hay tool_use (método robusto)
        has_tool_use = any(
            getattr(block, "type", None) == "tool_use"
            for block in response.content
        )

        if not has_tool_use:
            # No más tools, extraer respuesta final
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            return final_text

        # Agregar respuesta de Claude
        messages.append({
            "role": "assistant",
            "content": response.content
        })

        # Ejecutar todas las tools solicitadas
        tool_results = []
        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                print(f"  → Ejecutando: {block.name}")
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

        # Agregar resultados
        messages.append({
            "role": "user",
            "content": tool_results
        })

    return "⚠️ Se alcanzó el límite de iteraciones"


# Uso
respuesta = chat_with_tools("¿Qué está pasando con la IA en 2025?")
print(respuesta)
```

### ⚠️ CRÍTICO: No confíes en `stop_reason`

```python
# ❌ FRÁGIL: Depender de stop_reason
if response.stop_reason == "tool_use":
    # Procesar tools

# ✅ ROBUSTO: Inspeccionar el contenido
has_tool_use = any(
    getattr(block, "type", None) == "tool_use"
    for block in response.content
)
if has_tool_use:
    # Procesar tools
```

**Razón**: Diferentes proxies, gateways o versiones pueden devolver `stop_reason='end_turn'` aunque haya `ToolUseBlock` en el contenido.

---

## 🎨 Patrones Avanzados

### Patrón 1: Tool con respuesta estructurada

```python
# Definir tool que devuelve JSON estructurado
tools = [
    {
        "name": "analyze_sentiment",
        "description": "Analiza el sentimiento de un texto y devuelve resultados estructurados",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Texto a analizar"},
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral"],
                    "description": "Sentimiento detectado"
                },
                "confidence": {
                    "type": "number",
                    "description": "Confianza del análisis (0-1)"
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Palabras clave detectadas"
                }
            },
            "required": ["text", "sentiment", "confidence", "keywords"]
        }
    }
]

# Forzar uso para obtener datos estructurados
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "tool", "name": "analyze_sentiment"},
    messages=[{
        "role": "user",
        "content": "Analiza: 'Este producto es increíble, lo recomiendo totalmente'"
    }]
)

# Extraer datos estructurados
for block in response.content:
    if getattr(block, "type", None) == "tool_use":
        structured_data = block.input
        print(f"Sentimiento: {structured_data['sentiment']}")
        print(f"Confianza: {structured_data['confidence']}")
        print(f"Keywords: {structured_data['keywords']}")
```

**Salida:**
```
Sentimiento: positive
Confianza: 0.95
Keywords: ['increíble', 'recomiendo', 'producto']
```

### Patrón 2: Multi-tool con dependencias

```python
tools = [
    {
        "name": "search_in_perplexity",
        "description": "Busca información en internet",
        "input_schema": {...}
    },
    {
        "name": "summarize_results",
        "description": "Resume los resultados de una búsqueda",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_results": {"type": "string"},
                "max_length": {"type": "integer", "default": 200}
            },
            "required": ["search_results"]
        }
    }
]

# Claude puede encadenar: primero busca, luego resume
messages = [{"role": "user", "content": "Busca sobre IA y dame un resumen corto"}]

# Bucle automático manejará ambas tools
respuesta = chat_with_tools("Busca sobre IA y dame un resumen corto")
```

### Patrón 3: Tool con validación

```python
def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Ejecutor con validación de parámetros"""

    if tool_name == "search_in_perplexity":
        # Validar parámetros
        query = tool_input.get("query")
        if not query or len(query) < 3:
            return json.dumps({
                "error": "Query debe tener al menos 3 caracteres",
                "success": False
            })

        # Validar focus
        focus = tool_input.get("focus", "web")
        if focus not in ["web", "academic", "news"]:
            return json.dumps({
                "error": f"Focus '{focus}' no válido. Usa: web, academic, news",
                "success": False
            })

        # Ejecutar búsqueda
        try:
            result = search_in_perplexity(query, focus)
            return json.dumps({
                "success": True,
                "data": result
            })
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "success": False
            })

    return json.dumps({"error": f"Tool {tool_name} no encontrada"})
```

### Patrón 4: Tool con caché/rate limiting

```python
from functools import lru_cache
from time import time, sleep

# Caché simple
@lru_cache(maxsize=100)
def search_in_perplexity_cached(query: str, focus: str = "web") -> str:
    """Versión con caché para evitar búsquedas duplicadas"""
    return search_in_perplexity(query, focus)

# Rate limiting
class RateLimiter:
    def __init__(self, calls_per_minute: int = 10):
        self.calls_per_minute = calls_per_minute
        self.calls = []

    def wait_if_needed(self):
        now = time()
        # Limpiar llamadas antiguas (> 1 minuto)
        self.calls = [t for t in self.calls if now - t < 60]

        if len(self.calls) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.calls[0])
            if sleep_time > 0:
                print(f"⏳ Rate limit alcanzado, esperando {sleep_time:.1f}s")
                sleep(sleep_time)

        self.calls.append(now)

rate_limiter = RateLimiter(calls_per_minute=10)

def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "search_in_perplexity":
        rate_limiter.wait_if_needed()  # ← Controlar rate limit
        return search_in_perplexity_cached(
            tool_input.get("query"),
            tool_input.get("focus", "web")
        )
    return json.dumps({"error": "Tool no encontrada"})
```

---

## ❌ Errores Comunes y Soluciones

### Error 1: "Tool result must be a string"

```python
# ❌ MAL: Devolver dict directamente
def execute_tool(tool_name, tool_input):
    return {"results": [...]}  # ← Error!

# ✅ BIEN: Convertir a JSON string
def execute_tool(tool_name, tool_input):
    return json.dumps({"results": [...]})  # ← Correcto
```

### Error 2: "tool_use_id mismatch"

```python
# ❌ MAL: ID incorrecto o faltante
tool_results.append({
    "type": "tool_result",
    "tool_use_id": "wrong_id",  # ← Error!
    "content": result
})

# ✅ BIEN: Usar el ID exacto del ToolUseBlock
for block in response.content:
    if block.type == "tool_use":
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,  # ← Correcto
            "content": execute_tool(block.name, block.input)
        })
```

### Error 3: No detectar tool_use correctamente

```python
# ❌ MAL: Asumir que stop_reason es confiable
if response.stop_reason == "tool_use":
    # Puede fallar con proxies

# ✅ BIEN: Inspeccionar el contenido
has_tool_use = any(
    getattr(block, "type", None) == "tool_use"
    for block in response.content
)
```

### Error 4: Bucle infinito de tools

```python
# ❌ MAL: Sin límite de iteraciones
while True:
    response = client.messages.create(...)
    # Puede nunca terminar

# ✅ BIEN: Límite de iteraciones
for iteration in range(max_iterations):
    response = client.messages.create(...)
    if not has_tool_use:
        break
```

### Error 5: No manejar errores en tools

```python
# ❌ MAL: Dejar que excepciones rompan el flujo
def execute_tool(tool_name, tool_input):
    result = api_call(tool_input["query"])  # Puede fallar
    return result

# ✅ BIEN: Manejar errores y devolver JSON
def execute_tool(tool_name, tool_input):
    try:
        result = api_call(tool_input["query"])
        return json.dumps({"success": True, "data": result})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
```

---

## ✅ Best Practices

### 1. Descripciones claras y específicas

```python
# ❌ Vago
"description": "Busca cosas"

# ✅ Específico
"description": """
Busca información actualizada en internet usando Perplexity AI.

CUÁNDO USAR:
- Necesitas datos recientes (noticias, eventos actuales)
- Información que no está en tu conocimiento base
- Verificar hechos o estadísticas

CUÁNDO NO USAR:
- Preguntas generales que puedes responder directamente
- Información histórica bien conocida
- Cálculos matemáticos simples
"""
```

### 2. Validación de parámetros

```python
def execute_tool(tool_name: str, tool_input: dict) -> str:
    # Validar parámetros requeridos
    if tool_name == "search_in_perplexity":
        if "query" not in tool_input:
            return json.dumps({"error": "Parámetro 'query' requerido"})

        if len(tool_input["query"]) < 3:
            return json.dumps({"error": "Query debe tener al menos 3 caracteres"})

    # Ejecutar tool...
```

### 3. Logging detallado

```python
import logging

logger = logging.getLogger(__name__)

def execute_tool(tool_name: str, tool_input: dict) -> str:
    logger.info(f"Ejecutando tool: {tool_name}")
    logger.debug(f"Input: {tool_input}")

    try:
        result = search_in_perplexity(**tool_input)
        logger.info(f"Tool {tool_name} ejecutada exitosamente")
        return result
    except Exception as e:
        logger.error(f"Error en tool {tool_name}: {e}", exc_info=True)
        return json.dumps({"error": str(e)})
```

### 4. Timeouts y reintentos

```python
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def search_in_perplexity(query: str, focus: str = "web") -> str:
    """Búsqueda con reintentos automáticos"""
    response = requests.post(
        "https://api.perplexity.ai/search",
        json={"query": query, "focus": focus},
        timeout=10  # ← Timeout de 10 segundos
    )
    response.raise_for_status()
    return json.dumps(response.json())
```

### 5. Respuestas estructuradas consistentes

```python
def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Siempre devolver formato consistente"""
    try:
        if tool_name == "search_in_perplexity":
            data = search_in_perplexity(**tool_input)
            return json.dumps({
                "success": True,
                "data": data,
                "metadata": {
                    "tool": tool_name,
                    "timestamp": time.time()
                }
            })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "metadata": {
                "tool": tool_name,
                "timestamp": time.time()
            }
        })
```

### 6. Testing de tools

```python
import pytest

def test_search_tool_basic():
    """Test básico de la tool de búsqueda"""
    result = execute_tool(
        "search_in_perplexity",
        {"query": "test query", "focus": "web"}
    )

    data = json.loads(result)
    assert data["success"] == True
    assert "data" in data

def test_search_tool_validation():
    """Test de validación de parámetros"""
    result = execute_tool(
        "search_in_perplexity",
        {"query": "ab"}  # Query muy corta
    )

    data = json.loads(result)
    assert data["success"] == False
    assert "error" in data

def test_search_tool_invalid_focus():
    """Test de focus inválido"""
    result = execute_tool(
        "search_in_perplexity",
        {"query": "test", "focus": "invalid"}
    )

    data = json.loads(result)
    assert data["success"] == False
```

---

## 🎓 Ejemplo Completo: Sistema de Investigación

```python
"""
Sistema completo de investigación con múltiples tools.
Demuestra todos los conceptos de esta guía.
"""

from anthropic import Anthropic
import json
from typing import Dict, Any, List
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DEFINICIÓN DE TOOLS
# ============================================================================

TOOLS = [
    {
        "name": "search_in_perplexity",
        "description": """
        Busca información actualizada en internet usando Perplexity AI.
        Úsala para obtener datos recientes, noticias o información verificada.
        """,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "La consulta de búsqueda"
                },
                "focus": {
                    "type": "string",
                    "enum": ["web", "academic", "news"],
                    "description": "Tipo de búsqueda"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "analyze_sources",
        "description": """
        Analiza la credibilidad y relevancia de las fuentes encontradas.
        Devuelve un análisis estructurado de cada fuente.
        """,
        "input_schema": {
            "type": "object",
            "properties": {
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de URLs o títulos de fuentes"
                },
                "credibility_scores": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Puntuación de credibilidad (0-1) para cada fuente"
                },
                "relevance_scores": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Puntuación de relevancia (0-1) para cada fuente"
                }
            },
            "required": ["sources", "credibility_scores", "relevance_scores"]
        }
    },
    {
        "name": "synthesize_research",
        "description": """
        Sintetiza los hallazgos de la investigación en un reporte estructurado.
        Incluye resumen ejecutivo, hallazgos clave y conclusiones.
        """,
        "input_schema": {
            "type": "object",
            "properties": {
                "executive_summary": {
                    "type": "string",
                    "description": "Resumen ejecutivo de la investigación"
                },
                "key_findings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Hallazgos clave"
                },
                "conclusions": {
                    "type": "string",
                    "description": "Conclusiones de la investigación"
                },
                "confidence_level": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Nivel de confianza en los hallazgos"
                }
            },
            "required": ["executive_summary", "key_findings", "conclusions", "confidence_level"]
        }
    }
]

# ============================================================================
# IMPLEMENTACIÓN DE TOOLS
# ============================================================================

def search_in_perplexity(query: str, focus: str = "web") -> Dict[str, Any]:
    """Mock de búsqueda en Perplexity"""
    logger.info(f"Buscando: '{query}' (focus: {focus})")

    # Simular resultados
    return {
        "query": query,
        "focus": focus,
        "results": [
            {
                "title": f"Artículo sobre {query}",
                "url": "https://example.com/article1",
                "snippet": "Información relevante sobre el tema...",
                "date": "2025-11-05",
                "source": "Example News"
            },
            {
                "title": f"Estudio académico: {query}",
                "url": "https://academic.example.com/paper1",
                "snippet": "Investigación científica reciente...",
                "date": "2025-10-15",
                "source": "Academic Journal"
            }
        ],
        "total_results": 2
    }

def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """
    Ejecutor central de tools con manejo de errores.
    """
    logger.info(f"Ejecutando tool: {tool_name}")
    logger.debug(f"Input: {json.dumps(tool_input, indent=2)}")

    try:
        if tool_name == "search_in_perplexity":
            # Validar parámetros
            query = tool_input.get("query")
            if not query or len(query) < 3:
                raise ValueError("Query debe tener al menos 3 caracteres")

            focus = tool_input.get("focus", "web")
            if focus not in ["web", "academic", "news"]:
                raise ValueError(f"Focus inválido: {focus}")

            # Ejecutar búsqueda
            result = search_in_perplexity(query, focus)
            return json.dumps({
                "success": True,
                "data": result,
                "metadata": {"tool": tool_name}
            })

        elif tool_name == "analyze_sources":
            # Esta tool es "virtual" - Claude la usa para estructurar su análisis
            # No necesita ejecución real, solo devolvemos confirmación
            return json.dumps({
                "success": True,
                "message": "Análisis de fuentes completado",
                "data": tool_input
            })

        elif tool_name == "synthesize_research":
            # Tool virtual para síntesis estructurada
            return json.dumps({
                "success": True,
                "message": "Síntesis completada",
                "data": tool_input
            })

        else:
            raise ValueError(f"Tool desconocida: {tool_name}")

    except Exception as e:
        logger.error(f"Error en tool {tool_name}: {e}", exc_info=True)
        return json.dumps({
            "success": False,
            "error": str(e),
            "metadata": {"tool": tool_name}
        })

# ============================================================================
# SISTEMA DE CHAT CON TOOLS
# ============================================================================

class ResearchAssistant:
    """Asistente de investigación con tools"""

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def research(self, topic: str, max_iterations: int = 10) -> Dict[str, Any]:
        """
        Realiza una investigación completa sobre un tema.

        Workflow:
        1. Busca información (forzado)
        2. Analiza fuentes (opcional)
        3. Sintetiza hallazgos (forzado)
        """
        messages = [{
            "role": "user",
            "content": f"""
            Investiga sobre: {topic}

            Proceso:
            1. Busca información actualizada usando search_in_perplexity
            2. Analiza la credibilidad de las fuentes con analyze_sources
            3. Sintetiza los hallazgos con synthesize_research

            Devuelve un reporte completo y estructurado.
            """
        }]

        synthesis_data = None

        for iteration in range(max_iterations):
            logger.info(f"\n{'='*60}")
            logger.info(f"Iteración {iteration + 1}/{max_iterations}")
            logger.info(f"{'='*60}")

            # Llamar a Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                tools=TOOLS,
                messages=messages
            )

            logger.info(f"Stop reason: {response.stop_reason}")

            # Detectar tool_use
            has_tool_use = any(
                getattr(block, "type", None) == "tool_use"
                for block in response.content
            )

            if not has_tool_use:
                # No más tools, extraer respuesta final
                final_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text += block.text

                return {
                    "success": True,
                    "final_response": final_text,
                    "synthesis": synthesis_data,
                    "iterations": iteration + 1
                }

            # Agregar respuesta de Claude
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Ejecutar tools
            tool_results = []
            for block in response.content:
                if getattr(block, "type", None) == "tool_use":
                    logger.info(f"  → Tool: {block.name}")

                    # Ejecutar tool
                    result = execute_tool(block.name, block.input)

                    # Guardar síntesis si es la tool final
                    if block.name == "synthesize_research":
                        synthesis_data = block.input

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Agregar resultados
            messages.append({
                "role": "user",
                "content": tool_results
            })

        return {
            "success": False,
            "error": "Se alcanzó el límite de iteraciones",
            "iterations": max_iterations
        }

# ============================================================================
# EJEMPLO DE USO
# ============================================================================

def main():
    """Ejemplo de uso del sistema completo"""

    # Inicializar asistente
    assistant = ResearchAssistant(api_key="tu-api-key-aqui")

    # Realizar investigación
    result = assistant.research("Avances en IA generativa en 2025")

    if result["success"]:
        print("\n" + "="*60)
        print("INVESTIGACIÓN COMPLETADA")
        print("="*60)

        if result.get("synthesis"):
            synthesis = result["synthesis"]
            print(f"\n📊 RESUMEN EJECUTIVO:")
            print(synthesis.get("executive_summary", "N/A"))

            print(f"\n🔍 HALLAZGOS CLAVE:")
            for i, finding in enumerate(synthesis.get("key_findings", []), 1):
                print(f"  {i}. {finding}")

            print(f"\n💡 CONCLUSIONES:")
            print(synthesis.get("conclusions", "N/A"))

            print(f"\n📈 NIVEL DE CONFIANZA: {synthesis.get('confidence_level', 'N/A')}")

        print(f"\n✅ Completado en {result['iterations']} iteraciones")
    else:
        print(f"\n❌ Error: {result.get('error')}")

if __name__ == "__main__":
    main()
```

---

## 🎯 Resumen Final

### Checklist de implementación

- [ ] **Definir tools** con `name`, `description` e `input_schema` claros
- [ ] **Implementar ejecutor** que convierta tool calls en acciones reales
- [ ] **Usar detección robusta** de tool_use (inspeccionar `content`, no `stop_reason`)
- [ ] **Implementar bucle** para manejar múltiples tool calls
- [ ] **Validar parámetros** antes de ejecutar tools
- [ ] **Manejar errores** y devolver JSON estructurado siempre
- [ ] **Usar `tool_choice`** apropiadamente según el caso de uso
- [ ] **Agregar logging** para debugging
- [ ] **Implementar rate limiting** si usas APIs externas
- [ ] **Escribir tests** para cada tool

### Conceptos clave

1. **Tools son funciones** que Claude puede invocar
2. **`tool_choice` controla** cuándo y cómo se usan
3. **El bucle de herramientas** maneja múltiples llamadas
4. **Siempre devolver JSON string** desde el ejecutor
5. **No confiar en `stop_reason`**, inspeccionar `content`
6. **Validar y manejar errores** en cada tool
7. **Tools virtuales** pueden usarse para respuestas estructuradas

---

## 📚 Referencias

- [Documentación oficial de Anthropic](https://docs.anthropic.com/claude/docs/tool-use)
- [JSON Schema](https://json-schema.org/)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)

---

**¡Felicidades!** Ahora dominas las Tools de Claude. 🎉

Este conocimiento te permitirá construir agentes inteligentes que pueden:
- 🔍 Buscar información en tiempo real
- 📊 Devolver datos estructurados y confiables
- 🔄 Ejecutar workflows complejos multi-etapa
- 🛠️ Integrarse con cualquier API o sistema externo

**Próximos pasos sugeridos:**
1. Implementa tu primera tool simple
2. Prueba el bucle de herramientas
3. Experimenta con `tool_choice`
4. Construye un sistema multi-tool como el ejemplo

¡Ahora ve y construye algo increíble! 🚀
