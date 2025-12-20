import { Link } from "react-router-dom";

import { Card } from "../../components/ui/Card";
import type { Song } from "../../types/api";

type Props = {
  songs?: Song[];
  viewMode?: "grid" | "list";
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export function SongGrid({ songs = [], viewMode = "grid" }: Props) {
  const gridStyle = viewMode === "grid"
    ? { gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))" }
    : { gridTemplateColumns: "1fr" };

  return (
    <Card title={`Songs (${songs.length})`}>
      <div className="grid" style={gridStyle}>
        {songs.map((song: Song) => (
          <Link key={song.id} to={`/songs/${song.id}`}>
            <div
              className="glass"
              style={{
                padding: 14,
                borderRadius: 14,
                height: "100%",
                display: viewMode === "list" ? "flex" : "grid",
                gap: 10,
                alignItems: viewMode === "list" ? "center" : "stretch"
              }}
            >
              {viewMode === "grid" && (
                <div
                  style={{
                    borderRadius: 12,
                    height: 120,
                    background: song.album_art
                      ? `url(${API_BASE}/${song.album_art}) center/cover`
                      : "linear-gradient(135deg, rgba(14,165,233,0.2), rgba(8,47,73,0.5))",
                    border: "1px solid rgba(255,255,255,0.06)"
                  }}
                />
              )}
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 800, marginBottom: 4 }}>{song.title}</div>
                <div style={{ color: "var(--gray-400)", fontSize: 13 }}>
                  {song.persona || "No persona"}
                </div>
              </div>
              <div className={`tag status-${song.status}`}>
                {song.status}
              </div>
            </div>
          </Link>
        ))}
        {songs.length === 0 && (
          <p style={{ color: "var(--gray-500)" }}>No songs match your criteria.</p>
        )}
      </div>
    </Card>
  );
}
