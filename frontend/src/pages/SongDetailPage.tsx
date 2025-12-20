import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";

import { Card } from "../components/ui/Card";
import { LiveProgress } from "../features/progress/LiveProgress";
import { LyricsSectionView } from "../features/songViewer/LyricsSectionView";
import { deleteSong, fetchSong } from "../services/api";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export function SongDetailPage() {
  const params = useParams();
  const songId = Number(params.songId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: song, isLoading } = useQuery({
    queryKey: ["song", songId],
    queryFn: () => fetchSong(songId),
    enabled: Number.isFinite(songId)
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSong,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["songs"] });
      navigate("/dashboard");
    }
  });

  const metadata = useMemo(() => {
    if (!song?.metadata) return null;
    try {
      return typeof song.metadata === "string" ? JSON.parse(song.metadata) : song.metadata;
    } catch {
      return null;
    }
  }, [song]);

  if (isLoading) return <p style={{ color: "var(--gray-400)" }}>Loading...</p>;
  if (!song) return <p style={{ color: "var(--gray-400)" }}>Song not found.</p>;

  return (
    <div className="stack" style={{ gap: 20 }}>
      <Card>
        <div className="section-title">
          <div>
            <div style={{ color: "var(--gray-400)", fontSize: 13 }}>Song</div>
            <h2 style={{ margin: 0 }}>{song.title}</h2>
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <div className="tag">{song.status}</div>
            <button
              type="button"
              className="btn secondary"
              style={{ padding: "10px 12px" }}
              onClick={() => {
                if (deleteMutation.isPending) return;
                if (!confirm(`Delete song "${song.title}"? This cannot be undone.`)) return;
                deleteMutation.mutate(song.id);
              }}
            >
              Delete
            </button>
          </div>
        </div>
        <p style={{ color: "var(--gray-300)" }}>{song.user_prompt}</p>
        {song.status !== "completed" && Number.isFinite(songId) && <LiveProgress songId={songId} />}
      </Card>

      {song.status === "completed" && (
        <div className="grid" style={{ gridTemplateColumns: "2fr 1fr", gap: 16 }}>
          <Card title="Song Lyrics">
            <LyricsSectionView lyrics={song.lyrics || ""} />
          </Card>
          <div className="stack" style={{ gap: 16 }}>
            {song.album_art && (
              <Card title="Album Art">
                <img
                  src={`${API_BASE}/${song.album_art}`}
                  alt={`${song.title} cover art`}
                  style={{
                    width: "100%",
                    borderRadius: 12,
                    border: "1px solid rgba(255,255,255,0.1)"
                  }}
                />
              </Card>
            )}
            <Card title="Metadata">
              <div className="stack">
                <div className="tag">Persona: {song.persona || "—"}</div>
                <div className="tag">Mode: {song.use_local ? "Local" : "Remote"}</div>
                {metadata &&
                  Object.entries(metadata).map(([key, value]) => (
                    <div key={key} className="glass">
                      <div style={{ fontWeight: 700, textTransform: "capitalize" }}>{key}</div>
                      <div style={{ color: "var(--gray-400)" }}>{String(value)}</div>
                    </div>
                  ))}
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
