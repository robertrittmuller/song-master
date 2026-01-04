import { useMemo, useState } from "react";
import { Copy, Check, Download } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";

import { Card } from "../components/ui/Card";
import { LiveProgress } from "../features/progress/LiveProgress";
import { LyricsSectionView } from "../features/songViewer/LyricsSectionView";
import { LyricVersionTabs } from "../features/songViewer/LyricVersionTabs";
import { LyricDiffView } from "../features/songViewer/LyricDiffView";
import { deleteSong, fetchSong, regenerateAlbumArt, fetchAlbums, updateSong, regenerateLyrics, uploadLiveFeedback } from "../services/api";

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

  const { data: albums = [] } = useQuery({
    queryKey: ["albums"],
    queryFn: fetchAlbums
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSong,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["songs"] });
      navigate("/dashboard");
    }
  });

  const regenerateArtMutation = useMutation({
    mutationFn: regenerateAlbumArt,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["song", songId] });
    }
  });

  const regenerateLyricsMutation = useMutation({
    mutationFn: regenerateLyrics,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["song", songId] });
    }
  });

  const updateSongMutation = useMutation({
    mutationFn: (payload: { album_id: number | null }) => updateSong(songId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["song", songId] });
      queryClient.invalidateQueries({ queryKey: ["songs"] });
    }
  });

  const metadata = useMemo(() => {
    const rawMetadata = song?.metadata || song?.metadata_json;
    if (!rawMetadata) return null;
    try {
      return typeof rawMetadata === "string" ? JSON.parse(rawMetadata) : rawMetadata;
    } catch {
      return null;
    }
  }, [song]);

  const [copiedStyles, setCopiedStyles] = useState(false);
  const [copiedExcludeStyles, setCopiedExcludeStyles] = useState(false);

  const [selectedVersionId, setSelectedVersionId] = useState<number | "current">("current");
  const [isDiffMode, setIsDiffMode] = useState(false);

  const handleCopyStyles = async () => {
    if (!metadata?.suno_styles) return;
    const styles = Array.isArray(metadata.suno_styles)
      ? metadata.suno_styles.join(", ")
      : String(metadata.suno_styles);

    try {
      await navigator.clipboard.writeText(styles);
      setCopiedStyles(true);
      setTimeout(() => setCopiedStyles(false), 2000);
    } catch (err) {
      console.error("Failed to copy styles: ", err);
    }
  };

  const handleCopyExcludeStyles = async () => {
    if (!metadata?.suno_exclude_styles) return;
    const styles = Array.isArray(metadata.suno_exclude_styles)
      ? metadata.suno_exclude_styles.join(", ")
      : String(metadata.suno_exclude_styles);

    try {
      await navigator.clipboard.writeText(styles);
      setCopiedExcludeStyles(true);
      setTimeout(() => setCopiedExcludeStyles(false), 2000);
    } catch (err) {
      console.error("Failed to copy exclude styles: ", err);
    }
  };

  if (isLoading) return <p style={{ color: "var(--gray-400)" }}>Loading...</p>;
  if (!song) return <p style={{ color: "var(--gray-400)" }}>Song not found.</p>;

  return (
    <div className="stack" style={{ gap: 20 }}>
      <Card>
        <div className="section-title" style={{ alignItems: "flex-start" }}>
          <div style={{ flex: 1 }}>
            <div style={{ color: "var(--gray-400)", fontSize: 13 }}>Song</div>
            <h2 style={{ margin: "0 0 4px 0" }}>{song.title}</h2>
            {metadata?.description && (
              <p style={{ color: "var(--gray-300)", fontStyle: "italic", margin: 0, fontSize: 14, lineHeight: 1.4 }}>
                {metadata.description}
              </p>
            )}
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <div className="tag">{song.status}</div>
            {song.status === "completed" && !song.use_local && (
              <button
                type="button"
                className="btn secondary"
                style={{ padding: "10px 12px" }}
                disabled={regenerateArtMutation.isPending}
                onClick={() => {
                  if (!confirm(`Are you sure you want to (re)generate the cover art for "${song.title}"?`)) return;
                  regenerateArtMutation.mutate(song.id);
                }}
              >
                {regenerateArtMutation.isPending ? "Generating..." : song.album_art ? "Regenerate Art" : "Generate Art"}
              </button>
            )}
            {song.status === "completed" && (
              <button
                type="button"
                className="btn secondary"
                style={{ padding: "10px 12px" }}
                disabled={regenerateLyricsMutation.isPending}
                onClick={() => {
                  if (!confirm(`Are you sure you want to regenerate the lyrics for "${song.title}"? This will use the original request and keep the current album art.`)) return;
                  regenerateLyricsMutation.mutate(song.id);
                }}
              >
                {regenerateLyricsMutation.isPending ? "Regenerating..." : "Regenerate Lyrics"}
              </button>
            )}
            <button
              type="button"
              className="btn secondary"
              style={{ padding: "10px 12px", background: "rgba(239, 68, 68, 0.1)", color: "#fca5a5", border: "1px solid rgba(239, 68, 68, 0.2)" }}
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

        <div style={{ display: "flex", gap: 20, marginTop: 16, alignItems: "center" }}>
          <div className="glass" style={{ flex: 1, padding: 12 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: "var(--gray-500)", marginBottom: 4, textTransform: "uppercase" }}>User Prompt</div>
            <p style={{ color: "var(--gray-200)", margin: 0, fontSize: 14, lineHeight: 1.5 }}>{song.user_prompt}</p>
          </div>

          <div className="glass" style={{ width: 240, padding: 12 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: "var(--gray-500)", marginBottom: 4, textTransform: "uppercase" }}>Album</div>
            <select
              className="input"
              style={{ padding: "6px 10px", fontSize: 13 }}
              value={song.album_id || ""}
              onChange={(e) => {
                const val = e.target.value ? Number(e.target.value) : null;
                updateSongMutation.mutate({ album_id: val });
              }}
              disabled={updateSongMutation.isPending}
            >
              <option value="">No Album</option>
              {albums.map((album) => (
                <option key={album.id} value={album.id}>{album.name}</option>
              ))}
            </select>
          </div>
        </div>

        {song.status !== "completed" && Number.isFinite(songId) && (
          <LiveProgress
            songId={songId}
            onRetry={() => regenerateLyricsMutation.mutate(song.id)}
          />
        )}
      </Card>

      {song.status === "completed" && (
        <div className="grid" style={{ gridTemplateColumns: "2fr 1fr", gap: 16 }}>
          <Card title="Song Lyrics">
            {song.versions && song.versions.length > 0 && (
              <LyricVersionTabs
                currentLyrics={song.lyrics || ""}
                versions={song.versions}
                selectedVersionId={selectedVersionId}
                onSelectVersion={setSelectedVersionId}
                isDiffMode={isDiffMode}
                onToggleDiffMode={setIsDiffMode}
              />
            )}

            {selectedVersionId === "current" ? (
              <LyricsSectionView lyrics={song.lyrics || ""} />
            ) : isDiffMode ? (
              <LyricDiffView
                oldLyrics={song.versions?.find(v => v.id === selectedVersionId)?.lyrics || ""}
                newLyrics={song.lyrics || ""}
              />
            ) : (
              <LyricsSectionView lyrics={song.versions?.find(v => v.id === selectedVersionId)?.lyrics || ""} />
            )}
          </Card>
          <div className="stack" style={{ gap: 16 }}>
            {song.album_art && (
              <Card
                title="Album Art"
                action={
                  <button
                    className="btn ghost"
                    style={{ padding: "4px 8px", fontSize: 12, height: "auto", minHeight: 0 }}
                    onClick={async () => {
                      const imageUrl = `${API_BASE}/${song.album_art}`;
                      try {
                        const response = await fetch(imageUrl);
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const link = document.createElement("a");
                        link.href = url;
                        link.download = `${song.title.replace(/\s+/g, "_")}_art.png`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        window.URL.revokeObjectURL(url);
                      } catch (err) {
                        console.error("Failed to download image:", err);
                        // Fallback to opening in new tab if fetch fails (e.g. CORS)
                        window.open(imageUrl, "_blank");
                      }
                    }}
                  >
                    <Download size={14} style={{ marginRight: 4 }} />
                    Download
                  </button>
                }
              >
                <img
                  src={`${API_BASE}/${song.album_art}?t=${new Date().getTime()}`}
                  alt={`${song.title} cover art`}
                  style={{
                    width: "100%",
                    borderRadius: 12,
                    border: "1px solid rgba(255,255,255,0.1)"
                  }}
                />
              </Card>
            )}

            {!song.use_local && (
              <Card title="Live Listen Feedback">
                <div className="stack" style={{ gap: 12 }}>
                  <p style={{ color: "var(--gray-300)", fontSize: 13, margin: 0, lineHeight: 1.4 }}>
                    Upload an MP3 of your current generated song. The AI will listen and provide feedback to improve the lyrics fit.
                  </p>

                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      const form = e.target as HTMLFormElement;
                      const fileInput = form.elements.namedItem("file") as HTMLInputElement;
                      if (!fileInput.files?.length) return;

                      if (!confirm("This will submit the audio to an external LLM for analysis and regenerate the lyrics based on feedback. Continue?")) return;

                      const file = fileInput.files[0];
                      const btn = form.querySelector("button[type=submit]") as HTMLButtonElement;
                      const originalText = btn.textContent;
                      btn.disabled = true;
                      btn.textContent = "Analyzing...";

                      uploadLiveFeedback(song.id, file)
                        .then(() => {
                          queryClient.invalidateQueries({ queryKey: ["song", songId] });
                          form.reset();
                          alert("Feedback received and lyrics updated!");
                        })
                        .catch((err) => {
                          console.error(err);
                          alert("Failed to process feedback: " + (err.response?.data?.detail || err.message));
                        })
                        .finally(() => {
                          btn.disabled = false;
                          btn.textContent = originalText;
                        });
                    }}
                  >
                    <input
                      type="file"
                      name="file"
                      accept=".mp3,audio/mpeg"
                      className="input"
                      style={{ width: "100%", marginBottom: 12, fontSize: 13 }}
                      required
                    />
                    <button type="submit" className="btn primary" style={{ width: "100%" }}>
                      Submit for Feedback
                    </button>
                  </form>

                  {song.live_feedback && (
                    <div className="glass" style={{ padding: 12, marginTop: 12, border: "1px solid rgba(139, 92, 246, 0.3)" }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: "var(--violet-400)", marginBottom: 6, textTransform: "uppercase", display: "flex", alignItems: "center", gap: 6 }}>
                        <div style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--violet-400)" }} />
                        Latest AI Feedback
                      </div>
                      <p style={{ color: "var(--gray-200)", margin: 0, fontSize: 13, lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
                        {song.live_feedback}
                      </p>
                    </div>
                  )}
                </div>
              </Card>
            )}

            <Card title="Metadata">
              <div className="stack" style={{ gap: 16 }}>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <div className="tag" style={{ background: "rgba(255,255,255,0.1)" }}>Persona: {song.persona || "—"}</div>
                  <div className="tag" style={{ background: "rgba(255,255,255,0.1)" }}>Mode: {song.use_local ? "Local" : "Remote"}</div>
                </div>

                {metadata?.suno_styles && (
                  <div className="stack" style={{ gap: 6 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>Suno Styles</div>
                      <button
                        className="btn ghost"
                        style={{ padding: "2px 6px", fontSize: 11, height: "auto", minHeight: 0 }}
                        onClick={handleCopyStyles}
                        title="Copy Styles"
                      >
                        {copiedStyles ? <Check size={12} /> : <Copy size={12} />}
                        {copiedStyles ? "Copied" : "Copy"}
                      </button>
                    </div>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {(Array.isArray(metadata.suno_styles) ? metadata.suno_styles : String(metadata.suno_styles).split(",")).map((s: any) => (
                        <span key={String(s)} className="tag" style={{ fontSize: 11, background: "rgba(139, 92, 246, 0.2)", color: "#c4b5fd", border: "1px solid rgba(139, 92, 246, 0.3)" }}>
                          {String(s).trim()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {metadata?.suno_exclude_styles && metadata.suno_exclude_styles !== "None" && metadata.suno_exclude_styles.length > 0 && (
                  <div className="stack" style={{ gap: 6 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>Exclude</div>
                      <button
                        className="btn ghost"
                        style={{ padding: "2px 6px", fontSize: 11, height: "auto", minHeight: 0 }}
                        onClick={handleCopyExcludeStyles}
                        title="Copy Exclude Styles"
                      >
                        {copiedExcludeStyles ? <Check size={12} /> : <Copy size={12} />}
                        {copiedExcludeStyles ? "Copied" : "Copy"}
                      </button>
                    </div>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {(Array.isArray(metadata.suno_exclude_styles) ? metadata.suno_exclude_styles : String(metadata.suno_exclude_styles).split(",")).map((s: any) => (
                        <span key={String(s)} className="tag" style={{ fontSize: 11, background: "rgba(239, 68, 68, 0.15)", color: "#fca5a5", border: "1px solid rgba(239, 68, 68, 0.3)" }}>
                          {String(s).trim()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid" style={{ gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {[
                    { key: "genre", label: "Genre" },
                    { key: "tempo", label: "Tempo / BPM" },
                    { key: "key", label: "Musical Key" },
                    { key: "mood", label: "Emotional Arc" }
                  ].map(item => metadata?.[item.key] && (
                    <div key={item.key} className="glass" style={{ padding: "10px" }}>
                      <div style={{ fontSize: 10, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase", marginBottom: 2 }}>{item.label}</div>
                      <div style={{ fontSize: 13, color: "var(--gray-100)" }}>{metadata[item.key]}</div>
                    </div>
                  ))}
                </div>

                {metadata?.instruments && (
                  <div className="glass" style={{ padding: "10px" }}>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase", marginBottom: 2 }}>Instruments</div>
                    <div style={{ fontSize: 13, color: "var(--gray-100)" }}>{metadata.instruments}</div>
                  </div>
                )}

                {metadata?.target_audience && (
                  <div className="glass" style={{ padding: "10px" }}>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase", marginBottom: 2 }}>Target Audience</div>
                    <div style={{ fontSize: 13, color: "var(--gray-400)" }}>{metadata.target_audience}</div>
                  </div>
                )}

                {metadata?.commercial_potential && (
                  <div className="glass" style={{ padding: "10px" }}>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase", marginBottom: 2 }}>Commercial Assessment</div>
                    <div style={{ fontSize: 13, color: "var(--gray-400)" }}>{metadata.commercial_potential}</div>
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
