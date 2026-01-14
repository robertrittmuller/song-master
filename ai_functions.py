import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
import litellm
from litellm import completion

load_dotenv()


def _is_truthy_env(value: Optional[str]) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _is_real_langfuse_key(value: Optional[str]) -> bool:
    if not value:
        return False
    trimmed = value.strip()
    if not trimmed:
        return False
    lowered = trimmed.lower()
    return not lowered.startswith("your_langfuse_")


def _check_langfuse_server_available() -> bool:
    """Check if the langfuse server is reachable before enabling langfuse."""
    import socket
    host = os.getenv("LANGFUSE_HOST", "http://localhost:3000").replace("http://", "").replace("https://", "").split("/")[0]
    port = 3000
    if ":" in host:
        host, port_str = host.split(":")
        port = int(port_str)
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


_LANGFUSE_ACTIVE = (
    _is_truthy_env(os.getenv("LANGFUSE_ENABLED"))
    and _is_real_langfuse_key(os.getenv("LANGFUSE_PUBLIC_KEY"))
    and _is_real_langfuse_key(os.getenv("LANGFUSE_SECRET_KEY"))
    and _check_langfuse_server_available()
)

if _LANGFUSE_ACTIVE:
    from langfuse.openai import openai
else:
    import openai

_LANGFUSE_CONFIGURED = False
_LANGFUSE_LANGCHAIN_HANDLER = None


def _get_litellm_langfuse_callback() -> Optional[str]:
    if not _LANGFUSE_ACTIVE:
        return None
    try:
        from langfuse import Langfuse
    except Exception:
        return None
    if hasattr(Langfuse, "trace"):
        return "langfuse"
    return "langfuse_otel"


def _patch_langfuse_sdk_integration() -> None:
    if not _LANGFUSE_ACTIVE:
        return
    try:
        import inspect
        from langfuse import Langfuse
    except Exception:
        return
    if "sdk_integration" in inspect.signature(Langfuse.__init__).parameters:
        return
    original_init = Langfuse.__init__

    def _patched_init(self, *args, **kwargs):
        kwargs.pop("sdk_integration", None)
        return original_init(self, *args, **kwargs)

    Langfuse.__init__ = _patched_init


def _configure_langfuse() -> None:
    global _LANGFUSE_CONFIGURED, _LANGFUSE_ACTIVE
    if _LANGFUSE_CONFIGURED or not _LANGFUSE_ACTIVE:
        return
    _LANGFUSE_CONFIGURED = True
    callback_name = _get_litellm_langfuse_callback()
    if not callback_name:
        return
    try:
        for callback_list in (litellm.success_callback, litellm.failure_callback):
            if callback_name not in callback_list:
                callback_list.append(callback_name)
    except Exception as e:
        # Log the error but don't fail - langfuse server may be unavailable
        import logging
        logging.warning(f"Failed to configure langfuse callback (langfuse server may be down): {e}")
        # Disable langfuse to prevent further connection attempts
        _LANGFUSE_ACTIVE = False


def _get_langfuse_langchain_handler():
    global _LANGFUSE_LANGCHAIN_HANDLER, _LANGFUSE_ACTIVE
    if not _LANGFUSE_ACTIVE:
        return None
    if _LANGFUSE_LANGCHAIN_HANDLER is None:
        try:
            from langfuse.langchain import CallbackHandler
        except Exception:
            return None
        try:
            _LANGFUSE_LANGCHAIN_HANDLER = CallbackHandler()
        except Exception as e:
            # Log the error but don't fail - langfuse server may be unavailable
            import logging
            logging.warning(f"Failed to create langfuse handler (langfuse server may be down): {e}")
            # Disable langfuse to prevent further connection attempts
            _LANGFUSE_ACTIVE = False
            return None
    return _LANGFUSE_LANGCHAIN_HANDLER


_patch_langfuse_sdk_integration()
_configure_langfuse()

# LLM instance will be created fresh for every call to get_llm


