# 🔌 Configuración de Settings y Proxy
## Cómo este proyecto lee configuración y se conecta a través de proxy

> **Guía práctica** basada en la implementación real de `claude_config.py`

---

## 📋 Tabla de Contenidos

1. [El Problema](#el-problema)
2. [Lectura de Settings](#lectura-de-settings)
3. [Configuración de Proxy](#configuración-de-proxy)
4. [Uso de Modelos Configurables](#uso-de-modelos-configurables)

---

## 🎯 El Problema

Por defecto, el SDK de Anthropic:
- Se conecta directamente a `https://api.anthropic.com`
- Requiere API key hardcodeada
- Usa nombres de modelo fijos

**Este proyecto soluciona:**
- ✅ Leer configuración desde archivos
- ✅ Usar proxy local si está configurado
- ✅ Cambiar modelos sin tocar código
- ✅ No hardcodear API keys

**Solución:** Sistema de lectura de configuración en `claude_config.py`

---

## 📂 Lectura de Settings

### Ubicaciones buscadas

El proyecto busca configuración en múltiples ubicaciones (en orden):

```python
config_paths = [
    Path.home() / ".claude-sdk" / "settings.json",
    Path.home() / ".claude" / "settings.json",
    Path.home() / ".claude-sdk" / ".claude.json",
    Path(".") / "settings.json",
    Path(".") / ".claude.json",
]
```

### Estructura del archivo

**Ejemplo:** `~/.claude-sdk/settings.json`

```json
{
  "env": {
    "ANTHROPIC_API_KEY": "sk-ant-api03-...",
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-4",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-3.5",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "gpt-4.1"
  }
}
```

### Implementación de lectura

<augment_code_snippet path="claude_config.py" mode="EXCERPT">
```python
def get_anthropic_config_from_claude():
    """Obtiene la configuración de Anthropic desde archivos de configuración"""
    config_paths = [
        Path.home() / ".claude-sdk" / "settings.json",
        Path.home() / ".claude" / "settings.json",
        Path(".") / "settings.json",
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                
                # Buscar en la sección 'env'
                if 'env' in config:
                    api_key = config['env'].get('ANTHROPIC_API_KEY')
                    base_url = config['env'].get('ANTHROPIC_BASE_URL')
                    
                    # Leer modelos configurados
                    models_config = {}
                    for key in ['ANTHROPIC_DEFAULT_HAIKU_MODEL', 
                                'ANTHROPIC_DEFAULT_SONNET_MODEL', 
                                'ANTHROPIC_DEFAULT_OPUS_MODEL']:
                        if key in config['env']:
                            model_type = key.replace('ANTHROPIC_DEFAULT_', '').lower().replace('_MODEL', '')
                            models_config[model_type] = config['env'][key]
                    
                    if api_key:
                        return api_key, base_url, models_config
    
    return None, None, {}
````
</augment_code_snippet>

### ¿Qué hace?

1. **Busca archivos** en múltiples ubicaciones
2. **Lee la sección `env`** del JSON
3. **Extrae:**
   - `ANTHROPIC_API_KEY`: Credencial de autenticación
   - `ANTHROPIC_BASE_URL`: URL del proxy (opcional)
   - `ANTHROPIC_DEFAULT_*_MODEL`: Nombres de modelos personalizados

---

## 🌐 Configuración de Proxy

### ¿Qué es el base_url?

El parámetro `base_url` permite redirigir las peticiones del SDK a un servidor diferente:

```python
# Sin proxy (default)
client = Anthropic(api_key="sk-ant-...")
# → Conecta a https://api.anthropic.com

# Con proxy
client = Anthropic(
    api_key="sk-ant-...",
    base_url="http://localhost:4000"  # ← Proxy local
)
# → Conecta a http://localhost:4000
```

### Implementación en el proyecto

<augment_code_snippet path="claude_config.py" mode="EXCERPT">
```python
def get_anthropic_client_with_permissions():
    """Obtiene una instancia del cliente Anthropic con configuración de permisos."""
    api_key, base_url, _ = get_anthropic_config_from_claude()
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no encontrada")

    # Si hay una URL base (proxy), usarla
    client_params = {"api_key": api_key}
    if base_url:
        client_params["base_url"] = base_url  # ← Aquí se configura el proxy

    return Anthropic(**client_params)
````
</augment_code_snippet>

### ¿Por qué usar proxy?

En este proyecto, el proxy permite:
- **Usar modelos alternativos** (GPT-4, etc.) con la API de Claude
- **Testing local** sin llamar a APIs reales
- **Centralizar configuración** de múltiples modelos

**Ejemplo de configuración:**

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "gpt-4.1"
  }
}
```

El proxy en `localhost:4000` traduce las peticiones de Claude a GPT-4.

---

## 🔄 Uso de Modelos Configurables

### Lectura de modelos desde settings

<augment_code_snippet path="claude_config.py" mode="EXCERPT">
```python
def get_models_config():
    """Obtiene la configuración de modelos desde archivos de configuración"""
    _, _, models_config = get_anthropic_config_from_claude()

    # Normalizar nombres (quitar '_model' del final)
    normalized_config = {}
    for key, value in models_config.items():
        normalized_key = key.replace('_model', '')
        normalized_config[normalized_key] = value

    return normalized_config
````
</augment_code_snippet>

**Ejemplo de configuración:**

```json
{
  "env": {
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-3.5",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-4",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "gpt-4.1"
  }
}
```

**Resultado:**

```python
models = get_models_config()
# {'haiku': 'claude-haiku-3.5', 'sonnet': 'claude-sonnet-4', 'opus': 'gpt-4.1'}
```

### Uso en el agente

<augment_code_snippet path="advanced_claude_agent.py" mode="EXCERPT">
```python
class ClaudeYouTubeAnalyzer:
    def __init__(self):
        self.client = get_anthropic_client_with_permissions()
        self.models_config = get_models_config()

        # Usar modelo configurado o default
        self.model = self.models_config.get(
            'sonnet',
            'claude-3-sonnet-20240229'
        )
````
</augment_code_snippet>

### Cambiar de modelo sin tocar código

**1. Editar `settings.json`:**

```json
{
  "env": {
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "gpt-4.1"
  }
}
```

**2. El código sigue igual:**

```python
agent = ClaudeYouTubeAnalyzer()  # Automáticamente usa gpt-4.1
```

---

## � Resumen

### Flujo completo

```
settings.json
    ↓
get_anthropic_config_from_claude()
    ↓
api_key, base_url, models_config
    ↓
Anthropic(api_key, base_url)
    ↓
client.messages.create(model=models['sonnet'])
    ↓
Proxy (si está configurado) → API real
```

### Ventajas

| Ventaja | Descripción |
|---------|-------------|
| **Sin hardcodear** | API keys y modelos en archivos |
| **Flexibilidad** | Cambia de modelo editando JSON |
| **Proxy opcional** | Usa proxy local si lo necesitas |
| **Multi-modelo** | Soporta diferentes proveedores |

### Configuración de Embeddings

El proyecto también configura embeddings de forma similar:

<augment_code_snippet path="claude_config.py" mode="EXCERPT">
```python
def get_embedding_config():
    """Config de embeddings: base_url, api_key y modelo"""
    base_url = os.environ.get("EMBEDDINGS_BASE_URL") or "http://localhost:4141"
    api_key = os.environ.get("EMBEDDINGS_API_KEY") or "api-placeholder"
    model = os.environ.get("EMBEDDINGS_MODEL") or "text-embedding-ada-002"
    return base_url.rstrip('/'), api_key, model
````
</augment_code_snippet>

---

**¡Listo!** Así es como este proyecto maneja configuración, proxy y modelos. 🚀

