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


def _is_openrouter_target(model: Optional[str], base_url: Optional[str]) -> bool:
    """Return True when the LiteLLM request is targeting OpenRouter."""
    return "openrouter" in (model or "").lower() or "openrouter" in (base_url or "").lower()


def _get_litellm_extra_headers(model: Optional[str], base_url: Optional[str]) -> Optional[Dict[str, str]]:
    """Return app attribution headers for LiteLLM calls routed to OpenRouter."""
    if not _is_openrouter_target(model, base_url):
        return None

    return {
        "HTTP-Referer": os.getenv("LITELLM_APP_REFERER", "https://github.com/robertrittmuller/song-master"),
        "X-Title": os.getenv("LITELLM_APP_NAME", "SongMaster"),
    }


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
            "extra_headers": _get_litellm_extra_headers(self.model, self.base_url),
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

    temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
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


def build_prompts() -> Dict[str, Any]:
    """Build and return all prompt templates for song generation."""
    from helpers import read_prompt

    song_brief_template = read_prompt("song_brief")
    song_structure_template = read_prompt("song_structure_planner")
    song_drafter_template = read_prompt("song_drafter")
    song_theme_review_template = read_prompt("song_review_theme")
    song_wording_review_template = read_prompt("song_review_wording")
    song_suno_review_template = read_prompt("song_review_suno")
    metadata_template = read_prompt("song_metadata")
    song_revision_template = read_prompt("song_revision")

    return {
        "brief": PromptTemplate(
            input_variables=["user_input", "styles_context", "tags_context", "persona_styles", "default_params"],
            template=f"""
{song_brief_template}

Relevant Style Context:
{{styles_context}}

Relevant Tag Context:
{{tags_context}}

Persona Styles:
{{persona_styles}}

Default Song Parameters:
{{default_params}}

User Input:
{{user_input}}
""",
        ),
        "structure": PromptTemplate(
            input_variables=[
                "user_input",
                "brief",
                "structure_guidance",
                "tags_context",
                "allowed_section_names",
                "default_params",
            ],
            template=f"""
{song_structure_template}

Creative Brief:
{{brief}}

Structure Guidance:
{{structure_guidance}}

Relevant Suno Tag Context:
{{tags_context}}

Allowed Section Names:
{{allowed_section_names}}

Default Song Parameters:
{{default_params}}

User Input:
{{user_input}}
""",
        ),
        "draft": PromptTemplate(
            input_variables=[
                "user_input",
                "brief",
                "song_structure",
                "styles_context",
                "tags_context",
                "persona_styles",
                "default_params",
            ],
            template=f"""
{song_drafter_template}

Creative Brief:
{{brief}}

Song Structure Plan:
{{song_structure}}

Relevant Style Context:
{{styles_context}}

Relevant Tag Context:
{{tags_context}}

Persona Styles:
{{persona_styles}}

Default Song Parameters:
{{default_params}}

User Input:
{{user_input}}

Use the default song parameters as a baseline when creating the song, but adapt them based on the user's specific request.
Output your draft as a basic song structure plus lyrics.
""",
        ),
        "review_theme": PromptTemplate(
            input_variables=["lyrics", "user_input", "brief"],
            template=f"""
{song_theme_review_template}

Creative Brief:
{{brief}}

User Input:
{{user_input}}

Lyrics:
{{lyrics}}
""",
        ),
        "review_quality": PromptTemplate(
            input_variables=["lyrics", "user_input", "brief"],
            template=f"""
{song_wording_review_template}

Creative Brief:
{{brief}}

User Input:
{{user_input}}

Lyrics:
{{lyrics}}
""",
        ),
        "review_suno": PromptTemplate(
            input_variables=["lyrics", "user_input", "brief"],
            template=f"""
{song_suno_review_template}

Creative Brief:
{{brief}}

User Input:
{{user_input}}

Lyrics:
{{lyrics}}
""",
        ),
        "revision": PromptTemplate(
            input_variables=["lyrics", "feedback", "user_input", "brief"],
            template=f"""{song_revision_template}

Creative Brief:
{{brief}}

User Input:
{{user_input}}

Lyrics:
{{lyrics}}

Targeted Edit Plan:
{{feedback}}
""",
        ),
        "metadata": PromptTemplate(
            input_variables=["lyrics", "user_input", "default_params", "persona_styles", "brief"],
            template=f"""{metadata_template}

Creative Brief:
{{brief}}

Lyrics:
{{lyrics}}

User Input:
{{user_input}}

Default Parameters:
{{default_params}}

Persona Styles:
{{persona_styles}}
""",
        ),
    }