class LMStudioLLM:
    def __init__(self, model: str, temperature: float, max_tokens: int, api_key: str, base_url: str):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

    def invoke(self, prompt: str) -> str:
        try:
            comp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            return comp.choices[0].message.content
        except Exception as chat_exc:
            try:
                comp = self.client.completions.create(
                    model=self.model,
                    prompt=prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                return comp.choices[0].text
            except Exception as completion_exc:
                raise ValueError(
                    "LM Studio connection failed. Tried both chat and completions endpoints. "
                    f"Original errors: {chat_exc}, {completion_exc}"
                ) from completion_exc


class OpenRouterLLM:
    def __init__(self, model: str, temperature: float, max_tokens: int, api_key: str, base_url: str):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

    def invoke(self, prompt: str) -> str:
        comp = self.client.completions.create(
            model=self.model,
            prompt=prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return comp.choices[0].text


class LiteLLMWrapper:
    """Wrapper for LiteLLM API calls."""
    def __init__(self, model: str, temperature: float, max_tokens: int, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.base_url = base_url

    def invoke(self, prompt: str) -> str:
        kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if self.api_key and self.api_key != "your_openrouter_api_key_here":
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["api_base"] = self.base_url

        try:
            response = completion(**kwargs)
            return response.choices[0].message.content
        except Exception as exc:
            raise ValueError(f"LiteLLM call failed: {exc}") from exc


def get_llm(use_local: bool = False):

    temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    if use_local:
        lmstudio_api_key = os.getenv("LMSTUDIO_API_KEY", "lm-studio")
        lmstudio_base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        lmstudio_model = os.getenv("LMSTUDIO_LLM_MODEL", "local-model")

        return LMStudioLLM(
            model=lmstudio_model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=lmstudio_api_key,
            base_url=lmstudio_base_url,
        )

    litellm_model = os.getenv("LITELLM_MODEL")
    litellm_api_key = os.getenv("LITELLM_API_KEY")
    litellm_base_url = os.getenv("LITELLM_API_BASE")

    if litellm_model:
        return LiteLLMWrapper(
            model=litellm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=litellm_api_key,
            base_url=litellm_base_url,
        )

    model = os.getenv("LLM_MODEL", "openai/gpt-3.5-turbo")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    if openrouter_api_key and openrouter_api_key != "your_openrouter_api_key_here":
        return OpenRouterLLM(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=openrouter_api_key,
            base_url=openrouter_base_url,
        )

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("Neither OPENROUTER_API_KEY nor OPENAI_API_KEY found in environment variables")

    langfuse_handler = _get_langfuse_langchain_handler()
    return OpenAI(
        temperature=temperature,
        model=model,
        max_tokens=max_tokens,
        openai_api_key=openai_api_key,
        callbacks=[langfuse_handler] if langfuse_handler else None,
    )


def build_prompts():
    """Build and return all prompt templates for song generation."""
    from helpers import read_prompt, remove_thinking_tags

    song_drafter_template = read_prompt("song_drafter")
    song_review_template = read_prompt("song_review")
    song_critic_template = read_prompt("song_critic")
    song_preflight_template = read_prompt("song_preflight")
    metadata_template = read_prompt("song_metadata")
    preflight_triage_template = read_prompt("song_preflight_triage")
    scoring_template = read_prompt("song_scoring")
    song_revision_template = read_prompt("song_revision")

    song_drafter_prompt = PromptTemplate(
        input_variables=["user_input", "styles", "tags", "persona_styles", "default_params"],
        template=f"""
{song_drafter_template}

Data and Resources:
- Styles: {{styles}}
- Tags: {{tags}}
- Persona Styles: {{persona_styles}}
- Default Song Parameters: {{default_params}}

User Input: {{user_input}}

Use the default song parameters as a baseline when creating the song, but adapt them based on the user's specific request.
Output your draft as a basic song structure plus lyrics.
""",
    )

    song_review_prompt = PromptTemplate(
        input_variables=["lyrics", "user_input"],
        template=f"""
{song_review_template}

User Input: {{user_input}}

Lyrics: {{lyrics}}
""",
    )

    song_critic_prompt = PromptTemplate(
        input_variables=["lyrics", "user_input"],
        template=f"""
{song_critic_template}

User Input: {{user_input}}

Lyrics: {{lyrics}}
""",
    )

    song_preflight_prompt = PromptTemplate(
        input_variables=["lyrics", "styles", "tags", "user_input"],
        template=f"""
{song_preflight_template}

Styles: {{styles}}
Tags: {{tags}}

User Input: {{user_input}}

Lyrics: {{lyrics}}
""",
    )

    song_revision_prompt = PromptTemplate(
        input_variables=["lyrics", "feedback", "user_input"],
        template=f"""{song_revision_template}

User Input:
{{user_input}}

Lyrics:
{{lyrics}}

Reviewer Feedback:
{{feedback}}
""",
    )

    metadata_prompt = PromptTemplate(
        input_variables=["lyrics", "user_input", "default_params", "persona_styles"],
        template=f"""{metadata_template}

Lyrics:
{{lyrics}}

User Input:
{{user_input}}

Default Parameters:
{{default_params}}

Persona Styles:
{{persona_styles}}
""",
    )

    preflight_triage_prompt = PromptTemplate(
        input_variables=["preflight_output"],
        template=f"""{preflight_triage_template}

Preflight Feedback:
{{preflight_output}}
""",
    )

    song_score_prompt = PromptTemplate(
        input_variables=["lyrics"],
        template=f"""{scoring_template}

Lyrics:
{{lyrics}}
""",
    )

    return (
        song_drafter_prompt,
        song_review_prompt,
        song_critic_prompt,
        song_preflight_prompt,
        song_revision_prompt,
        song_score_prompt,
        metadata_prompt,
        preflight_triage_prompt,
    )


def draft_song(prompt_template: PromptTemplate, enhanced_input: str, styles: Dict[str, str], tags: Dict[str, str], persona_styles: str, default_params: Dict[str, Optional[str]], use_local: bool) -> str:
    formatted_prompt = prompt_template.format(
        user_input=enhanced_input,
        styles=str(styles),
        tags=str(tags),
        persona_styles=persona_styles,
        default_params=str(default_params),
    )
    return get_llm(use_local).invoke(formatted_prompt)


def revise_lyrics(
    prompt_template: PromptTemplate,
    lyrics: str,
    feedback: str,
    use_local: bool,
    user_input: str = "",
) -> str:
    formatted_prompt = prompt_template.format(lyrics=lyrics, feedback=feedback, user_input=user_input)
    return get_llm(use_local).invoke(formatted_prompt)


def run_parallel_reviews(
    prompt_template: PromptTemplate,
    lyrics: str,
    use_local: bool,
    reviewer_count: int = 3,
    user_input: str = "",
) -> str:
    """Run multiple AI reviewers in parallel and merge their feedback."""
    def _call(_):
        formatted_prompt = prompt_template.format(lyrics=lyrics, user_input=user_input)
        return get_llm(use_local).invoke(formatted_prompt)

    with ThreadPoolExecutor(max_workers=reviewer_count) as executor:
        feedbacks = list(executor.map(_call, range(reviewer_count)))
    merged = "\n\n".join([f"Reviewer {idx + 1} Feedback:\n{fb}" for idx, fb in enumerate(feedbacks)])
    return merged


def score_lyrics(prompt_template: PromptTemplate, lyrics: str, use_local: bool) -> float:
    formatted_prompt = prompt_template.format(lyrics=lyrics)
    try:
        raw = get_llm(use_local).invoke(formatted_prompt)
        from helpers import remove_thinking_tags
        clean_raw = remove_thinking_tags(raw)
        parsed = json.loads(clean_raw)
        return float(parsed.get("score", 0))
    except Exception:
        return 0.0


def review_song(
    prompt_template: PromptTemplate,
    revision_prompt: PromptTemplate,
    scoring_prompt: PromptTemplate,
    lyrics: str,
    use_local: bool,
    reviewer_count: int = 3,
    score_threshold: float = 8.0,
    max_rounds: int = 2,
    user_input: str = "",
) -> str:
    for _ in range(max_rounds):
        feedback = run_parallel_reviews(
            prompt_template, lyrics, use_local, reviewer_count=reviewer_count, user_input=user_input
        )
        lyrics = revise_lyrics(revision_prompt, lyrics, feedback, use_local, user_input=user_input)
        score = score_lyrics(scoring_prompt, lyrics, use_local)
        if score >= score_threshold:
            break
    return lyrics


def critique_song(
    prompt_template: PromptTemplate,
    revision_prompt: PromptTemplate,
    lyrics: str,
    use_local: bool,
    user_input: str = "",
) -> str:
    formatted_prompt = prompt_template.format(lyrics=lyrics, user_input=user_input)
    raw_feedback = get_llm(use_local).invoke(formatted_prompt)
    try:
        parsed = json.loads(raw_feedback)
        feedback = parsed.get("feedback", raw_feedback)
    except Exception:
        feedback = raw_feedback
    return revise_lyrics(revision_prompt, lyrics, feedback, use_local, user_input=user_input)


def preflight_song(
    prompt_template: PromptTemplate,
    lyrics: str,
    styles: Dict[str, str],
    tags: Dict[str, str],
    use_local: bool,
    user_input: str = "",
) -> str:
    formatted_prompt = prompt_template.format(lyrics=lyrics, styles=str(styles), tags=str(tags), user_input=user_input)
    return get_llm(use_local).invoke(formatted_prompt)


def triage_preflight(prompt_template: PromptTemplate, preflight_output: str, use_local: bool):
    """Parse preflight feedback and determine if issues exist."""
    fallback = {"pass": False, "issues": ["Preflight feedback could not be parsed. Review manually."]}
    if not preflight_output:
        return fallback
    formatted = prompt_template.format(preflight_output=preflight_output)
    try:
        raw = get_llm(use_local).invoke(formatted)
        from helpers import remove_thinking_tags
        clean_raw = remove_thinking_tags(raw)
        parsed = json.loads(clean_raw)
        passed = bool(parsed.get("pass", False))
        issues = parsed.get("issues", [])
        if isinstance(issues, str):
            issues = [issues]
        issues = [issue for issue in issues if issue]
        return {"pass": passed, "issues": issues}
    except Exception:
        return fallback


def generate_metadata_summary(prompt_template: PromptTemplate, lyrics: str, user_input: str, default_params: Dict[str, Optional[str]], persona_styles: str, use_local: bool):
    from helpers import parse_persona_styles_list

    persona_style_tokens = parse_persona_styles_list(persona_styles)
    fallback = {
        "description": "Short description of the song's theme and style.",
        "suno_styles": [default_params.get("genre", "rock"), *persona_style_tokens],
        "suno_exclude_styles": [],
        "target_audience": "Suggested demographic",
        "commercial_potential": "Assessment",
    }
    formatted_prompt = prompt_template.format(
        lyrics=lyrics,
        user_input=user_input,
        default_params=str(default_params),
        persona_styles=persona_styles or "None provided",
    )
    try:
        raw = get_llm(use_local).invoke(formatted_prompt)
        from helpers import remove_thinking_tags
        clean_raw = remove_thinking_tags(raw)
        parsed = json.loads(clean_raw)
        description = parsed.get("description") or fallback["description"]
        styles = parsed.get("suno_styles") or fallback["suno_styles"]
        exclude_styles = parsed.get("suno_exclude_styles") or fallback["suno_exclude_styles"]
        if isinstance(styles, str):
            styles = [styles]
        if isinstance(exclude_styles, str):
            exclude_styles = [exclude_styles]
        # Ensure persona tokens are included
        if persona_style_tokens:
            styles = list(dict.fromkeys(list(styles) + persona_style_tokens))
        target_audience = parsed.get("target_audience") or fallback["target_audience"]
        commercial_potential = parsed.get("commercial_potential") or fallback["commercial_potential"]
        return {
            "description": description,
            "suno_styles": styles,
            "suno_exclude_styles": exclude_styles,
            "target_audience": target_audience,
            "commercial_potential": commercial_potential,
        }
    except Exception:
        return fallback


def review_song_with_audio(lyrics: str, audio_path: str, use_local: bool) -> str:
    """
    Send the audio file and lyrics to a multimodal LLM for review.
    Returns the feedback string.
    """
    import base64
    from helpers import read_prompt

    if use_local:
        return "Audio review is not supported in local mode."

    # Load prompt
    system_prompt = read_prompt("live_listen")

    # Encode audio
    try:
        with open(audio_path, "rb") as audio_file:
            audio_base64 = base64.b64encode(audio_file.read()).decode("utf-8")
    except Exception as e:
        return f"Error reading audio file: {str(e)}"

    # Use the LiteLLM multimodal model for live feedback
    litellm_model = os.getenv("LITELLM_MULTIMODAL_MODEL")
    litellm_api_key = os.getenv("LITELLM_API_KEY")
    litellm_base_url = os.getenv("LITELLM_API_BASE")

    def _is_real_key(value: Optional[str]) -> bool:
        return bool(value and value != "your_openrouter_api_key_here")

    litellm_api_key = litellm_api_key if _is_real_key(litellm_api_key) else None

    if not litellm_model:
        return "Multimodal LLM error: LITELLM_MULTIMODAL_MODEL is not set."

    # Headers often required/recommended for OpenRouter
    extra_headers = {
        "HTTP-Referer": "https://github.com/robertrittmuller/song-master",
        "X-Title": "Song Master Web App",
    }

    try:
        kwargs = {
            "model": litellm_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{system_prompt}\n\nLyrics:\n{lyrics}"},
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_base64,
                                "format": "mp3"
                            }
                        }
                    ]
                }
            ],
            "extra_headers": extra_headers if "openrouter" in (litellm_base_url or "").lower() or "openrouter" in litellm_model.lower() else None
        }
        if litellm_api_key:
            kwargs["api_key"] = litellm_api_key
        if litellm_base_url:
            kwargs["api_base"] = litellm_base_url

        response = completion(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling multimodal LLM: {str(e)}"
