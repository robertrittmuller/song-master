import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { StyleSelector } from "../../components/ui/StyleSelector";
import { Toggle } from "../../components/ui/Toggle";
import { createSong, fetchAlbums, fetchPersonas, fetchSettings, fetchInstruments } from "../../services/api";
import type { Persona } from "../../types/api";

export function GenerationForm() {
  const navigate = useNavigate();
  const { data: personas = [] } = useQuery({ queryKey: ["personas"], queryFn: fetchPersonas });
  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: fetchSettings });
  const { data: albums = [] } = useQuery({ queryKey: ["albums"], queryFn: fetchAlbums });
  const { data: availableInstruments = [] } = useQuery({ queryKey: ["instruments"], queryFn: fetchInstruments });

  const [prompt, setPrompt] = useState("");
  const [title, setTitle] = useState("");
  const [persona, setPersona] = useState<string | undefined>(settings?.generation.persona);
  const [style, setStyle] = useState("");
  const [albumId, setAlbumId] = useState<number | undefined>(undefined);
  const [useLocal, setUseLocal] = useState(false);
  const [generateCoverArt, setGenerateCoverArt] = useState(true);

  const [genre, setGenre] = useState("");
  const [tempo, setTempo] = useState("120");
  const [key, setKey] = useState("C");
  const [selectedInstruments, setSelectedInstruments] = useState<Set<string>>(new Set(["guitar", "bass", "drums"]));
  const [customInstruments, setCustomInstruments] = useState("");
  const [mood, setMood] = useState("happy");
  const [vocalGender, setVocalGender] = useState("");

  const toggleInstrument = (inst: string) => {
    const next = new Set(selectedInstruments);
    if (next.has(inst)) {
      next.delete(inst);
    } else {
      next.add(inst);
    }
    setSelectedInstruments(next);
  };

  const mutation = useMutation({
    mutationFn: createSong,
    onSuccess: (song) => navigate(`/songs/${song.id}`)
  });

  const filteredPersonas = useMemo<Persona[]>(() => personas, [personas]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!prompt.trim() || !title.trim()) return;
    mutation.mutate({
      user_prompt: prompt,
      title: title,
      persona,
      style: style || undefined,
      genre: genre || undefined,
      tempo,
      key,
      instruments: [
        ...Array.from(selectedInstruments),
        ...(customInstruments ? customInstruments.split(",").map(i => i.trim()) : [])
      ].filter(Boolean).join(", "),
      mood,
      vocal_gender: vocalGender || undefined,
      use_local: useLocal,
      album_id: albumId,
      generate_album_art: useLocal ? false : generateCoverArt
    });
  };

  return (
    <form onSubmit={handleSubmit} className="stack" style={{ maxWidth: 940 }}>
      <Card title="Song Description">
        <textarea
          required
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          rows={6}
          placeholder="Describe the song you want to create..."
          style={{
            width: "100%",
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.1)",
            background: "rgba(255,255,255,0.04)",
            color: "var(--gray-50)",
            padding: 16,
            fontSize: 15
          }}
        />
        <div style={{ marginTop: 16 }}>
          <div style={{ color: "var(--gray-300)", fontSize: 13, marginBottom: 8 }}>LLM Location</div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Toggle
              value={useLocal}
              onChange={setUseLocal}
              leftLabel="Remote"
              rightLabel="Local"
            />
            <span style={{ color: "var(--gray-400)", fontSize: 13 }}>
              {useLocal ? "Using Local LLM (skips album art generation)" : "Using Remote LLM (includes album art)"}
            </span>
          </div>
        </div>

        {!useLocal && (
          <div style={{ marginTop: 16 }}>
            <div style={{ color: "var(--gray-300)", fontSize: 13, marginBottom: 8 }}>Cover Art</div>
            <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={generateCoverArt}
                onChange={(e) => setGenerateCoverArt(e.target.checked)}
                style={{
                  width: 18,
                  height: 18,
                  accentColor: "var(--primary-500)",
                  cursor: "pointer"
                }}
              />
              <span style={{ color: "var(--gray-300)", fontSize: 14 }}>Generate Cover Art</span>
            </label>
          </div>
        )}
      </Card>

      <Card title="Song Details">
        <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))" }}>
          <div className="stack">
            <label style={{ color: "var(--gray-300)", fontSize: 13 }}>Song Title</label>
            <input
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Give your song a name"
              style={{
                padding: "12px 14px",
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.1)",
                background: "rgba(255,255,255,0.04)",
                color: "var(--gray-50)"
              }}
            />
          </div>
          <StyleSelector value={style} onChange={setStyle} label="Core Style & Genre" />

          <div className="stack">
            <label style={{ color: "var(--gray-300)", fontSize: 13 }}>Tempo (BPM)</label>
            <input
              type="number"
              value={tempo}
              onChange={(e) => setTempo(e.target.value)}
              className="input"
              style={{
                padding: "12px 14px",
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.1)",
                background: "rgba(255,255,255,0.04)",
                color: "var(--gray-50)"
              }}
            />
          </div>

          <div className="stack">
            <label style={{ color: "var(--gray-300)", fontSize: 13 }}>Key</label>
            <select
              className="input"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              style={{
                padding: "12px 14px",
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.1)",
                background: "rgba(255,255,255,0.04)",
                color: "var(--gray-50)"
              }}
            >
              {["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"].map(k => (
                <option key={k} value={k}>{k}</option>
              ))}
            </select>
          </div>

          <div className="stack">
            <label style={{ color: "var(--gray-300)", fontSize: 13 }}>Mood</label>
            <select
              className="input"
              value={mood}
              onChange={(e) => setMood(e.target.value)}
              style={{
                padding: "12px 14px",
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.1)",
                background: "rgba(255,255,255,0.04)",
                color: "var(--gray-50)"
              }}
            >
              {["happy", "sad", "energetic", "calm", "dark", "uplifting", "angry", "romantic"].map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>

          <div className="stack">
            <label style={{ color: "var(--gray-300)", fontSize: 13 }}>Vocal Gender</label>
            <select
              className="input"
              value={vocalGender}
              onChange={(e) => setVocalGender(e.target.value)}
              style={{
                padding: "12px 14px",
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.1)",
                background: "rgba(255,255,255,0.04)",
                color: "var(--gray-50)"
              }}
            >
              <option value="">Auto (Persona / AI choice)</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Duet">Duet</option>
            </select>
          </div>

          <div className="stack" style={{ gridColumn: "1 / -1" }}>
            <label style={{ color: "var(--gray-300)", fontSize: 13 }}>Instruments</label>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 4 }}>
              {availableInstruments.map((inst) => {
                const isSelected = selectedInstruments.has(inst);
                return (
                  <button
                    key={inst}
                    type="button"
                    onClick={() => toggleInstrument(inst)}
                    className="tag"
                    style={{
                      cursor: "pointer",
                      fontSize: 12,
                      padding: "6px 12px",
                      background: isSelected ? "rgba(139, 92, 246, 0.4)" : "rgba(255,255,255,0.05)",
                      color: isSelected ? "#ddd6fe" : "var(--gray-400)",
                      border: isSelected ? "1px solid rgba(139, 92, 246, 0.6)" : "1px solid rgba(255,255,255,0.1)",
                      transition: "all 0.2s ease"
                    }}
                  >
                    {inst}
                  </button>
                );
              })}
            </div>

            <div style={{ marginTop: 12 }}>
              <label style={{ color: "var(--gray-500)", fontSize: 11, fontWeight: 700, textTransform: "uppercase" }}>Manual / Custom Instruments</label>
              <input
                value={customInstruments}
                onChange={(e) => setCustomInstruments(e.target.value)}
                placeholder="e.g. sitar, bagpipes, laser sounds"
                className="input"
                style={{
                  marginTop: 6,
                  padding: "10px 14px",
                  borderRadius: 12,
                  border: "1px solid rgba(255,255,255,0.1)",
                  background: "rgba(255,255,255,0.04)",
                  color: "var(--gray-50)",
                  width: "100%"
                }}
              />
            </div>
          </div>

          <div className="stack">
            <label style={{ color: "var(--gray-300)", fontSize: 13 }}>Album (optional)</label>
            <select
              className="input"
              value={albumId || ""}
              onChange={(e) => setAlbumId(e.target.value ? Number(e.target.value) : undefined)}
              style={{
                padding: "12px 14px",
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.1)",
                background: "rgba(255,255,255,0.04)",
                color: "var(--gray-50)"
              }}
            >
              <option value="">No Album</option>
              {albums.map((album) => (
                <option key={album.id} value={album.id}>{album.name}</option>
              ))}
            </select>
          </div>
        </div>
        <div style={{ marginTop: 16 }}>
          <label style={{ color: "var(--gray-300)", fontSize: 13, marginBottom: 8, display: "block" }}>Persona</label>
          <div className="glass" style={{ maxHeight: 220, overflow: "auto" }}>
            {filteredPersonas.length === 0 && (
              <p style={{ color: "var(--gray-500)", margin: 0 }}>No personas found yet.</p>
            )}
            <div className="stack">
              {filteredPersonas.map((p) => (
                <button
                  type="button"
                  key={p.name}
                  onClick={() => setPersona(prev => prev === p.name ? undefined : p.name)}
                  style={{
                    textAlign: "left",
                    width: "100%",
                    background: persona === p.name ? "rgba(14,165,233,0.12)" : "transparent",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: 12,
                    padding: "10px 12px",
                    color: "var(--gray-100)",
                    cursor: "pointer"
                  }}
                >
                  <div style={{ fontWeight: 700 }}>{p.name}</div>
                  <div style={{ color: "var(--gray-400)", fontSize: 13 }}>{p.styles || p.description}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? "Generating..." : "Generate Song"}
        </Button>
        {mutation.isError && (
          <span style={{ color: "var(--error)" }}>Failed to start generation, try again.</span>
        )}
      </div>
    </form >
  );
}
