import os
from typing import Iterable, List, Optional
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv

from backend.app.schemas import GenerationDefaults, ModelOption, SettingsResponse
from backend.shared.helpers import get_default_song_params

# Ensure .env is loaded so the API can surface real configuration values.
load_dotenv()


def _split_model_list(raw_value: Optional[str]) -> List[str]:
    if not raw_value:
        return []
    return [model.strip() for model in raw_value.replace("\n", ",").split(",") if model.strip()]


def _is_placeholder(value: Optional[str]) -> bool:
    normalized = (value or "").strip().lower()
    return normalized in {"", "none", "null", "your_openrouter_api_key_here"}


def _display_model_name(model_id: str, name: Optional[str] = None) -> str:
    return (name or model_id).replace("openrouter/", "", 1)


def _dedupe_options(options: Iterable[ModelOption]) -> List[ModelOption]:
    deduped: dict[str, ModelOption] = {}
    for option in options:
        if not option.id:
            continue
        existing = deduped.get(option.id)
        if existing:
            existing.recommended = existing.recommended or option.recommended
            if not existing.name and option.name:
                existing.name = option.name
            continue
        deduped[option.id] = option
    return sorted(
        deduped.values(),
        key=lambda item: (not item.recommended, item.source, (item.name or item.id).lower()),
    )


def _openrouter_option_id(model_id: str) -> str:
    if model_id.startswith("openrouter/"):
        return model_id
    return f"openrouter/{model_id}"


def _fetch_openrouter_models(recommended: set[str], configured_model: str) -> List[ModelOption]:
    models_url = os.getenv("OPENROUTER_MODELS_URL", "https://openrouter.ai/api/v1/models")
    timeout = float(os.getenv("MODEL_LIST_TIMEOUT_SECONDS", "2.5"))
    headers = {}
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("LITELLM_API_KEY")
    if not _is_placeholder(api_key):
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.get(models_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return []

    raw_models = payload.get("data", []) if isinstance(payload, dict) else []
    options: List[ModelOption] = []
    for item in raw_models:
        if not isinstance(item, dict):
            continue
        raw_id = str(item.get("id") or "").strip()
        if not raw_id:
            continue
        model_id = _openrouter_option_id(raw_id)
        options.append(
            ModelOption(
                id=model_id,
                name=_display_model_name(model_id, item.get("name")),
                source="remote",
                recommended=model_id in recommended or raw_id in recommended or model_id == configured_model,
            )
        )
    return options


def _local_models_url(base_url: Optional[str]) -> Optional[str]:
    if not base_url:
        return None
    normalized = base_url.rstrip("/") + "/"
    return urljoin(normalized, "models")


def _fetch_local_models(recommended: set[str], configured_model: str, local_url: Optional[str]) -> List[ModelOption]:
    models_url = os.getenv("LOCAL_LLM_MODELS_URL") or _local_models_url(local_url)
    if not models_url:
        return []

    headers = {}
    api_key = os.getenv("LMSTUDIO_API_KEY")
    if not _is_placeholder(api_key):
        headers["Authorization"] = f"Bearer {api_key}"

    timeout = float(os.getenv("MODEL_LIST_TIMEOUT_SECONDS", "2.5"))
    try:
        response = requests.get(models_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return []

    raw_models = payload.get("data", []) if isinstance(payload, dict) else []
    options: List[ModelOption] = []
    for item in raw_models:
        if isinstance(item, dict):
            model_id = str(item.get("id") or item.get("name") or "").strip()
            name = str(item.get("name") or model_id).strip()
        else:
            model_id = str(item).strip()
            name = model_id
        if not model_id:
            continue
        options.append(
            ModelOption(
                id=model_id,
                name=name,
                source="local",
                recommended=model_id in recommended or model_id == configured_model,
            )
        )
    return options


def _build_model_options(
    configured_remote_model: str,
    configured_local_model: str,
    recommended_remote_models: List[str],
    recommended_local_models: List[str],
    local_url: Optional[str],
) -> List[ModelOption]:
    remote_recommended = set(recommended_remote_models)
    local_recommended = set(recommended_local_models)
    options: List[ModelOption] = [
        ModelOption(
            id=configured_remote_model,
            name=_display_model_name(configured_remote_model),
            source="remote",
            recommended=True,
        ),
        ModelOption(
            id=configured_local_model,
            name=configured_local_model,
            source="local",
            recommended=True,
        ),
    ]
    options.extend(
        ModelOption(
            id=model,
            name=_display_model_name(model),
            source="remote",
            recommended=True,
        )
        for model in recommended_remote_models
    )
    options.extend(
        ModelOption(id=model, name=model, source="local", recommended=True)
        for model in recommended_local_models
    )
    options.extend(_fetch_openrouter_models(remote_recommended, configured_remote_model))
    options.extend(_fetch_local_models(local_recommended, configured_local_model, local_url))
    return _dedupe_options(options)


def get_settings_payload() -> SettingsResponse:
    """Return consolidated settings for the frontend."""
    defaults = get_default_song_params()
    llm_provider = os.getenv("LITELLM_API_BASE", "openrouter")
    model = os.getenv("LITELLM_MODEL", "gpt-4o-mini")
    local_model = os.getenv("LMSTUDIO_LLM_MODEL", "local-model")
    regenerate_model = os.getenv("REGENERATE_LYRICS_MODEL") or model
    temperature = float(os.getenv("LITELLM_TEMPERATURE") or os.getenv("LLM_TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    use_local = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
    local_url = os.getenv("LMSTUDIO_BASE_URL") or None
    theme = os.getenv("UI_THEME", "dark")
    recommended_models = _split_model_list(os.getenv("RECOMMENDED_LYRICS_MODELS"))
    recommended_local_models = _split_model_list(os.getenv("RECOMMENDED_LOCAL_LYRICS_MODELS"))

    return SettingsResponse(
        generation=GenerationDefaults(**defaults),
        use_local=use_local,
        local_url=local_url,
        llm_provider=llm_provider,
        model=model,
        local_model=local_model,
        regenerate_model=regenerate_model,
        temperature=temperature,
        max_tokens=max_tokens,
        recommended_models=recommended_models,
        recommended_local_models=recommended_local_models,
        models=_build_model_options(
            model,
            local_model,
            recommended_models,
            recommended_local_models,
            local_url,
        ),
        ui={"theme": theme},
    )