def _load_json_response(raw: Optional[str]) -> Optional[Any]:
    from helpers import remove_thinking_tags

    if raw is None:
        return None

    clean_raw = remove_thinking_tags(raw)
    try:
        return json.loads(clean_raw)
    except Exception:
        return None


def _coerce_string_list(value: Any, field_name: str) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_values = [value]
    elif isinstance(value, list):
        raw_values = value
    else:
        raise ValueError(f"Expected '{field_name}' to be a list of strings.")
    return [str(item).strip() for item in raw_values if str(item).strip()]


def _normalize_section_plan_payload(raw_sections: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw_sections, list) or not raw_sections:
        raise ValueError("The model did not return a usable section plan.")

    section_plan: List[Dict[str, Any]] = []
    for index, item in enumerate(raw_sections):
        if not isinstance(item, dict):
            raise ValueError(f"Section plan item {index + 1} must be an object.")

        name = str(item.get("name") or item.get("section") or "").strip()
        if not name:
            raise ValueError(f"Section plan item {index + 1} is missing a name.")

        goal = str(item.get("goal") or item.get("purpose") or "").strip()
        section_plan.append(
            {
                "name": name,
                "goal": goal,
                "tags": _coerce_string_list(item.get("tags"), f"sections[{index}].tags"),
                "style_tags": _coerce_string_list(item.get("style_tags"), f"sections[{index}].style_tags"),
            }
        )
    return section_plan


def _normalize_brief_payload(raw_payload: Any) -> Dict[str, Any]:
    if not isinstance(raw_payload, dict):
        raise ValueError("The model did not return a usable creative brief.")

    return {
        "theme": str(raw_payload.get("theme") or "").strip(),
        "point_of_view": str(raw_payload.get("point_of_view") or "").strip(),
        "emotional_arc": str(raw_payload.get("emotional_arc") or "").strip(),
        "hook_strategy": str(raw_payload.get("hook_strategy") or "").strip(),
        "imagery_anchors": _coerce_string_list(raw_payload.get("imagery_anchors"), "imagery_anchors"),
        "non_negotiables": _coerce_string_list(raw_payload.get("non_negotiables"), "non_negotiables"),
        "required_lines": _coerce_string_list(raw_payload.get("required_lines"), "required_lines"),
        "avoid_phrases": _coerce_string_list(raw_payload.get("avoid_phrases"), "avoid_phrases"),
        "suno_style_tokens": _coerce_string_list(raw_payload.get("suno_style_tokens"), "suno_style_tokens"),
        "section_plan": _normalize_section_plan_payload(raw_payload.get("section_plan")),
    }


def build_song_brief(
    prompt_template: PromptTemplate,
    user_input: str,
    styles_context: str,
    tags_context: str,
    persona_styles: str,
    default_params: Dict[str, Optional[str]],
    use_local: bool,
) -> Dict[str, Any]:
    formatted_prompt = prompt_template.format(
        user_input=user_input,
        styles_context=styles_context or "None provided",
        tags_context=tags_context or "None provided",
        persona_styles=persona_styles or "None provided",
        default_params=str(default_params),
    )
    raw_response = get_llm(use_local).invoke(formatted_prompt)
    parsed = _load_json_response(raw_response)
    return _normalize_brief_payload(parsed)


def plan_song_structure(
    prompt_template: PromptTemplate,
    user_input: str,
    brief: Dict[str, Any],
    structure_guidance: str,
    tags_context: str,
    default_params: Dict[str, Optional[str]],
    use_local: bool,
) -> List[Dict[str, Any]]:
    from helpers import get_allowed_structure_names

    allowed_section_names = get_allowed_structure_names(user_input, brief)
    formatted_prompt = prompt_template.format(
        user_input=user_input,
        brief=json.dumps(brief, ensure_ascii=True, indent=2),
        structure_guidance=structure_guidance,
        tags_context=tags_context or "None provided",
        allowed_section_names=", ".join(allowed_section_names),
        default_params=str(default_params),
    )
    parsed = _load_json_response(get_llm(use_local).invoke(formatted_prompt))
    if not isinstance(parsed, dict):
        raise ValueError("The model did not return a usable song structure.")
    return _normalize_section_plan_payload(parsed.get("sections") or parsed.get("section_plan"))


