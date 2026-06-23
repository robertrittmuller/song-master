import os
from contextlib import nullcontext
from typing import Any, Callable, Optional

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from tqdm import tqdm

from backend.shared.ai_functions import (
    build_prompts,
    build_song_brief,
    draft_song,
    generate_metadata_summary,
    plan_song_structure,
    revise_lyrics,
    run_specialized_reviews,
)
from backend.shared.helpers import (
    SongState,
    apply_section_plan_tags_to_lyrics,
    build_compact_style_context,
    build_compact_tag_context,
    build_structure_guidance,
    contains_live_performance_terms,
    enhance_user_input,
    extract_song_details_for_art,
    extract_title,
    get_allowed_structure_names,
    generate_album_art,
    load_prompt_from_file,
    load_resources,
    normalize_album_art_aspect_ratio,
    parse_persona,
    remove_title_from_lyrics,
    remove_thinking_tags,
    sanitize_brief_for_no_live_performance,
    sanitize_live_performance_text_block,
    save_song,
)

load_dotenv()

ProgressCallback = Callable[[str, Optional[int]], None]


def generate_song_pipeline(
    user_input: str,
    use_local: bool = False,
    song_name: Optional[str] = None,
    persona: Optional[str] = None,
    style: Optional[str] = None,
    should_generate_art: bool = True,
    genre: Optional[str] = None,
    tempo: Optional[str] = None,
    key: Optional[str] = None,
    instruments: Optional[str] = None,
    mood: Optional[str] = None,
    vocal_gender: Optional[str] = None,
    rhyme_scheme: Optional[str] = None,
    lyrics_model: Optional[str] = None,
    generation_config: Optional[dict[str, Any]] = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> SongState:
    """
    Full lyric generation pipeline shared by the backend and any non-HTTP callers.
    Optionally accepts a progress callback to surface stage updates to the API layer.
    """

    def notify(message: str, progress: Optional[int] = None) -> None:
        if progress_callback:
            progress_callback(message, progress)
        else:
            prefix = "✓ " if progress is not None else ""
            tqdm.write(f"{prefix}{message}")

    def is_invalid_lyrics_output(text: Optional[str]) -> bool:
        cleaned = remove_thinking_tags(text or "").strip()
        if not cleaned:
            return True

        lowered = cleaned.lower()
        invalid_markers = (
            "no lyrics were provided",
            "lyrics were not provided",
            "please provide the lyrics",
            "please provide lyrics",
            "i need the lyrics",
        )
        if any(marker in lowered for marker in invalid_markers):
            return True

        non_empty_lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        if len(non_empty_lines) <= 1 and any(
            line.lower().startswith(("title:", "song title:", "## song title"))
            for line in non_empty_lines
        ):
            return True

        return False

    def coerce_lyrics_output(candidate: Optional[str], fallback: Optional[str] = None) -> str:
        cleaned = remove_thinking_tags(candidate or "").strip()
        if is_invalid_lyrics_output(cleaned):
            return remove_thinking_tags(fallback or "").strip()
        return cleaned

    prompts = build_prompts()

    persona_name = parse_persona(user_input, persona)
    resources = load_resources(persona_name)

    auto_select_fields = set()
    no_live_performance = False
    album_art_aspect_ratio = "3:4"
    if generation_config:
        raw_auto_fields = generation_config.get("auto_select_fields")
        if isinstance(raw_auto_fields, list):
            auto_select_fields = {str(field) for field in raw_auto_fields}
        no_live_performance = bool(generation_config.get("no_live_performance", False))
        album_art_aspect_ratio = normalize_album_art_aspect_ratio(
            generation_config.get("art_aspect_ratio")
        )

    for field in auto_select_fields:
        if field in resources.default_params:
            resources.default_params[field] = None

    # Override default parameters with user selections if provided
    if genre:
        resources.default_params["genre"] = genre
    if tempo:
        resources.default_params["tempo"] = tempo
    if key:
        resources.default_params["key"] = key
    if instruments:
        resources.default_params["instruments"] = instruments
    if mood:
        resources.default_params["mood"] = mood
    if vocal_gender:
        resources.default_params["vocal_gender"] = vocal_gender
    if rhyme_scheme:
        resources.default_params["rhyme_scheme"] = rhyme_scheme

    max_rounds = int(os.getenv("REVIEW_MAX_ROUNDS", "1"))

    prompt_user_input = enhance_user_input(user_input, song_name, style, vocal_gender, rhyme_scheme)
    sanitized_style = None if (no_live_performance and contains_live_performance_terms(style)) else style
    style_context = build_compact_style_context(
        resources.styles,
        prompt_user_input,
        resources.default_params,
        resources.persona_styles,
        style=sanitized_style,
    )
    allowed_structure_names = get_allowed_structure_names(prompt_user_input)
    tag_context = build_compact_tag_context(
        resources.tags,
        prompt_user_input,
        resources.default_params,
        resources.persona_styles,
        style=sanitized_style,
        allowed_structure_names=allowed_structure_names,
    )
    style_context = sanitize_live_performance_text_block(style_context, no_live_performance)
    tag_context = sanitize_live_performance_text_block(tag_context, no_live_performance)
    structure_guidance = build_structure_guidance(
        prompt_user_input,
        {},
        resources.default_params,
        allowed_structure_names,
    )

    initial_state: SongState = {
        "user_input": user_input,
        "prompt_user_input": prompt_user_input,
        "song_name": song_name,
        "persona": persona,
        "persona_name": persona_name,
        "style": sanitized_style,
        "use_local": use_local,
        "resources": resources,
        "lyrics": "",
        "feedback": "",
        "score": 0.0,
        "round": 0,
        "max_rounds": max_rounds,
        "structure_plan": [],
        "review_issues": [],
        "suno_review_issues": [],
        "quality_review_issues": [],
        "needs_revision": False,
        "metadata": {},
        "brief": {},
        "filename": None,
        "album_art": None,
        "style_context": style_context,
        "tag_context": tag_context,
        "structure_guidance": structure_guidance,
        "vocal_gender": vocal_gender,
        "lyrics_model": lyrics_model,
        "generate_album_art": should_generate_art,
        "album_art_aspect_ratio": album_art_aspect_ratio,
        "no_live_performance": no_live_performance,
    }

    def brief_node(state: SongState):
        """Generate a compact creative brief before lyric drafting starts."""
        notify("Planning creative brief", 12)
        brief = build_song_brief(
            prompts["brief"],
            state["prompt_user_input"],
            state.get("style_context", ""),
            state.get("tag_context", ""),
            state["resources"].persona_styles,
            state["resources"].default_params,
            state["use_local"],
            model=state.get("lyrics_model"),
        )
        brief = sanitize_brief_for_no_live_performance(brief, state.get("no_live_performance", False))
        notify("Creative brief ready", 18)
        return {"brief": brief}

    def structure_node(state: SongState):
        """Select a constrained section scaffold from the creative brief."""
        structure_guidance = build_structure_guidance(
            state["prompt_user_input"],
            state.get("brief", {}),
            state["resources"].default_params,
            get_allowed_structure_names(state["prompt_user_input"], state.get("brief", {})),
        )
        notify("Planning song structure", 20)
        section_plan = plan_song_structure(
            prompts["structure"],
            state["prompt_user_input"],
            state.get("brief", {}),
            structure_guidance,
            state.get("tag_context", ""),
            state["resources"].default_params,
            state["use_local"],
            model=state.get("lyrics_model"),
        )
        updated_brief = dict(state.get("brief", {}))
        updated_brief["section_plan"] = section_plan
        notify("Song structure selected", 26)
        return {
            "brief": updated_brief,
            "structure_plan": section_plan,
            "structure_guidance": structure_guidance,
        }

    def draft_node(state: SongState):
        """Generate initial song draft using AI."""
        notify("Generating initial draft", 28)
        raw_lyrics = draft_song(
            prompt_template=prompts["draft"],
            enhanced_input=state["prompt_user_input"],
            song_structure=state.get("structure_plan") or state.get("brief", {}).get("section_plan", []),
            styles_context=state.get("style_context", ""),
            tags_context=state.get("tag_context", ""),
            brief=state.get("brief", {}),
            persona_styles=state["resources"].persona_styles,
            default_params=state["resources"].default_params,
            use_local=state["use_local"],
            model=state.get("lyrics_model"),
        )
        notify("Draft generated", 34)

        raw_lyrics = coerce_lyrics_output(raw_lyrics)
        if is_invalid_lyrics_output(raw_lyrics):
            raise ValueError("The model did not return usable lyrics for the initial draft.")

        # Extract title and clean lyrics
        title = extract_title(raw_lyrics, state.get("song_name"))
        clean_lyrics = remove_title_from_lyrics(raw_lyrics, title).strip()
        if is_invalid_lyrics_output(clean_lyrics):
            clean_lyrics = raw_lyrics
        clean_lyrics = apply_section_plan_tags_to_lyrics(
            clean_lyrics,
            state.get("structure_plan") or state.get("brief", {}).get("section_plan", []),
        )
        return {"lyrics": clean_lyrics, "song_name": title}

    def review_node(state: SongState):
        review_results = run_specialized_reviews(
            {
                "theme": prompts["review_theme"],
                "quality": prompts["review_quality"],
                "suno": prompts["review_suno"],
            },
            state["lyrics"],
            state["use_local"],
            user_input=state["prompt_user_input"],
            brief=state.get("brief", {}),
            model=state.get("lyrics_model"),
        )
        merged_issues = list(review_results.get("issues", []))

        notify(
            "Prompt-only review pass complete"
            + ("" if not merged_issues else f" with {len(merged_issues)} issue(s)"),
            42,
        )
        suno_issues = [issue for issue in merged_issues if str(issue.get("review_type")) == "suno"]
        quality_issues = [issue for issue in merged_issues if str(issue.get("review_type")) == "quality"]
        penalty = 0.0
        for issue in merged_issues:
            priority = int(issue.get("priority", 1))
            penalty += 2.5 if priority >= 3 else 1.0 if priority == 2 else 0.4
        score = max(0.0, 10.0 - penalty)
        needs_revision = any(int(issue.get("priority", 0)) >= 2 for issue in merged_issues)

        notify(
            "Review analysis ready"
            + ("" if not merged_issues else f" with {len(merged_issues)} issue(s)"),
            50 + min(state["round"] * 10, 10),
        )
        return {
            "suno_review_issues": suno_issues,
            "quality_review_issues": quality_issues,
            "review_issues": merged_issues,
            "feedback": str(review_results.get("feedback", "")).strip(),
            "needs_revision": needs_revision,
            "score": score,
        }

    def review_router(state: SongState):
        if state.get("needs_revision") and state["round"] < state["max_rounds"]:
            return "revise"
        return "metadata"

    def targeted_revise_node(state: SongState):
        """Apply one tightly scoped revision pass based on the merged review issues."""
        feedback = str(state.get("feedback", "")).strip()
        if not feedback:
            return {"round": state["round"] + 1}
        revised = coerce_lyrics_output(
            revise_lyrics(
                prompts["revision"],
                state["lyrics"],
                feedback,
                state["use_local"],
                user_input=state["prompt_user_input"],
                brief=state.get("brief", {}),
                model=state.get("lyrics_model"),
            ),
            fallback=state["lyrics"],
        )
        revised = apply_section_plan_tags_to_lyrics(
            revised,
            state.get("structure_plan") or state.get("brief", {}).get("section_plan", []),
        )
        notify("Applied targeted lyric fixes", 55)
        return {"lyrics": revised, "feedback": feedback, "round": state["round"] + 1}

    def metadata_node(state: SongState):
        metadata = generate_metadata_summary(
            prompts["metadata"],
            state["lyrics"],
            state["prompt_user_input"],
            state["resources"].default_params,
            state["resources"].persona_styles,
            state["use_local"],
            brief=state.get("brief", {}),
            no_live_performance=state.get("no_live_performance", False),
            style_catalog=state["resources"].styles,
            model=state.get("lyrics_model"),
        )
        # Merge default params into metadata to ensure they are persisted
        if isinstance(metadata, dict):
            metadata.update(state["resources"].default_params)
        notify("Metadata summary generated", 75)
        return {"metadata": metadata}

    def album_art_node(state: SongState):
        """Generate album artwork if not in local mode and requested."""
        if state["use_local"]:
            notify("Album artwork skipped (local mode)", 80)
            return {"album_art": None}
        if not state.get("generate_album_art", True):
            notify("Album artwork skipped (manually disabled)", 80)
            return {"album_art": None}
        title = extract_title(state["lyrics"], state.get("song_name"))
        artwork_path = generate_album_art(
            title, 
            state["user_input"],
            persona_name=state.get("persona_name"),
            style=state.get("style"),
            mood=state.get("mood") or state.get("resources").default_params.get("mood"),
            vocal_gender=state.get("vocal_gender") or state.get("resources").default_params.get("vocal_gender"),
            aspect_ratio=state.get("album_art_aspect_ratio"),
        )
        notify(f"Album artwork generated: {artwork_path}", 85)
        return {"album_art": artwork_path}

    def save_node(state: SongState):
        title = extract_title(state["lyrics"], state.get("song_name"))
        filename = save_song(
            title, 
            state["user_input"], 
            state["lyrics"], 
            state["resources"].default_params, 
            state["metadata"],
            album_art_path=state.get("album_art")
        )
        notify(f"Song saved to {filename}", 95)
        return {"filename": filename}

    graph = StateGraph(SongState)
    graph.add_node("brief", brief_node)
    graph.add_node("structure", structure_node)
    graph.add_node("draft", draft_node)
    graph.add_node("review", review_node)
    graph.add_node("targeted_revise", targeted_revise_node)
    graph.add_node("metadata", metadata_node)
    graph.add_node("album_art", album_art_node)
    graph.add_node("save", save_node)

    graph.set_entry_point("brief")
    graph.add_edge("brief", "structure")
    graph.add_edge("structure", "draft")
    graph.add_edge("draft", "review")
    graph.add_conditional_edges("review", review_router, {"revise": "targeted_revise", "metadata": "metadata"})
    graph.add_edge("targeted_revise", "review")
    graph.add_edge("metadata", "album_art")
    graph.add_edge("album_art", "save")
    graph.add_edge("save", END)

    app = graph.compile()
    progress_bar = None if progress_callback else tqdm(total=None, desc="Creating your song (agentic)", unit="step")
    with progress_bar if progress_bar else nullcontext():
        final_state = app.invoke(initial_state)
    notify("Generation completed", 100)
    return final_state


# Compatibility helpers for callers expecting the old CLI function names.
def load_prompt(prompt_path: Optional[str], prompt_arg: Optional[str]) -> str:
    """Load prompt content either from a file or direct argument."""
    return load_prompt_from_file(prompt_path) if prompt_path else prompt_arg


def regenerate_album_art(song_path: str) -> str:
    """Regenerate album art using the existing helper pipeline."""
    title, user_prompt = extract_song_details_for_art(song_path)
    return generate_album_art(title, user_prompt or "Use the song metadata to inspire the cover art.")
