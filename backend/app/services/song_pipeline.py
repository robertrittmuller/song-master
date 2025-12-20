import os
from contextlib import nullcontext
from typing import Callable, Optional

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph
from tqdm import tqdm

from ai_functions import (
    build_prompts,
    critique_song,
    draft_song,
    generate_metadata_summary,
    preflight_song,
    revise_lyrics,
    run_parallel_reviews,
    score_lyrics,
    triage_preflight,
)
from helpers import (
    SongState,
    enhance_user_input,
    extract_song_details_for_art,
    extract_title,
    generate_album_art,
    load_prompt_from_file,
    load_resources,
    parse_persona,
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

    (
        drafter_prompt,
        review_prompt,
        critic_prompt,
        preflight_prompt,
        revision_prompt,
        scoring_prompt,
        metadata_prompt,
        preflight_triage_prompt,
    ) = build_prompts()

    persona_name = parse_persona(user_input, persona)
    resources = load_resources(persona_name)
    max_rounds = int(os.getenv("REVIEW_MAX_ROUNDS", "3"))
    score_threshold = float(os.getenv("REVIEW_SCORE_THRESHOLD", "8.0"))

    initial_state: SongState = {
        "user_input": user_input,
        "song_name": song_name,
        "persona": persona,
        "persona_name": persona_name,
        "style": style,
        "use_local": use_local,
        "resources": resources,
        "lyrics": "",
        "feedback": "",
        "score": 0.0,
        "round": 0,
        "max_rounds": max_rounds,
        "score_threshold": score_threshold,
        "preflight_passed": False,
        "preflight_issues": [],
        "metadata": {},
        "filename": None,
        "album_art": None,
    }

    def draft_node(state: SongState):
        """Generate initial song draft using AI."""
        notify("Generating initial draft", 20)
        enhanced_input = enhance_user_input(state["user_input"], state.get("song_name"), state.get("style"))
        lyrics = draft_song(
            prompt_template=drafter_prompt,
            enhanced_input=enhanced_input,
            styles=state["resources"].styles,
            tags=state["resources"].tags,
            persona_styles=state["resources"].persona_styles,
            default_params=state["resources"].default_params,
            use_local=state["use_local"],
        )
        notify("Draft generated", 25)
        return {"lyrics": lyrics}

    def review_node(state: SongState):
        feedback = run_parallel_reviews(review_prompt, state["lyrics"], state["use_local"])
        revised_lyrics = revise_lyrics(revision_prompt, state["lyrics"], feedback, state["use_local"])
        score = score_lyrics(scoring_prompt, revised_lyrics, state["use_local"])
        round_complete = state["round"] + 1
        notify(f"Review round {round_complete} complete (score {score:.2f})", 40 + min(round_complete * 5, 10))
        return {"lyrics": revised_lyrics, "feedback": feedback, "score": score, "round": round_complete}

    def review_router(state: SongState):
        """Decide whether to continue reviewing or proceed to critic based on score and rounds."""
        if state["score"] < state["score_threshold"] and state["round"] < state["max_rounds"]:
            return "keep_reviewing"
        return "go_critic"

    def critic_node(state: SongState):
        revised = critique_song(critic_prompt, revision_prompt, state["lyrics"], state["use_local"])
        notify("Critic feedback applied", 55)
        return {"lyrics": revised}

    def preflight_node(state: SongState):
        raw = preflight_song(preflight_prompt, state["lyrics"], state["resources"].styles, state["resources"].tags, state["use_local"])
        triaged = triage_preflight(preflight_triage_prompt, raw, state["use_local"])
        passed = bool(triaged.get("pass", False))
        issues = triaged.get("issues", [])
        notify("Preflight checks completed" + ("" if passed else f" with {len(issues)} issue(s) flagged"), 65)
        return {"preflight_passed": passed, "preflight_issues": issues}

    def preflight_router(state: SongState):
        if not state["preflight_passed"] and state["round"] < state["max_rounds"]:
            return "needs_fix"
        return "ready_for_metadata"

    def targeted_revise_node(state: SongState):
        """Revise lyrics specifically to address preflight issues."""
        issues = state.get("preflight_issues", [])
        feedback = "Fix these preflight issues:\n" + "\n".join(f"- {issue}" for issue in issues)
        revised = revise_lyrics(revision_prompt, state["lyrics"], feedback, state["use_local"])
        notify("Applied targeted fixes from preflight", 50)
        return {"lyrics": revised, "feedback": feedback, "round": state["round"] + 1}

    def metadata_node(state: SongState):
        metadata = generate_metadata_summary(
            metadata_prompt,
            state["lyrics"],
            state["user_input"],
            state["resources"].default_params,
            state["resources"].persona_styles,
            state["use_local"],
        )
        notify("Metadata summary generated", 75)
        return {"metadata": metadata}

    def album_art_node(state: SongState):
        """Generate album artwork if not in local mode."""
        if state["use_local"]:
            notify("Album artwork skipped (local mode)", 80)
            return {"album_art": None}
        title = extract_title(state["lyrics"], state.get("song_name"))
        artwork_path = generate_album_art(title, state["user_input"])
        notify(f"Album artwork generated: {artwork_path}", 85)
        return {"album_art": artwork_path}

    def save_node(state: SongState):
        title = extract_title(state["lyrics"], state.get("song_name"))
        filename = save_song(title, state["user_input"], state["lyrics"], state["resources"].default_params, state["metadata"])
        notify(f"Song saved to {filename}", 95)
        return {"filename": filename}

    graph = StateGraph(SongState)
    graph.add_node("draft", draft_node)
    graph.add_node("review", review_node)
    graph.add_node("critic", critic_node)
    graph.add_node("preflight", preflight_node)
    graph.add_node("targeted_revise", targeted_revise_node)
    graph.add_node("metadata", metadata_node)
    graph.add_node("album_art", album_art_node)
    graph.add_node("save", save_node)

    graph.set_entry_point("draft")
    graph.add_edge("draft", "review")
    graph.add_conditional_edges("review", review_router, {"keep_reviewing": "review", "go_critic": "critic"})
    graph.add_edge("critic", "preflight")
    graph.add_conditional_edges("preflight", preflight_router, {"needs_fix": "targeted_revise", "ready_for_metadata": "metadata"})
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
