import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.shared.ai_functions import get_llm
from backend.shared.helpers import get_repo_root, remove_thinking_tags


def generate_song_proposal_ideas(
    source_prompt: str,
    count: int,
    use_local: bool,
) -> List[Dict[str, str]]:
    """Generate song prompt proposals from high-level user guidance."""
    prompt_creator_guidelines = _read_prompt_creator_guidelines()
    raw_response = get_llm(use_local).invoke(
        _build_song_proposal_prompt(prompt_creator_guidelines, source_prompt, count)
    )
    return _normalize_song_proposals(raw_response, count)


def _read_prompt_creator_guidelines() -> str:
    prompt_path = Path(get_repo_root()) / "prompts" / "prompt_creator.txt"
    if not prompt_path.exists():
        raise FileNotFoundError("prompts/prompt_creator.txt was not found.")
    return prompt_path.read_text(encoding="utf-8").strip()


def _build_song_proposal_prompt(
    prompt_creator_guidelines: str,
    source_prompt: str,
    count: int,
) -> str:
    return f"""
You create saved Song Master proposal ideas. Use the Prompt Creator guidelines below
as the structure standard for every generated song prompt.

Prompt Creator guidelines:
{prompt_creator_guidelines}

User guidance:
{source_prompt}

Generate exactly {count} distinct song prompt ideas. Each proposal must be ready to
paste into the Song Master "Song Prompt" field.

For each proposal:
- Give it a concise working title.
- Write a complete prompt that covers genre/style, theme/mood, structure, rhyme or
  meter guidance, length/complexity, unique imagery or storytelling elements,
  audience, inspiration references, and creative constraints.
- Encourage originality. Do not request copying lyrics, melodies, or a living
  artist's exact style.

Return JSON only in this exact shape:
{{
  "proposals": [
    {{
      "title": "Working title",
      "prompt": "Complete song prompt"
    }}
  ]
}}
""".strip()


def _normalize_song_proposals(raw_response: Optional[str], count: int) -> List[Dict[str, str]]:
    parsed = _parse_json_response(raw_response)
    raw_proposals = _extract_proposal_list(parsed)
    proposals: List[Dict[str, str]] = []

    for index, item in enumerate(raw_proposals):
        proposal = _normalize_proposal_item(item, index)
        if proposal:
            proposals.append(proposal)

    if len(proposals) < count:
        raise ValueError(f"Expected {count} proposals but received {len(proposals)} usable proposals.")

    return proposals[:count]


def _parse_json_response(raw_response: Optional[str]) -> Any:
    if not raw_response:
        raise ValueError("The model did not return a response.")

    clean_response = remove_thinking_tags(raw_response).strip()
    clean_response = _strip_markdown_code_fence(clean_response)

    try:
        return json.loads(clean_response)
    except json.JSONDecodeError:
        json_match = re.search(r"(\{.*\}|\[.*\])", clean_response, flags=re.DOTALL)
        if not json_match:
            raise ValueError("The model did not return valid JSON.")
        return json.loads(json_match.group(1))


def _strip_markdown_code_fence(value: str) -> str:
    fence_match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", value, flags=re.DOTALL | re.IGNORECASE)
    return fence_match.group(1).strip() if fence_match else value


def _extract_proposal_list(parsed: Any) -> List[Any]:
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ("proposals", "song_proposals", "ideas", "song_prompt_ideas"):
            value = parsed.get(key)
            if isinstance(value, list):
                return value
    raise ValueError("The model response did not include a proposals list.")


def _normalize_proposal_item(item: Any, index: int) -> Optional[Dict[str, str]]:
    if isinstance(item, str):
        prompt = item.strip()
        title = f"Song Proposal {index + 1}"
    elif isinstance(item, dict):
        title = str(
            item.get("title")
            or item.get("name")
            or item.get("song_title")
            or f"Song Proposal {index + 1}"
        ).strip()
        prompt = str(
            item.get("prompt")
            or item.get("song_prompt")
            or item.get("idea")
            or item.get("description")
            or ""
        ).strip()
    else:
        return None

    if not prompt:
        return None

    return {
        "title": title[:255] or f"Song Proposal {index + 1}",
        "prompt": prompt,
    }