def draft_song(
    prompt_template: PromptTemplate,
    enhanced_input: str,
    song_structure: List[Dict[str, Any]],
    styles_context: str,
    tags_context: str,
    brief: Dict[str, Any],
    persona_styles: str,
    default_params: Dict[str, Optional[str]],
    use_local: bool,
) -> str:
    formatted_prompt = prompt_template.format(
        user_input=enhanced_input,
        brief=json.dumps(brief, ensure_ascii=True, indent=2),
        song_structure=json.dumps(song_structure, ensure_ascii=True, indent=2),
        styles_context=styles_context or "None provided",
        tags_context=tags_context or "None provided",
        persona_styles=persona_styles or "None provided",
        default_params=str(default_params),
    )
    return get_llm(use_local).invoke(formatted_prompt)


def revise_lyrics(
    prompt_template: PromptTemplate,
    lyrics: str,
    feedback: str,
    use_local: bool,
    user_input: str = "",
    brief: Optional[Dict[str, Any]] = None,
) -> str:
    formatted_prompt = prompt_template.format(
        lyrics=lyrics,
        feedback=feedback,
        user_input=user_input,
        brief=json.dumps(brief or {}, ensure_ascii=True, indent=2),
    )
    return get_llm(use_local).invoke(formatted_prompt)


def _normalize_review_issue(review_type: str, issue: Any) -> Optional[Dict[str, Any]]:
    if isinstance(issue, str):
        text = issue.strip()
        if not text:
            return None
        return {
            "review_type": review_type,
            "location": "General",
            "problem": text,
            "instruction": text,
            "priority": 2,
        }

    if not isinstance(issue, dict):
        return None

    priority_raw = issue.get("priority", 2)
    priority_mapping = {"high": 3, "medium": 2, "low": 1}
    if isinstance(priority_raw, str):
        priority = priority_mapping.get(priority_raw.strip().lower(), 2)
    else:
        try:
            priority = int(priority_raw)
        except (TypeError, ValueError):
            priority = 2
    priority = max(1, min(priority, 3))

    location = str(issue.get("location") or issue.get("section") or "General").strip()
    problem = str(issue.get("problem") or issue.get("issue") or "").strip()
    instruction = str(issue.get("instruction") or issue.get("fix") or problem).strip()
    if not instruction:
        return None

    return {
        "review_type": review_type,
        "location": location or "General",
        "problem": problem or instruction,
        "instruction": instruction,
        "priority": priority,
    }


def _normalize_review_payload(review_type: str, raw: str) -> Dict[str, Any]:
    parsed = _load_json_response(raw)
    if not isinstance(parsed, dict):
        summary = (raw or "").strip().splitlines()[0] if raw else ""
        return {"summary": summary[:220], "issues": []}

    issues = parsed.get("issues", [])
    if isinstance(issues, (str, dict)):
        issues = [issues]

    normalized_issues = []
    for issue in issues:
        normalized = _normalize_review_issue(review_type, issue)
        if normalized:
            normalized_issues.append(normalized)

    return {
        "summary": str(parsed.get("summary") or parsed.get("focus") or "").strip(),
        "issues": normalized_issues[:4],
    }


