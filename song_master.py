"""
Song Master Script

This script generates songs using AI-powered agents in a structured workflow.
It supports both local and remote LLM usage, with options for personas, album art generation, and more.
"""

import argparse
import os
import sys
from typing import Optional

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
    SongResources,
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


def generate_song(user_input: str, use_local: bool = False, song_name: Optional[str] = None, persona: Optional[str] = None):
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
        enhanced_input = enhance_user_input(state["user_input"], state.get("song_name"))
        lyrics = draft_song(
            prompt_template=drafter_prompt,
            enhanced_input=enhanced_input,
            styles=state["resources"].styles,
            tags=state["resources"].tags,
            persona_styles=state["resources"].persona_styles,
            default_params=state["resources"].default_params,
            use_local=state["use_local"],
        )
        tqdm.write("✓ Draft generated.")
        return {"lyrics": lyrics}

    def review_node(state: SongState):
        feedback = run_parallel_reviews(review_prompt, state["lyrics"], state["use_local"])
        revised_lyrics = revise_lyrics(revision_prompt, state["lyrics"], feedback, state["use_local"])
        score = score_lyrics(scoring_prompt, revised_lyrics, state["use_local"])
        tqdm.write(f"✓ Review round {state['round'] + 1}: score {score:.2f}")
        return {"lyrics": revised_lyrics, "feedback": feedback, "score": score, "round": state["round"] + 1}

    def review_router(state: SongState):
        """Decide whether to continue reviewing or proceed to critic based on score and rounds."""
        if state["score"] < state["score_threshold"] and state["round"] < state["max_rounds"]:
            return "keep_reviewing"
        return "go_critic"

    def critic_node(state: SongState):
        revised = critique_song(critic_prompt, revision_prompt, state["lyrics"], state["use_local"])
        tqdm.write("✓ Critic feedback applied.")
        return {"lyrics": revised}

    def preflight_node(state: SongState):
        raw = preflight_song(preflight_prompt, state["lyrics"], state["resources"].styles, state["resources"].tags, state["use_local"])
        triaged = triage_preflight(preflight_triage_prompt, raw, state["use_local"])
        passed = bool(triaged.get("pass", False))
        issues = triaged.get("issues", [])
        if passed:
            tqdm.write("✓ Preflight passed.")
        else:
            tqdm.write(f"! Preflight flagged {len(issues)} issue(s).")
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
        tqdm.write("✓ Applied targeted fixes from preflight.")
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
        tqdm.write("✓ Metadata summary generated.")
        return {"metadata": metadata}

    def album_art_node(state: SongState):
        """Generate album artwork if not in local mode."""
        if state["use_local"]:
            tqdm.write("✓ Album artwork skipped (local mode).")
            return {"album_art": None}
        title = extract_title(state["lyrics"], state.get("song_name"))
        artwork_path = generate_album_art(title, state["user_input"])
        tqdm.write(f"✓ Album artwork generated: {artwork_path}")
        return {"album_art": artwork_path}

    def save_node(state: SongState):
        title = extract_title(state["lyrics"], state.get("song_name"))
        filename = save_song(title, state["user_input"], state["lyrics"], state["resources"].default_params, state["metadata"])
        tqdm.write(f"✓ Song saved to {filename}")
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

    # Compile and execute the graph
    app = graph.compile()
    with tqdm(total=None, desc="Creating your song (agentic)", unit="step") as _:
        app.invoke(initial_state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a song using AI")
    parser.add_argument("prompt", nargs="?", help="The song description or request")
    parser.add_argument(
        "--prompt-file",
        type=str,
        default=None,
        help="Path to a .txt file containing the song description or request",
    )
    parser.add_argument("--local", action="store_true", help="Use local LM Studio LLM and disable image generation")
    parser.add_argument("--name", type=str, default=None, help="Optional song name/title")
    parser.add_argument(
        "--persona",
        type=str,
        default=None,
        help='Specify the persona by name (e.g., "antidote") or by path to a persona .md file',
    )
    parser.add_argument(
        "--regen-cover",
        type=str,
        default=None,
        help="Path to an existing song markdown file to regenerate album art and exit",
    )

    args = parser.parse_args()

    if args.regen_cover:
        try:
            title, user_prompt = extract_song_details_for_art(args.regen_cover)
        except (FileNotFoundError, ValueError) as regen_err:
            parser.error(str(regen_err))
            sys.exit(2)
        artwork_path = generate_album_art(title, user_prompt or "Use the song metadata to inspire the cover art.")
        print(f"Album art regenerated: {artwork_path}")
        sys.exit(0)

    # Load prompt from file or argument
    try:
        prompt_text = load_prompt_from_file(args.prompt_file) if args.prompt_file else args.prompt
    except FileNotFoundError as prompt_err:
        parser.error(str(prompt_err))
        sys.exit(2)

    if not prompt_text:
        parser.error("You must provide a prompt as an argument or via --prompt-file")
        sys.exit(2)

    # Generate the song
    generate_song(prompt_text, args.local, args.name, args.persona)
