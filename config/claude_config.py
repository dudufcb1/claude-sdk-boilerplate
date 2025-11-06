import json
from pathlib import Path
from anthropic import Anthropic


def get_config():
    """Lee la configuración desde settings"""
    config_path = Path.home() / ".claude-sdk" / "settings.json"

    if not config_path.exists():
        raise ValueError(f"Settings no encontrado en {config_path}")

    with open(config_path, 'r') as f:
        config = json.load(f)

    if 'env' not in config:
        raise ValueError("Sección 'env' no encontrada en settings")

    return config['env']


def get_anthropic_client():
    """Obtiene cliente de Anthropic desde settings locales, usaremos únicamente nuestros settings de sdk"""
    env = get_config()

    api_key = env.get('ANTHROPIC_AUTH_TOKEN')
    base_url = env.get('ANTHROPIC_BASE_URL')

    if not api_key:
        raise ValueError("ANTHROPIC_AUTH_TOKEN no encontrado en settings")

    client_params = {"api_key": api_key}
    if base_url:
        client_params["base_url"] = base_url.rstrip('/')

    return Anthropic(**client_params)


def get_model():
    """Obtiene el modelo desde settings (ANTHROPIC_DEFAULT_SONNET_MODEL)"""
    env = get_config()
    model = env.get('ANTHROPIC_DEFAULT_SONNET_MODEL', 'gpt-4.1')
    return model

