import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { Card } from "../components/ui/Card";
import { SongGrid } from "../features/library/SongGrid";
import { fetchSongs } from "../services/api";

export function LandingPage() {
  const { data: songs = [] } = useQuery({ queryKey: ["songs"], queryFn: fetchSongs });

  // Show only the 8 most recent songs on the landing page
  const recentSongs = songs.slice(0, 8);

  return (
    <div className="stack" style={{ gap: 20 }}>
      <Card>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.1fr 0.9fr",
            gap: 24,
            alignItems: "center"
          }}
        >
          <div className="stack" style={{ gap: 14 }}>
            <div className="pill">AI Songwriting for Suno</div>
            <h1 style={{ margin: 0, fontSize: 34 }}>
              Generate your next hit with Song Master!
            </h1>
            <p style={{ color: "var(--gray-300)", fontSize: 16 }}>
              Transform prompts into performance-ready lyrics, track progress live, and manage every
              song from one streamlined workspace.
            </p>
            <div style={{ display: "flex", gap: 12 }}>
              <Link to="/generate" className="btn">
                Quick Start
              </Link>
              <Link to="/dashboard" className="btn secondary">
                View Albums
              </Link>
            </div>
          </div>
          <div className="glass" style={{ padding: 20 }}>
            <p style={{ margin: 0, color: "var(--gray-200)", fontWeight: 700 }}>Highlights</p>
            <ul style={{ color: "var(--gray-300)", lineHeight: 1.5 }}>
              <li>Persona-based generation with real-time stage tracking</li>
              <li>Album art previews, clean lyric exports, and metadata at a glance</li>
              <li>Dashboard for albums, favorites, and recently viewed songs</li>
            </ul>
          </div>
        </div>
      </Card>

      <SongGrid songs={recentSongs} />

      <Card title="Feature Highlights">
        <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(240px,1fr))" }}>
          {[
            { title: "🎵 AI-Powered Lyrics", body: "Multi-stage agentic pipeline aligned with the CLI." },
            { title: "🎨 Album Art", body: "Preview cover concepts while the song is generating." },
            { title: "📊 Progress", body: "Stage-aware tracker with ETA, logs, and live notifications." },
            { title: "🎭 Personas", body: "Browse and apply curated personas or add your own." }
          ].map((item) => (
            <div key={item.title} className="glass">
              <div style={{ fontWeight: 700 }}>{item.title}</div>
              <p style={{ color: "var(--gray-400)" }}>{item.body}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
