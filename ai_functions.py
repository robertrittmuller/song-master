import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from litellm import completion

load_dotenv()

# Initialize LLM lazily to avoid key requirements at import time
llm = None


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
    global llm
    if llm is not None:
        return llm

    temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))

    if use_local:
        lmstudio_api_key = os.getenv("LMSTUDIO_API_KEY")
        lmstudio_base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        lmstudio_model = os.getenv("LMSTUDIO_LLM_MODEL", "local-model")

        if not lmstudio_api_key or lmstudio_api_key == "your_openrouter_api_key_here":
            lmstudio_api_key = "lm-studio"

        import openai

        class LMStudioLLM:
            def __init__(self, model: str, temperature: float, max_tokens: int, api_key: str, base_url: str):
                self.model = model
                self.temperature = temperature
                self.max_tokens = max_tokens
                self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

            def invoke(self, prompt: str) -> str:
                try:
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                    )
                    return completion.choices[0].message.content
                except Exception as chat_exc:
                    try:
                        completion = self.client.completions.create(
                            model=self.model,
                            prompt=prompt,
                            max_tokens=self.max_tokens,
                            temperature=self.temperature,
                        )
                        return completion.choices[0].text
                    except Exception as completion_exc:
                        raise ValueError(
                            "LM Studio connection failed. Tried both chat and completions endpoints. "
                            f"Original errors: {chat_exc}, {completion_exc}"
                        ) from completion_exc

        llm = LMStudioLLM(
            model=lmstudio_model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=lmstudio_api_key,
            base_url=lmstudio_base_url,
        )
        return llm

    litellm_model = os.getenv("LITELLM_MODEL")
    litellm_api_key = os.getenv("LITELLM_API_KEY")
    litellm_base_url = os.getenv("LITELLM_API_BASE")

    if litellm_model:
        llm = LiteLLMWrapper(
            model=litellm_model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=litellm_api_key,
            base_url=litellm_base_url,
        )
        return llm

    model = os.getenv("LLM_MODEL", "openai/gpt-3.5-turbo")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    if openrouter_api_key and openrouter_api_key != "your_openrouter_api_key_here":
        import openai

        class OpenRouterLLM:
            def __init__(self, model: str, temperature: float, max_tokens: int, api_key: str, base_url: str):
                self.model = model
                self.temperature = temperature
                self.max_tokens = max_tokens
                self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

            def invoke(self, prompt: str) -> str:
                completion = self.client.completions.create(
                    model=self.model,
                    prompt=prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                return completion.choices[0].text

        llm = OpenRouterLLM(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=openrouter_api_key,
            base_url=openrouter_base_url,
        )
        return llm

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("Neither OPENROUTER_API_KEY nor OPENAI_API_KEY found in environment variables")

    llm = OpenAI(
        temperature=temperature,
        model=model,
        max_tokens=max_tokens,
        openai_api_key=openai_api_key,
    )
    return llm


def build_prompts():
    """Build and return all prompt templates for song generation."""
    from helpers import read_prompt

    song_drafter_template = read_prompt("song_drafter")
    song_review_template = read_prompt("song_review")
    song_critic_template = read_prompt("song_critic")
    song_preflight_template = read_prompt("song_preflight")
    metadata_template = (
        "You are preparing concise metadata for a Suno song render.\n"
        "- Provide a 1-2 sentence description of the song's theme and style.\n"
        "- Suggest 3-6 Suno style tokens that best fit the song (concise, lower case).\n"
        "- Suggest 0-3 Suno style tokens to avoid if any conflict appears.\n"
        "- Suggest a concise target audience and a one-line commercial potential assessment.\n"
        "- Return only JSON with keys: description (string), suno_styles (list of strings), suno_exclude_styles (list of strings), target_audience (string), commercial_potential (string).\n"
        "- Do not include explanations or markdown."
    )
    preflight_triage_template = (
        "You are a strict validator. Given preflight feedback text, output JSON with keys:\n"
        '- "pass" (boolean), true only if the text clearly signals no action needed.\n'
        '- "issues" (array of short actionable strings). Empty if pass is true.\n'
        "Be concise. No markdown, no prose—JSON only."
    )
    scoring_template = (
        "You are a songwriting judge scoring the lyrics for production readiness.\n"
        "- Score from 0-10 (float) considering structure, imagery, singability, theme coherence, and avoidance of clichés.\n"
        "- Keep rationale to one short sentence.\n"
        "- Return only JSON like {{\"score\": 8.4, \"rationale\": \"...\"}} with no extra text."
    )
    song_revision_template = (
        "You are a skilled songwriter. Revise the lyrics based on the reviewer feedback.\n"
        "- Keep the structure (sections, order, and counts) unless the feedback explicitly asks to change it.\n"
        "- Improve clarity, imagery, and singability per the feedback.\n"
        "- Keep the title and metadata untouched.\n"
        "- CRITICAL: Ensure total lyrics remain under 2500 characters including spaces and punctuation. If feedback suggests additions that would exceed the limit, prioritize condensing existing content or removing less essential sections.\n"
        "- Return only the revised lyrics, no commentary."
    )

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
        input_variables=["lyrics"],
        template=f"""
{song_review_template}

Lyrics: {{lyrics}}
""",
    )

    song_critic_prompt = PromptTemplate(
        input_variables=["lyrics"],
        template=f"""
{song_critic_template}

Lyrics: {{lyrics}}
""",
    )

    song_preflight_prompt = PromptTemplate(
        input_variables=["lyrics", "styles", "tags"],
        template=f"""
{song_preflight_template}

Styles: {{styles}}
Tags: {{tags}}

Lyrics: {{lyrics}}
""",
    )

    song_revision_prompt = PromptTemplate(
        input_variables=["lyrics", "feedback"],
        template=f"""{song_revision_template}

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


def revise_lyrics(prompt_template: PromptTemplate, lyrics: str, feedback: str, use_local: bool) -> str:
    formatted_prompt = prompt_template.format(lyrics=lyrics, feedback=feedback)
    return get_llm(use_local).invoke(formatted_prompt)


def run_parallel_reviews(prompt_template: PromptTemplate, lyrics: str, use_local: bool, reviewer_count: int = 3) -> str:
    """Run multiple AI reviewers in parallel and merge their feedback."""
    def _call(_):
        formatted_prompt = prompt_template.format(lyrics=lyrics)
        return get_llm(use_local).invoke(formatted_prompt)

    with ThreadPoolExecutor(max_workers=reviewer_count) as executor:
        feedbacks = list(executor.map(_call, range(reviewer_count)))
    merged = "\n\n".join([f"Reviewer {idx + 1} Feedback:\n{fb}" for idx, fb in enumerate(feedbacks)])
    return merged


def score_lyrics(prompt_template: PromptTemplate, lyrics: str, use_local: bool) -> float:
    formatted_prompt = prompt_template.format(lyrics=lyrics)
    try:
        raw = get_llm(use_local).invoke(formatted_prompt)
        parsed = json.loads(raw)
        return float(parsed.get("score", 0))
    except Exception:
        return 0.0


def review_song(prompt_template: PromptTemplate, revision_prompt: PromptTemplate, scoring_prompt: PromptTemplate, lyrics: str, use_local: bool, reviewer_count: int = 3, score_threshold: float = 8.0, max_rounds: int = 2) -> str:
    for _ in range(max_rounds):
        feedback = run_parallel_reviews(prompt_template, lyrics, use_local, reviewer_count=reviewer_count)
        lyrics = revise_lyrics(revision_prompt, lyrics, feedback, use_local)
        score = score_lyrics(scoring_prompt, lyrics, use_local)
        if score >= score_threshold:
            break
    return lyrics


def critique_song(prompt_template: PromptTemplate, revision_prompt: PromptTemplate, lyrics: str, use_local: bool) -> str:
    formatted_prompt = prompt_template.format(lyrics=lyrics)
    feedback = get_llm(use_local).invoke(formatted_prompt)
    return revise_lyrics(revision_prompt, lyrics, feedback, use_local)


def preflight_song(prompt_template: PromptTemplate, lyrics: str, styles: Dict[str, str], tags: Dict[str, str], use_local: bool) -> None:
    formatted_prompt = prompt_template.format(lyrics=lyrics, styles=str(styles), tags=str(tags))
    return get_llm(use_local).invoke(formatted_prompt)


def triage_preflight(prompt_template: PromptTemplate, preflight_output: str, use_local: bool):
    """Parse preflight feedback and determine if issues exist."""
    fallback = {"pass": False, "issues": ["Preflight feedback could not be parsed. Review manually."]}
    if not preflight_output:
        return fallback
    formatted = prompt_template.format(preflight_output=preflight_output)
    try:
        raw = get_llm(use_local).invoke(formatted)
        parsed = json.loads(raw)
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
        parsed = json.loads(raw)
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