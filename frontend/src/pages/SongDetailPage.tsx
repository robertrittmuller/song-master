import { useEffect, useMemo, useRef, useState } from "react";
import { Copy, Check, Download, Pencil } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { ConfirmationModal } from "../components/ui/ConfirmationModal";
import { LiveProgress } from "../features/progress/LiveProgress";
import { LyricsSectionView } from "../features/songViewer/LyricsSectionView";
import { LyricVersionTabs } from "../features/songViewer/LyricVersionTabs";
import { LyricDiffView } from "../features/songViewer/LyricDiffView";
import { deleteSong, fetchSong, regenerateAlbumArt, fetchAlbums, updateSong, regenerateLyrics, uploadLiveFeedback, fetchPersonas, uploadSongArt } from "../services/api";

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

  const { data: personas = [] } = useQuery({
    queryKey: ["personas"],
    queryFn: fetchPersonas
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

  const uploadArtMutation = useMutation({
    mutationFn: (file: File) => uploadSongArt(songId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["song", songId] });
      if (uploadArtInputRef.current) {
        uploadArtInputRef.current.value = "";
      }
    }
  });

  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState("");
  const [editedDescription, setEditedDescription] = useState("");
  const editRef = useRef<HTMLDivElement>(null);
  const uploadArtInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (editRef.current && !editRef.current.contains(event.target as Node)) {
        setIsEditing(false);
      }
    }

    if (isEditing) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isEditing]);

  const updateSongMutation = useMutation({
    mutationFn: (payload: { title?: string; description?: string; album_id?: number | null; persona?: string | null }) => {
      const apiPayload: Record<string, unknown> = {};
      if (payload.title !== undefined) apiPayload.title = payload.title;
      if (payload.description !== undefined) apiPayload.description = payload.description;
      if (payload.album_id !== undefined) apiPayload.album_id = payload.album_id;
      if (payload.persona !== undefined) {
        // If payload.persona is null, we want to send null to the backend to clear it
        // If it's a string, we slugify it
        apiPayload.persona = payload.persona ? payload.persona.toLowerCase().replace(/\s+/g, "_") : null;
      }
      return updateSong(songId, apiPayload as Partial<import("../types/api").Song>);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["song", songId] });
      queryClient.invalidateQueries({ queryKey: ["songs"] });
      setIsEditing(false);
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

  useEffect(() => {
    if (song && !isEditing) {
      setEditedTitle(song.title);
      setEditedDescription(metadata?.description || "");
    }
  }, [song, metadata, isEditing]);

  const [copiedStyles, setCopiedStyles] = useState(false);
  const [copiedExcludeStyles, setCopiedExcludeStyles] = useState(false);
  const [isLiveFeedbackOpen, setIsLiveFeedbackOpen] = useState(false);

  const [selectedVersionId, setSelectedVersionId] = useState<number | "current">("current");
  const [isDiffMode, setIsDiffMode] = useState(false);

  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    type: "regenerate_art" | "regenerate_lyrics" | "delete_song" | "live_listen" | null;
  }>({
    isOpen: false,
    type: null,
  });

  const closeConfirmDialog = () => setConfirmDialog({ isOpen: false, type: null });

  const handleConfirmAction = () => {
    if (!confirmDialog.type || !song) return;

    if (confirmDialog.type === "regenerate_art") {
      regenerateArtMutation.mutate(song.id);
    } else if (confirmDialog.type === "regenerate_lyrics") {
      regenerateLyricsMutation.mutate(song.id);
    } else if (confirmDialog.type === "delete_song") {
      deleteMutation.mutate(song.id);
    } else if (confirmDialog.type === "live_listen") {
      // We'll trigger the form submission manually or move the logic here
      // For now, let's keep it simple and just trigger the mutation if we had one
      // but actually live listen uses a manual fetch call.
      // I'll refactor this better.
    }
    closeConfirmDialog();
  };

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

  const stripStyleTags = (lyrics: string) => {
    const lines = lyrics.split(/\r?\n/);
    const cleanLines: string[] = [];
    const nonSungLinePattern = /^\*[^*]+\*$/;
    const structuralPatterns = [
      /\[Verse\s*\d*\]/i,
      /\[Pre-Chorus\]/i,
      /\[Chorus\]/i,
      /\[Bridge\]/i,
      /\[Outro\]/i,
      /\[Intro\]/i,
      /\[Final Chorus\]/i,
      /\[Guitar Solo\]/i,
      /\[Instrumental\]/i
    ];

    for (const line of lines) {
      const strippedLine = line.trim();
      if (!strippedLine) {
        continue;
      }

      if (nonSungLinePattern.test(strippedLine)) {
        continue;
      }

      let structuralHeader: string | null = null;
      for (const pattern of structuralPatterns) {
        const match = strippedLine.match(pattern);
        if (match) {
          structuralHeader = match[0];
          break;
        }
      }

      if (structuralHeader) {
        cleanLines.push(structuralHeader);
        continue;
      }

      if (/^\[.*\]$/.test(strippedLine)) {
        continue;
      }

      const cleanLine = strippedLine.replace(/^\[.*?\]\s*/, "").trim();
      if (cleanLine) {
        cleanLines.push(cleanLine);
      }
    }

    const resultLines: string[] = [];
    for (let i = 0; i < cleanLines.length; i += 1) {
      const line = cleanLines[i];
      resultLines.push(line);
      if (i < cleanLines.length - 1) {
        const isHeader = structuralPatterns.some((pattern) => pattern.test(line));
        if (isHeader && cleanLines[i + 1].trim()) {
          resultLines.push("");
        }
      }
    }

    return resultLines.join("\n");
  };

  const buildSongMarkdown = () => {
    const description = metadata?.description || "Short description of the song's theme and style.";
    const sunoStyles = metadata?.suno_styles ?? metadata?.genre ?? "rock";
    const sunoExcludeStyles = metadata?.suno_exclude_styles ?? [];
    const stylesLine = Array.isArray(sunoStyles) ? sunoStyles.join(", ") : String(sunoStyles);
    const excludeLine = Array.isArray(sunoExcludeStyles) ? sunoExcludeStyles.join(", ") : String(sunoExcludeStyles);
    const targetAudience = metadata?.target_audience || "Suggested demographic";
    const commercialPotential = metadata?.commercial_potential || "Assessment";
    const mood = metadata?.mood || "happy";
    const tempo = metadata?.tempo || "120";
    const key = metadata?.key || "C";
    const instruments = metadata?.instruments || "guitar,bass,drums";
    const userPrompt = song?.user_prompt || "";
    const lyrics = song?.lyrics || "";
    const cleanLyrics = lyrics ? stripStyleTags(lyrics) : "";
    const albumArtLine = song?.album_art
      ? `![Album Art](${song.album_art.split("/").pop()})\n\n`
      : "";

    return `
## ${song?.title || "Untitled"}
### ${description}

${albumArtLine}## Suno Styles
${stylesLine}

## Suno Exclude-styles
${excludeLine || "None"}

## Additional Metadata
- **Emotional Arc**: ${mood}
- **Target Audience**: ${targetAudience}
- **Commercial Potential**: ${commercialPotential}
- **Technical Notes**: BPM: ${tempo}, Key: ${key}, Instruments: ${instruments}
- **User Prompt**: ${userPrompt}

### Song Lyrics:
${lyrics}

### Clean Lyrics (No Style Tags):
${cleanLyrics}
`.trimStart();
  };

  const handleDownloadLyrics = () => {
    if (!song?.lyrics) return;
    const markdown = buildSongMarkdown();
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    const safeTitle = song.title.replace(/[<>:"/\\|?*]+/g, "").replace(/\s+/g, "_").trim() || "song";
    link.href = url;
    link.download = `${safeTitle}_lyrics.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  if (isLoading) return <p style={{ color: "var(--gray-400)" }}>Loading...</p>;
  if (!song) return <p style={{ color: "var(--gray-400)" }}>Song not found.</p>;

  return (
    <div className="stack" style={{ gap: 20 }}>
      <Card>
        <div className="section-title" style={{ alignItems: "flex-start" }}>
          <div style={{ flex: 1 }}>
            <div style={{ color: "var(--gray-400)", fontSize: 13 }}>Song</div>
            {isEditing ? (
              <div ref={editRef} className="stack" style={{ gap: 8, marginTop: 4 }}>
                <input
                  className="input"
                  style={{
                    fontSize: "var(--text-xl)",
                    fontWeight: "var(--font-bold)",
                    width: "100%",
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    borderRadius: "var(--rounded-sm)",
                    padding: "4px 12px"
                  }}
                  value={editedTitle}
                  onChange={(e) => setEditedTitle(e.target.value)}
                  placeholder="Song Title"
                  autoFocus
                />
                <textarea
                  className="input"
                  style={{
                    width: "100%",
                    minHeight: 60,
                    fontSize: 14,
                    fontStyle: "italic",
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    borderRadius: "var(--rounded-sm)",
                    padding: "8px 12px",
                    resize: "vertical",
                    lineHeight: 1.4
                  }}
                  value={editedDescription}
                  onChange={(e) => setEditedDescription(e.target.value)}
                  placeholder="Add a description..."
                />
                <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
                  <Button
                    variant="success"
                    size="sm"
                    iconLeft={<Check size={16} />}
                    onClick={() => updateSongMutation.mutate({ title: editedTitle, description: editedDescription })}
                    isLoading={updateSongMutation.isPending}
                    disabled={!editedTitle.trim() || (editedTitle === song.title && editedDescription === (metadata?.description || ""))}
                  >
                    Save
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsEditing(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <div 
                className="editable-header" 
                onClick={() => setIsEditing(true)}
                style={{ cursor: "pointer" }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <h2 style={{ margin: "0 0 4px 0" }}>{song.title}</h2>
                  <Pencil size={14} style={{ color: "var(--gray-500)", opacity: 0.6 }} />
                </div>
                {metadata?.description ? (
                  <p style={{ color: "var(--gray-300)", fontStyle: "italic", margin: 0, fontSize: 14, lineHeight: 1.4 }}>
                    {metadata.description}
                  </p>
                ) : (
                  <p style={{ color: "var(--gray-500)", fontStyle: "italic", margin: 0, fontSize: 13 }}>
                    Click to add description...
                  </p>
                )}
              </div>
            )}
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <div className="tag">{song.status}</div>
            {song.status === "completed" && !song.use_local && (
              <Button
                variant="secondary"
                size="sm"
                isLoading={regenerateArtMutation.isPending}
                onClick={() => setConfirmDialog({ isOpen: true, type: "regenerate_art" })}
              >
                {song.album_art ? "Regenerate Art" : "Generate Art"}
              </Button>
            )}
            {song.status === "completed" && (
              <Button
                variant="secondary"
                size="sm"
                isLoading={regenerateLyricsMutation.isPending}
                onClick={() => setConfirmDialog({ isOpen: true, type: "regenerate_lyrics" })}
              >
                Regenerate Lyrics
              </Button>
            )}
            <Button
              variant="danger"
              size="sm"
              onClick={() => setConfirmDialog({ isOpen: true, type: "delete_song" })}
            >
              Delete
            </Button>


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
          <Card
            title="Song Lyrics"
            action={
              <button
                className="btn ghost"
                style={{ padding: "4px 8px", fontSize: 12, height: "auto", minHeight: 0 }}
                onClick={handleDownloadLyrics}
                disabled={!song.lyrics}
              >
                <Download size={14} style={{ marginRight: 4 }} />
                Download .md
              </button>
            }
          >
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
            <Card
              title="Album Art"
              action={
                song.album_art ? (
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
                ) : null
              }
            >
              {song.album_art ? (
                <img
                  src={encodeURI(`${API_BASE}/${song.album_art}?t=${new Date().getTime()}`)}
                  alt={`${song.title} cover art`}
                  style={{
                    width: "100%",
                    borderRadius: 12,
                    border: "1px solid rgba(255,255,255,0.1)"
                  }}
                />
              ) : (
                <div className="glass" style={{ padding: 16, textAlign: "center", color: "var(--gray-400)" }}>
                  No album art yet.
                </div>
              )}

              <form
                style={{ marginTop: 12 }}
                onSubmit={(e) => {
                  e.preventDefault();
                  const form = e.target as HTMLFormElement;
                  const fileInput = form.elements.namedItem("album_art") as HTMLInputElement;
                  const file = fileInput.files?.[0];
                  if (!file) return;

                  const isValidType = ["image/jpeg", "image/png"].includes(file.type);
                  const isValidName = /\.(jpe?g|png)$/i.test(file.name);
                  if (!isValidType && !isValidName) {
                    alert("Please upload a JPEG or PNG image.");
                    return;
                  }

                  uploadArtMutation.mutate(file, {
                    onError: (err: any) => {
                      console.error(err);
                      alert("Failed to upload album art.");
                    }
                  });
                }}
              >
                <input
                  ref={uploadArtInputRef}
                  type="file"
                  name="album_art"
                  accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                  className="input"
                  style={{ width: "100%", marginBottom: 10, fontSize: 13 }}
                  disabled={uploadArtMutation.isPending}
                  required
                />
                <button type="submit" className="btn primary" style={{ width: "100%" }} disabled={uploadArtMutation.isPending}>
                  {uploadArtMutation.isPending ? "Uploading..." : "Upload Art"}
                </button>
              </form>
            </Card>

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
                      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, marginBottom: isLiveFeedbackOpen ? 6 : 0 }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: "var(--violet-400)", textTransform: "uppercase", display: "flex", alignItems: "center", gap: 6 }}>
                          <div style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--violet-400)" }} />
                          Latest AI Feedback
                        </div>
                        <button
                          type="button"
                          className="btn ghost"
                          style={{ padding: "2px 6px", fontSize: 11, height: "auto", minHeight: 0 }}
                          onClick={() => setIsLiveFeedbackOpen((prev) => !prev)}
                        >
                          {isLiveFeedbackOpen ? "Hide" : "Show"}
                        </button>
                      </div>
                      {isLiveFeedbackOpen && (
                        <div className="markdown-content" style={{ color: "var(--gray-200)", fontSize: 13, lineHeight: 1.5 }}>
                          <ReactMarkdown>{song.live_feedback}</ReactMarkdown>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </Card>
            )}

            <Card title="Metadata">
              <div className="stack" style={{ gap: 16 }}>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                  <div className="tag" style={{ background: "rgba(255,255,255,0.1)" }}>Mode: {song.use_local ? "Local" : "Remote"}</div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span className="tag" style={{ background: "rgba(255,255,255,0.1)" }}>Persona:</span>
                    <select
                      className="input"
                      style={{ padding: "4px 8px", fontSize: 12, minWidth: 120 }}
                      value={song.persona ? song.persona.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()) : ""}
                      onChange={(e) => {
                        const val = e.target.value || null;
                        updateSongMutation.mutate({ persona: val });
                      }}
                      disabled={updateSongMutation.isPending}
                    >
                      <option value="">None</option>
                      {personas.map((p) => (
                        <option key={p.name} value={p.name}>{p.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {metadata?.suno_styles && (
                  <div className="stack" style={{ gap: 6 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>Suno Styles</div>
                      <Button
                        variant="ghost"
                        size="sm"
                        style={{ padding: "2px 6px", height: "auto", minHeight: 0 }}
                        onClick={handleCopyStyles}
                        iconLeft={copiedStyles ? <Check size={12} /> : <Copy size={12} />}
                      >
                        {copiedStyles ? "Copied" : "Copy"}
                      </Button>
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
                      <Button
                        variant="ghost"
                        size="sm"
                        style={{ padding: "2px 6px", height: "auto", minHeight: 0 }}
                        onClick={handleCopyExcludeStyles}
                        iconLeft={copiedExcludeStyles ? <Check size={12} /> : <Copy size={12} />}
                      >
                        {copiedExcludeStyles ? "Copied" : "Copy"}
                      </Button>
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

      <ConfirmationModal
        isOpen={confirmDialog.isOpen}
        onClose={closeConfirmDialog}
        onConfirm={handleConfirmAction}
        title={
          confirmDialog.type === "regenerate_art" ? "Regenerate Album Art" :
          confirmDialog.type === "regenerate_lyrics" ? "Regenerate Lyrics" :
          "Delete Song"
        }
        message={
          confirmDialog.type === "regenerate_art" ? `Are you sure you want to (re)generate the cover art for "${song.title}"?` :
          confirmDialog.type === "regenerate_lyrics" ? `Are you sure you want to regenerate the lyrics for "${song.title}"? This will use the original request and keep the current album art.` :
          `Are you sure you want to delete "${song.title}"? This action cannot be undone.`
        }
        confirmText={confirmDialog.type === "delete_song" ? "Delete" : "Regenerate"}
        variant={confirmDialog.type === "delete_song" ? "danger" : "ai-glow"}
        isConfirming={
          confirmDialog.type === "regenerate_art" ? regenerateArtMutation.isPending :
          confirmDialog.type === "regenerate_lyrics" ? regenerateLyricsMutation.isPending :
          deleteMutation.isPending
        }
      />
    </div>
  );
}
