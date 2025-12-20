import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { StyleSelector } from "../../components/ui/StyleSelector";
import { Toggle } from "../../components/ui/Toggle";
import { fetchPersonas, fetchSettings, createSong } from "../../services/api";
import type { Persona } from "../../types/api";

export function GenerationForm() {
  const navigate = useNavigate();
  const { data: personas = [] } = useQuery({ queryKey: ["personas"], queryFn: fetchPersonas });
  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: fetchSettings });
  const [prompt, setPrompt] = useState("");
  const [title, setTitle] = useState("");
  const [persona, setPersona] = useState<string | undefined>(settings?.generation.persona);
  const [style, setStyle] = useState("");
  const [useLocal, setUseLocal] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const mutation = useMutation({
    mutationFn: createSong,
    onSuccess: (song) => navigate(`/songs/${song.id}`)
  });

  const filteredPersonas = useMemo<Persona[]>(() => personas, [personas]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!prompt.trim()) return;
    mutation.mutate({
      user_prompt: prompt,
      title: title || undefined,
      persona,
      style: style || undefined,
      use_local: useLocal
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
      </Card>

      <Card title="Song Details">
        <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))" }}>
          <div className="stack">
            <label style={{ color: "var(--gray-300)", fontSize: 13 }}>Song Title (optional)</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="My awesome song"
              style={{
                padding: "12px 14px",
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.1)",
                background: "rgba(255,255,255,0.04)",
                color: "var(--gray-50)"
              }}
            />
          </div>
          <StyleSelector value={style} onChange={setStyle} />
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
                  onClick={() => setPersona(p.name)}
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
        <button
          type="button"
          className="btn secondary"
          style={{ marginTop: 12 }}
          onClick={() => setShowAdvanced((prev) => !prev)}
        >
          {showAdvanced ? "Hide" : "Show"} Advanced Settings
        </button>
        {showAdvanced && settings && (
          <div className="glass" style={{ marginTop: 12 }}>
            <p style={{ margin: "0 0 6px", color: "var(--gray-200)", fontWeight: 700 }}>
              Generation Defaults
            </p>
            <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(200px,1fr))" }}>
              {Object.entries(settings.generation).map(([key, value]) => (
                <div key={key} style={{ color: "var(--gray-400)", fontSize: 13 }}>
                  <strong style={{ color: "var(--gray-200)" }}>{key}</strong>: {String(value || "—")}
                </div>
              ))}
            </div>
          </div>
        )}
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
