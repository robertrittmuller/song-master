import { FormEvent, ReactNode, useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Toggle } from "../../components/ui/Toggle";
import {
  createSong,
  fetchAlbums,
  fetchInstruments,
  fetchPersonas,
  fetchSettings,
  fetchStyles
} from "../../services/api";

const KEY_OPTIONS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const MOOD_OPTIONS = ["happy", "sad", "energetic", "calm", "dark", "uplifting", "angry", "romantic"];
const RHYME_SCHEMES = [
  { value: "", label: "Auto" },
  { value: "AABB", label: "AABB · Couplet rhyme" },
  { value: "ABAB", label: "ABAB · Alternate rhyme" },
  { value: "ABBA", label: "ABBA · Enclosed rhyme" },
  { value: "AAAA", label: "AAAA · Monorhyme" },
  { value: "AABCCB", label: "AABCCB · Ballad stanza" },
  { value: "Free Verse", label: "Free Verse" }
] as const;

const AUTO_SELECT_FIELDS = [
  "genre",
  "tempo",
  "key",
  "instruments",
  "mood",
  "vocal_gender",
  "rhyme_scheme"
] as const;
const DEFAULT_GENERATE_COVER_ART = false;
const SONG_PROMPT_PLACEHOLDER =
  "Describe the story, energy, perspective, references, must-include lines, or production ideas...";

type GenerationMode = "simple" | "advanced";

function normalizeOptionalText(value: string): string | undefined {
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
}

function buildInstrumentValue(selectedInstruments: Set<string>, customInstruments: string): string | undefined {
  const customList = customInstruments
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);

  const combined = [...Array.from(selectedInstruments), ...customList];
  return combined.length ? combined.join(", ") : undefined;
}

