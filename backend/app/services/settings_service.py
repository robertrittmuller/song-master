import os

from dotenv import load_dotenv

from backend.app.schemas import GenerationDefaults, SettingsResponse
from helpers import get_default_song_params

# Ensure .env is loaded so the API can surface real configuration values.
load_dotenv()


def get_settings_payload() -> SettingsResponse:
    """Return consolidated settings for the frontend."""
    defaults = get_default_song_params()
    llm_provider = os.getenv("LITELLM_API_BASE", "openrouter")
    model = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("LITELLM_TEMPERATURE", "0.6"))
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    use_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    local_url = os.getenv("LMSTUDIO_BASE_URL") or None
    theme = os.getenv("UI_THEME", "dark")

    return SettingsResponse(
        generation=GenerationDefaults(**defaults),
        use_local=use_local,
        local_url=local_url,
        llm_provider=llm_provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        ui={"theme": theme},
    )