def run_specialized_reviews(
    review_prompts: Dict[str, PromptTemplate],
    lyrics: str,
    use_local: bool,
    user_input: str = "",
    brief: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run three focused reviewers and merge their issues into a compact edit plan."""
    brief_text = json.dumps(brief or {}, ensure_ascii=True, indent=2)

    def _call(item: tuple[str, PromptTemplate]) -> tuple[str, Dict[str, Any]]:
        review_type, prompt_template = item
        formatted_prompt = prompt_template.format(lyrics=lyrics, user_input=user_input, brief=brief_text)
        raw = get_llm(use_local).invoke(formatted_prompt)
        return review_type, _normalize_review_payload(review_type, raw)

    role_weights = {"theme": 3, "quality": 2, "suno": 1}
    merged_issues: List[Dict[str, Any]] = []
    raw_reviews: Dict[str, Dict[str, Any]] = {}

    with ThreadPoolExecutor(max_workers=len(review_prompts)) as executor:
        for review_type, payload in executor.map(_call, review_prompts.items()):
            raw_reviews[review_type] = payload
            merged_issues.extend(payload.get("issues", []))

    deduped_issues: List[Dict[str, Any]] = []
    seen = set()
    merged_issues.sort(
        key=lambda issue: (
            -int(issue.get("priority", 2)),
            -role_weights.get(str(issue.get("review_type", "")), 0),
            issue.get("location", ""),
        )
    )
    for issue in merged_issues:
        dedupe_key = (
            str(issue.get("location", "")).lower(),
            str(issue.get("instruction", "")).lower(),
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped_issues.append(issue)
        if len(deduped_issues) >= 6:
            break

    feedback_lines = []
    for issue in deduped_issues:
        label = issue.get("review_type", "review").upper()
        feedback_lines.append(
            f"- [{label}] [{issue['location']}] {issue['instruction']} "
            f"(problem: {issue['problem']}; priority: {issue['priority']})"
        )

    return {
        "reviews": raw_reviews,
        "issues": deduped_issues,
        "feedback": "\n".join(feedback_lines),
    }


def generate_metadata_summary(
    prompt_template: PromptTemplate,
    lyrics: str,
    user_input: str,
    default_params: Dict[str, Optional[str]],
    persona_styles: str,
    use_local: bool,
    brief: Optional[Dict[str, Any]] = None,
    no_live_performance: bool = False,
    style_catalog: Optional[Dict[str, str]] = None,
):
    from helpers import (
        build_live_performance_exclude_styles,
        map_artist_references_to_suno_styles,
        parse_persona_styles_list,
        sanitize_style_token_list,
    )

    style_catalog = style_catalog or {}

    persona_style_tokens = parse_persona_styles_list(persona_styles)
    planned_style_tokens = []
    if isinstance(brief, dict):
        raw_planned_styles = brief.get("suno_style_tokens", [])
        if isinstance(raw_planned_styles, str):
            planned_style_tokens = [token.strip() for token in raw_planned_styles.split(",") if token.strip()]
        elif isinstance(raw_planned_styles, list):
            planned_style_tokens = [str(token).strip() for token in raw_planned_styles if str(token).strip()]

    planned_style_tokens = sanitize_style_token_list(planned_style_tokens, no_live_performance)
    persona_style_tokens = sanitize_style_token_list(persona_style_tokens, no_live_performance)

    def finalize_suno_styles(raw_style_tokens: List[str]) -> List[str]:
        normalized_raw = sanitize_style_token_list(
            [str(token).strip() for token in raw_style_tokens if str(token).strip()],
            no_live_performance,
        )
        merged = planned_style_tokens + normalized_raw + persona_style_tokens
        merged = map_artist_references_to_suno_styles(merged, user_input, style_catalog)
        return sanitize_style_token_list(merged, no_live_performance)

    fallback_styles = finalize_suno_styles(
        [token for token in [default_params.get("genre"), *planned_style_tokens, *persona_style_tokens] if token]
    )
    fallback = {
        "description": "Short description of the song's theme and style.",
        "suno_styles": fallback_styles,
        "suno_exclude_styles": [],
        "target_audience": "Suggested demographic",
        "commercial_potential": "Assessment",
    }
    formatted_prompt = prompt_template.format(
        lyrics=lyrics,
        user_input=user_input,
        default_params=str(default_params),
        persona_styles=persona_styles or "None provided",
        brief=json.dumps(brief or {}, ensure_ascii=True, indent=2),
    )
    try:
        raw = get_llm(use_local).invoke(formatted_prompt)
        parsed = _load_json_response(raw)
        if not isinstance(parsed, dict):
            fallback["suno_exclude_styles"] = build_live_performance_exclude_styles(
                list(fallback["suno_exclude_styles"]),
                no_live_performance,
            )
            return fallback
        description = parsed.get("description") or fallback["description"]
        generated_styles = parsed.get("suno_styles") or fallback["suno_styles"]
        exclude_styles = parsed.get("suno_exclude_styles") or fallback["suno_exclude_styles"]
        if isinstance(generated_styles, str):
            generated_styles = [generated_styles]
        if isinstance(exclude_styles, str):
            exclude_styles = [exclude_styles]
        generated_styles = finalize_suno_styles(
            [str(style).strip() for style in generated_styles if str(style).strip()]
        )
        exclude_styles = build_live_performance_exclude_styles(
            [str(style).strip() for style in exclude_styles if str(style).strip()],
            no_live_performance,
        )
        target_audience = parsed.get("target_audience") or fallback["target_audience"]
        commercial_potential = parsed.get("commercial_potential") or fallback["commercial_potential"]
        return {
            "description": description,
            "suno_styles": generated_styles,
            "suno_exclude_styles": exclude_styles,
            "target_audience": target_audience,
            "commercial_potential": commercial_potential,
        }
    except Exception:
        fallback["suno_exclude_styles"] = build_live_performance_exclude_styles(
            list(fallback["suno_exclude_styles"]),
            no_live_performance,
        )
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
            "extra_headers": _get_litellm_extra_headers(litellm_model, litellm_base_url),
        }
        if litellm_api_key:
            kwargs["api_key"] = litellm_api_key
        if litellm_base_url:
            kwargs["api_base"] = litellm_base_url

        response = completion(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling multimodal LLM: {str(e)}"