export function GenerationForm() {
  const navigate = useNavigate();
  const { data: personas = [] } = useQuery({ queryKey: ["personas"], queryFn: fetchPersonas });
  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: fetchSettings });
  const { data: albums = [] } = useQuery({ queryKey: ["albums"], queryFn: fetchAlbums });
  const { data: availableInstruments = [] } = useQuery({ queryKey: ["instruments"], queryFn: fetchInstruments });
  const { data: styles = [], isLoading: stylesLoading } = useQuery({
    queryKey: ["styles"],
    queryFn: fetchStyles
  });

  const [title, setTitle] = useState("");
  const [prompt, setPrompt] = useState("");
  const [generationMode, setGenerationMode] = useState<GenerationMode>("simple");
  const [persona, setPersona] = useState<string | undefined>();
  const [albumId, setAlbumId] = useState<number | undefined>();
  const [style, setStyle] = useState("");
  const [genre, setGenre] = useState("");
  const [tempo, setTempo] = useState("");
  const [key, setKey] = useState("");
  const [mood, setMood] = useState("");
  const [vocalGender, setVocalGender] = useState("");
  const [rhymeScheme, setRhymeScheme] = useState("");
  const [selectedInstruments, setSelectedInstruments] = useState<Set<string>>(new Set());
  const [customInstruments, setCustomInstruments] = useState("");
  const [useLocal, setUseLocal] = useState(false);
  const [generateCoverArt, setGenerateCoverArt] = useState(false);
  const [settingsInitialized, setSettingsInitialized] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const isAdvancedMode = generationMode === "advanced";

  useEffect(() => {
    if (!settings || settingsInitialized) {
      return;
    }

    setUseLocal(settings.use_local);
    setSettingsInitialized(true);
  }, [settings, settingsInitialized]);

  const mutation = useMutation({
    mutationFn: createSong,
    onSuccess: (song) => navigate(`/songs/${song.id}`)
  });

  const selectedInstrumentCount = selectedInstruments.size + (customInstruments.trim() ? 1 : 0);
  const advancedOverrideCount = selectedInstrumentCount + [genre, tempo, key, mood, vocalGender, rhymeScheme].filter(Boolean).length;
  const lockedSettingCount = [
    isAdvancedMode ? persona : undefined,
    isAdvancedMode ? style : undefined,
    isAdvancedMode ? genre : undefined,
    isAdvancedMode ? tempo : undefined,
    isAdvancedMode ? key : undefined,
    isAdvancedMode ? mood : undefined,
    isAdvancedMode ? vocalGender : undefined,
    isAdvancedMode ? rhymeScheme : undefined,
    isAdvancedMode && selectedInstrumentCount ? "instruments" : "",
    isAdvancedMode && albumId ? "album" : ""
  ].filter(Boolean).length;

  useEffect(() => {
    if (
      genre ||
      tempo ||
      key ||
      mood ||
      vocalGender ||
      rhymeScheme ||
      selectedInstruments.size ||
      customInstruments.trim()
    ) {
      setAdvancedOpen(true);
    }
  }, [customInstruments, genre, key, mood, rhymeScheme, selectedInstruments, tempo, vocalGender]);

  const toggleInstrument = (instrument: string) => {
    setSelectedInstruments((previous) => {
      const next = new Set(previous);
      if (next.has(instrument)) {
        next.delete(instrument);
      } else {
        next.add(instrument);
      }
      return next;
    });
  };

  const clearInstrumentSelection = () => {
    setSelectedInstruments(new Set());
    setCustomInstruments("");
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!prompt.trim() || !title.trim()) {
      return;
    }

    const normalizedGenre = isAdvancedMode ? normalizeOptionalText(genre) : undefined;
    const normalizedTempo = isAdvancedMode ? normalizeOptionalText(tempo) : undefined;
    const normalizedKey = isAdvancedMode ? normalizeOptionalText(key) : undefined;
    const normalizedMood = isAdvancedMode ? normalizeOptionalText(mood) : undefined;
    const normalizedVocalGender = isAdvancedMode ? normalizeOptionalText(vocalGender) : undefined;
    const normalizedRhymeScheme = isAdvancedMode ? normalizeOptionalText(rhymeScheme) : undefined;
    const normalizedStyle = isAdvancedMode ? normalizeOptionalText(style) : undefined;
    const normalizedInstruments = isAdvancedMode
      ? buildInstrumentValue(selectedInstruments, customInstruments)
      : undefined;
    const submittedUseLocal = useLocal;
    const submittedGenerateCoverArt = isAdvancedMode
      ? submittedUseLocal ? false : generateCoverArt
      : DEFAULT_GENERATE_COVER_ART;

    const autoSelectFields = AUTO_SELECT_FIELDS.filter((field) => {
      switch (field) {
        case "genre":
          return !normalizedGenre;
        case "tempo":
          return !normalizedTempo;
        case "key":
          return !normalizedKey;
        case "instruments":
          return !normalizedInstruments;
        case "mood":
          return !normalizedMood;
        case "vocal_gender":
          return !normalizedVocalGender;
        case "rhyme_scheme":
          return !normalizedRhymeScheme;
        default:
          return false;
      }
    });

    mutation.mutate({
      user_prompt: prompt.trim(),
      title: title.trim(),
      persona: isAdvancedMode ? persona : undefined,
      style: normalizedStyle,
      genre: normalizedGenre,
      tempo: normalizedTempo,
      key: normalizedKey,
      instruments: normalizedInstruments,
      mood: normalizedMood,
      vocal_gender: normalizedVocalGender,
      rhyme_scheme: normalizedRhymeScheme,
      use_local: submittedUseLocal,
      album_id: isAdvancedMode ? albumId : undefined,
      generate_album_art: submittedGenerateCoverArt,
      generation_config: autoSelectFields.length
        ? { auto_select_fields: autoSelectFields }
        : undefined
    });
  };

  return (
    <form onSubmit={handleSubmit} className="generation-form">
      <Card>
        <div className="generation-mode-switch">
          <div>
            <div className="generation-eyebrow">Creation Mode</div>
            <h3 className="generation-mode-switch__title">{isAdvancedMode ? "Advanced setup" : "Simple setup"}</h3>
            <p className="generation-mode-switch__copy">
              {isAdvancedMode
                ? "Show every current song option, including persona, style, model location, and musical overrides."
                : "Keep the form to title and prompt only. Hidden settings stay at their default values."}
            </p>
          </div>

          <ToggleShell activeLabel={isAdvancedMode ? "Advanced" : "Simple"}>
            <Toggle
              value={isAdvancedMode}
              onChange={(value) => setGenerationMode(value ? "advanced" : "simple")}
              leftLabel="Simple"
              rightLabel="Advanced"
            />
          </ToggleShell>
        </div>

        <div className="generation-hero">
          <div className="generation-hero__main">
            <div className="generation-eyebrow">Prompt First</div>
            <h2 className="generation-hero__title">Start with the idea. Leave the music on Auto unless you want to steer it.</h2>
            <p className="generation-hero__copy">
              Auto lets the model infer style, tempo, mood, key, instruments, and rhyme choices from your prompt.
            </p>

            <div className="generation-field">
              <label className="generation-label" htmlFor="song-title">Song Title</label>
              <input
                id="song-title"
                required
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Give your song a name"
                className="generation-input"
              />
            </div>

            <div className="generation-field">
              <label className="generation-label" htmlFor="song-prompt">Song Prompt</label>
              <div className="generation-textarea-shell">
                {!prompt && (
                  <span className="generation-textarea-placeholder" aria-hidden="true">
                    {SONG_PROMPT_PLACEHOLDER}
                  </span>
                )}
                <textarea
                  id="song-prompt"
                  required
                  value={prompt}
                  onChange={(event) => setPrompt(event.target.value)}
                  rows={8}
                  wrap="soft"
                  className="generation-textarea"
                />
              </div>
              <p className="generation-help">
                Include anything non-negotiable here. Everything left on Auto stays flexible.
              </p>
            </div>
          </div>

          <div className="generation-hero__side">
            {isAdvancedMode && (
              <div className="generation-status-card">
                <div className="generation-status-card__eyebrow">Current Setup</div>
                <div className="generation-status-card__value">{lockedSettingCount} manual choice{lockedSettingCount === 1 ? "" : "s"}</div>
                <p className="generation-status-card__copy">
                  {lockedSettingCount === 0
                    ? "The model will determine the musical settings from your prompt."
                    : "Everything not explicitly chosen will stay on Auto."}
                </p>
              </div>
            )}

            <div className="generation-panel">
              <div className="generation-panel__header">
                <div>
                  <div className="generation-eyebrow">Model Location</div>
                  <h3 className="generation-panel__title">{useLocal ? "Local generation" : "Remote generation"}</h3>
                </div>
              </div>

              <div className="generation-toggle-row">
                <ToggleShell activeLabel={useLocal ? "Local" : "Remote"}>
                  <Toggle
                    value={useLocal}
                    onChange={setUseLocal}
                    leftLabel="Remote"
                    rightLabel="Local"
                  />
                </ToggleShell>
              </div>

              {isAdvancedMode && (
                <label className={`generation-check ${useLocal ? "is-disabled" : ""}`}>
                  <input
                    type="checkbox"
                    checked={generateCoverArt}
                    onChange={(event) => setGenerateCoverArt(event.target.checked)}
                    disabled={useLocal}
                  />
                  <span>
                    <strong>Generate cover art</strong>
                    <small>{useLocal ? "Disabled in local mode." : "Optional artwork for the finished song."}</small>
                  </span>
                </label>
              )}
            </div>
          </div>
        </div>
      </Card>

      {isAdvancedMode && (
        <>
          <Card title="Creative Direction">
            <div className="generation-grid generation-grid--core">
              <div className="generation-field">
                <label className="generation-label" htmlFor="style">Core Style</label>
                <select
                  id="style"
                  value={style}
                  onChange={(event) => setStyle(event.target.value)}
                  disabled={stylesLoading}
                  className="generation-input"
                >
                  <option value="">Auto</option>
                  {styles.map((styleOption) => (
                    <option key={styleOption} value={styleOption}>
                      {styleOption}
                    </option>
                  ))}
                </select>
                <p className="generation-help">Set this only when you want a strong stylistic anchor.</p>
              </div>

              <div className="generation-field">
                <label className="generation-label" htmlFor="album">Album</label>
                <select
                  id="album"
                  value={albumId || ""}
                  onChange={(event) => setAlbumId(event.target.value ? Number(event.target.value) : undefined)}
                  className="generation-input"
                >
                  <option value="">No album</option>
                  {albums.map((album) => (
                    <option key={album.id} value={album.id}>
                      {album.name}
                    </option>
                  ))}
                </select>
                <p className="generation-help">Optional organization only. It does not affect the generation.</p>
              </div>
            </div>

            <div className="generation-field">
              <label className="generation-label">Persona</label>
              <div className="generation-persona-grid">
                <button
                  type="button"
                  className={`generation-persona ${!persona ? "is-selected" : ""}`}
                  onClick={() => setPersona(undefined)}
                >
                  <span className="generation-persona__name">Auto</span>
                  <span className="generation-persona__meta">No persona bias. Let the prompt lead.</span>
                </button>

                {personas.length === 0 && (
                  <div className="generation-empty-state">No personas found yet.</div>
                )}

                {personas.map((currentPersona) => (
                  <button
                    type="button"
                    key={currentPersona.name}
                    onClick={() => setPersona((previous) => previous === currentPersona.name ? undefined : currentPersona.name)}
                    className={`generation-persona ${persona === currentPersona.name ? "is-selected" : ""}`}
                  >
                    <span className="generation-persona__name">{currentPersona.name}</span>
                    <span className="generation-persona__meta">
                      {currentPersona.styles || currentPersona.description || "Custom persona"}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </Card>

          <details
            className="generation-advanced"
            open={advancedOpen}
            onToggle={(event) => setAdvancedOpen(event.currentTarget.open)}
          >
            <summary className="generation-advanced__summary">
              <div>
                <div className="generation-eyebrow">Optional Guidance</div>
                <h3 className="generation-advanced__title">Fine-tune the musical details</h3>
                <p className="generation-advanced__copy">Leave any field on Auto to let the model decide from the prompt.</p>
              </div>
              <span className="generation-advanced__badge">
                {advancedOverrideCount} overrides
              </span>
            </summary>

            <div className="generation-grid generation-grid--advanced">
              <div className="generation-field">
                <label className="generation-label" htmlFor="genre">Genre</label>
                <input
                  id="genre"
                  value={genre}
                  onChange={(event) => setGenre(event.target.value)}
                  placeholder="Auto"
                  className="generation-input"
                />
              </div>

              <div className="generation-field">
                <label className="generation-label" htmlFor="tempo">Tempo (BPM)</label>
                <input
                  id="tempo"
                  type="number"
                  min="1"
                  value={tempo}
                  onChange={(event) => setTempo(event.target.value)}
                  placeholder="Auto"
                  className="generation-input"
                />
              </div>

              <div className="generation-field">
                <label className="generation-label" htmlFor="key-signature">Key</label>
                <select
                  id="key-signature"
                  value={key}
                  onChange={(event) => setKey(event.target.value)}
                  className="generation-input"
                >
                  <option value="">Auto</option>
                  {KEY_OPTIONS.map((keyOption) => (
                    <option key={keyOption} value={keyOption}>
                      {keyOption}
                    </option>
                  ))}
                </select>
              </div>

              <div className="generation-field">
                <label className="generation-label" htmlFor="mood">Mood</label>
                <select
                  id="mood"
                  value={mood}
                  onChange={(event) => setMood(event.target.value)}
                  className="generation-input"
                >
                  <option value="">Auto</option>
                  {MOOD_OPTIONS.map((moodOption) => (
                    <option key={moodOption} value={moodOption}>
                      {moodOption}
                    </option>
                  ))}
                </select>
              </div>

              <div className="generation-field">
                <label className="generation-label" htmlFor="vocal-gender">Vocal Style</label>
                <select
                  id="vocal-gender"
                  value={vocalGender}
                  onChange={(event) => setVocalGender(event.target.value)}
                  className="generation-input"
                >
                  <option value="">Auto</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Duet">Duet</option>
                </select>
              </div>

              <div className="generation-field">
                <label className="generation-label" htmlFor="rhyme-scheme">Rhyme Scheme</label>
                <select
                  id="rhyme-scheme"
                  value={rhymeScheme}
                  onChange={(event) => setRhymeScheme(event.target.value)}
                  className="generation-input"
                >
                  {RHYME_SCHEMES.map((scheme) => (
                    <option key={scheme.value || "auto"} value={scheme.value}>
                      {scheme.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="generation-field generation-field--full">
                <div className="generation-field__row">
                  <label className="generation-label">Instruments</label>
                  <button type="button" className="generation-inline-link" onClick={clearInstrumentSelection}>
                    Reset to Auto
                  </button>
                </div>

                <div className="generation-chip-grid">
                  <button
                    type="button"
                    onClick={clearInstrumentSelection}
                    className={`generation-chip ${selectedInstruments.size === 0 && !customInstruments.trim() ? "is-selected" : ""}`}
                  >
                    Auto
                  </button>

                  {availableInstruments.map((instrument) => (
                    <button
                      key={instrument}
                      type="button"
                      onClick={() => toggleInstrument(instrument)}
                      className={`generation-chip ${selectedInstruments.has(instrument) ? "is-selected" : ""}`}
                    >
                      {instrument}
                    </button>
                  ))}
                </div>

                <input
                  value={customInstruments}
                  onChange={(event) => setCustomInstruments(event.target.value)}
                  placeholder="Optional custom instruments, comma-separated"
                  className="generation-input"
                />
                <p className="generation-help">Use this only when the arrangement needs something specific.</p>
              </div>
            </div>
          </details>
        </>
      )}

      <div className="generation-submit-bar">
        <div>
          <div className="generation-submit-bar__title">Ready to generate</div>
          <p className="generation-submit-bar__copy">
            {!isAdvancedMode
              ? "Simple mode keeps every optional setting on its default path."
              : lockedSettingCount === 0
              ? "You are giving the model a clean brief with Auto musical settings."
              : `${lockedSettingCount} setting${lockedSettingCount === 1 ? "" : "s"} locked in. The rest will stay on Auto.`}
          </p>
        </div>

        <div className="generation-submit-bar__actions">
          {mutation.isError && (
            <span className="generation-error">Failed to start generation. Try again.</span>
          )}
          <Button type="submit" variant="ai-glow" size="lg" isLoading={mutation.isPending}>
            Generate Song
          </Button>
        </div>
      </div>
    </form>
  );
}

type ToggleShellProps = {
  activeLabel: string;
  children: ReactNode;
};

function ToggleShell({ activeLabel, children }: ToggleShellProps) {
  return (
    <div className="generation-toggle-shell">
      <div>
        <div className="generation-toggle-shell__label">{activeLabel}</div>
      </div>
      {children}
    </div>
  );
}
