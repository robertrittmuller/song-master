import { useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, Copy, Check, Download, Pencil } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { ConfirmationModal } from "../components/ui/ConfirmationModal";
import { LiveProgress } from "../features/progress/LiveProgress";
import { DemoTrackCard } from "../features/songViewer/DemoTrackCard";
import { LyricsSectionView } from "../features/songViewer/LyricsSectionView";
import { LyricVersionTabs } from "../features/songViewer/LyricVersionTabs";
import { LyricDiffView } from "../features/songViewer/LyricDiffView";
import { API_BASE, createDemoTrack, deleteSong, fetchSong, fetchSettings, regenerateAlbumArt, fetchAlbums, updateSong, updateSongLyrics, regenerateLyrics, submitDemoTrackLiveFeedback, uploadLiveFeedback, fetchPersonas, uploadSongArt } from "../services/api";
import { copyTextToClipboard } from "../services/clipboard";
import type { AlbumArtAspectRatio, SongFile } from "../types/api";

type LiveFeedbackSource = "upload" | "demo";
const ALBUM_ART_ASPECT_RATIO_OPTIONS: { value: AlbumArtAspectRatio; label: string }[] = [
  { value: "1:1", label: "Square · 1:1" },
  { value: "4:5", label: "Portrait · 4:5" },
  { value: "3:4", label: "Portrait · 3:4" },
  { value: "4:3", label: "Landscape · 4:3" },
  { value: "16:9", label: "Wide · 16:9" },
  { value: "9:16", label: "Vertical · 9:16" }
];

function isAlbumArtAspectRatio(value: unknown): value is AlbumArtAspectRatio {
  return ALBUM_ART_ASPECT_RATIO_OPTIONS.some((option) => option.value === value);
}

function parseAlbumArtAspectRatio(generationConfig?: string | null): AlbumArtAspectRatio {
  if (!generationConfig) {
    return "3:4";
  }
  try {
    const parsed = JSON.parse(generationConfig);
    const ratio = parsed?.art_aspect_ratio;
    return isAlbumArtAspectRatio(ratio) ? ratio : "3:4";
  } catch {
    return "3:4";
  }
}

function modelDisplayName(modelId?: string | null): string {
  if (!modelId) return "Manual edit";
  return modelId.replace(/^openrouter\//, "");
}

function getSortedDemoTracks(files?: SongFile[]): SongFile[] {
  return [...(files ?? [])]
    .filter((file) => file.file_type === "demo_track" && file.file_path)
    .sort((a, b) => {
      const aIsPrimary = a.is_primary ? 1 : 0;
      const bIsPrimary = b.is_primary ? 1 : 0;
      if (aIsPrimary !== bIsPrimary) {
        return bIsPrimary - aIsPrimary;
      }
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });
}

export function SongDetailPage() {
  const params = useParams();
  const songId = Number(params.songId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: song, isLoading } = useQuery({
    queryKey: ["song", songId],
    queryFn: () => fetchSong(songId),
    enabled: Number.isFinite(songId),
    refetchOnMount: "always"
  });

  const { data: albums = [] } = useQuery({
    queryKey: ["albums"],
    queryFn: fetchAlbums
  });

  const { data: personas = [] } = useQuery({
    queryKey: ["personas"],
    queryFn: fetchPersonas
  });

  const { data: settings } = useQuery({
    queryKey: ["settings"],
    queryFn: fetchSettings
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSong,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["songs"] });
      navigate("/");
    }
  });

  const regenerateArtMutation = useMutation({
    mutationFn: (payload: { songId: number; aspectRatio: AlbumArtAspectRatio }) =>
      regenerateAlbumArt(payload.songId, { aspect_ratio: payload.aspectRatio }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["song", songId] });
    }
  });

  const regenerateLyricsMutation = useMutation({
    mutationFn: (payload: { songId: number; lyrics_model?: string }) =>
      regenerateLyrics(payload.songId, payload.lyrics_model ? { lyrics_model: payload.lyrics_model } : {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["song", songId] });
    }
  });

  const createDemoTrackMutation = useMutation({
    mutationFn: createDemoTrack,
    onSuccess: (status) => {
      queryClient.setQueryData(["demo-track-status", songId], status);
    }
  });

  const uploadArtMutation = useMutation({
    mutationFn: (file: File) => uploadSongArt(songId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["song", songId] });
      if (uploadArtInputRef.current) {
        uploadArtInputRef.current.value = "";
      }
      setSelectedArtFileName("No file selected");
    }
  });

  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState("");
  const [editedDescription, setEditedDescription] = useState("");
  const [editedLyrics, setEditedLyrics] = useState<string | null>(null);
  const [selectedArtPath, setSelectedArtPath] = useState<string | null>(null);
  const [selectedArtFileName, setSelectedArtFileName] = useState("No file selected");
  const [selectedFeedbackFileName, setSelectedFeedbackFileName] = useState("No file selected");
  const [liveFeedbackSource, setLiveFeedbackSource] = useState<LiveFeedbackSource>("upload");
  const [selectedLiveDemoTrackPath, setSelectedLiveDemoTrackPath] = useState<string | null>(null);
  const [regenerateLyricsModel, setRegenerateLyricsModel] = useState("");
  const [regenerateArtAspectRatio, setRegenerateArtAspectRatio] = useState<AlbumArtAspectRatio>("3:4");
  const editRef = useRef<HTMLDivElement>(null);
  const uploadArtInputRef = useRef<HTMLInputElement>(null);
  const liveFeedbackInputRef = useRef<HTMLInputElement>(null);
  const liveFeedbackFormRef = useRef<HTMLFormElement>(null);

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

  const updateLyricsMutation = useMutation({
    mutationFn: (lyrics: string) => updateSongLyrics(songId, lyrics),
    onSuccess: (updatedSong) => {
      setEditedLyrics(updatedSong.lyrics || "");
      queryClient.invalidateQueries({ queryKey: ["song", songId] });
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

  const storedAlbumArtAspectRatio = useMemo(
    () => parseAlbumArtAspectRatio(song?.generation_config),
    [song?.generation_config]
  );
  const regenerateArtAspectRatioLabel =
    ALBUM_ART_ASPECT_RATIO_OPTIONS.find((option) => option.value === regenerateArtAspectRatio)?.label || regenerateArtAspectRatio;

  const hasAlbumArt = Boolean(song?.album_art);
  const hasDemoTrack = Boolean(song?.files?.some((file) => file.file_type === "demo_track"));
  const artworkHistory = useMemo<SongFile[]>(() => {
    if (!song) {
      return [];
    }

    const artworkByPath = new Map<string, SongFile>();
    for (const file of song.files ?? []) {
      if (file.file_type === "artwork" && file.file_path) {
        artworkByPath.set(file.file_path, {
          ...file,
          is_primary: file.file_path === song.album_art || file.is_primary,
        });
      }
    }

    if (song.album_art && !artworkByPath.has(song.album_art)) {
      const fileName = song.album_art.split("/").pop() || "album-art";
      artworkByPath.set(song.album_art, {
        id: -1,
        file_type: "artwork",
        file_path: song.album_art,
        file_name: fileName,
        is_primary: true,
        created_at: song.created_at,
      });
    }

    return Array.from(artworkByPath.values()).sort((a, b) => {
      const aIsCurrent = a.file_path === song.album_art ? 1 : 0;
      const bIsCurrent = b.file_path === song.album_art ? 1 : 0;
      if (aIsCurrent !== bIsCurrent) {
        return bIsCurrent - aIsCurrent;
      }
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });
  }, [song]);
  const selectedArtwork = artworkHistory.find((file) => file.file_path === selectedArtPath) ?? artworkHistory[0];
  const demoTracks = useMemo<SongFile[]>(() => getSortedDemoTracks(song?.files), [song?.files]);
  const selectedLiveDemoTrack = demoTracks.find((file) => file.file_path === selectedLiveDemoTrackPath) ?? demoTracks[0] ?? null;
  const regenerateModelOptions = (settings?.models || []).filter((model) => model.source === (song?.use_local ? "local" : "remote"));
  const regenerateFallbackModel = song?.lyrics_model || (song?.use_local ? settings?.local_model : settings?.regenerate_model || settings?.model);

  useEffect(() => {
    setSelectedArtPath(song?.album_art ?? null);
  }, [song?.album_art, songId]);

  useEffect(() => {
    setRegenerateLyricsModel(regenerateFallbackModel || "");
  }, [regenerateFallbackModel, songId]);

  useEffect(() => {
    setRegenerateArtAspectRatio(storedAlbumArtAspectRatio);
  }, [storedAlbumArtAspectRatio, songId]);

  useEffect(() => {
    setSelectedLiveDemoTrackPath((current) => {
      if (current && demoTracks.some((file) => file.file_path === current)) {
        return current;
      }
      return demoTracks[0]?.file_path ?? null;
    });

    if (demoTracks.length === 0) {
      setLiveFeedbackSource("upload");
    }
  }, [demoTracks, songId]);

  useEffect(() => {
    if (song && !isEditing) {
      setEditedTitle(song.title);
      setEditedDescription(metadata?.description || "");
    }
  }, [song, metadata, isEditing]);

  useEffect(() => {
    if (!song) {
      return;
    }
    setEditedLyrics((currentLyrics) => {
      if (currentLyrics === null || currentLyrics === (song.lyrics || "")) {
        return song.lyrics || "";
      }
      return currentLyrics;
    });
  }, [song]);

  const [copiedStyles, setCopiedStyles] = useState(false);
  const [copiedExcludeStyles, setCopiedExcludeStyles] = useState(false);
  const [isLiveFeedbackOpen, setIsLiveFeedbackOpen] = useState(false);
  const [isLiveFeedbackSubmitting, setIsLiveFeedbackSubmitting] = useState(false);
  const [pendingLiveFeedbackFile, setPendingLiveFeedbackFile] = useState<File | null>(null);
  const [liveFeedbackResponse, setLiveFeedbackResponse] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    variant: "primary" | "ai-glow" | "danger";
  }>({
    isOpen: false,
    title: "",
    message: "",
    variant: "primary",
  });

  const [selectedVersionId, setSelectedVersionId] = useState<number | "current">("current");
  const [isDiffMode, setIsDiffMode] = useState(false);
  const [demoTrackResponse, setDemoTrackResponse] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    variant: "primary" | "ai-glow" | "danger";
  }>({
    isOpen: false,
    title: "",
    message: "",
    variant: "primary",
  });

  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    type: "regenerate_art" | "regenerate_lyrics" | "delete_song" | "live_listen" | "create_demo_track" | null;
  }>({
    isOpen: false,
    type: null,
  });

  useEffect(() => {
    setIsEditing(false);
    setEditedTitle("");
    setEditedDescription("");
    setEditedLyrics(null);
    setSelectedVersionId("current");
    setIsDiffMode(false);
    setConfirmDialog({ isOpen: false, type: null });
    setPendingLiveFeedbackFile(null);
    setLiveFeedbackSource("upload");
    setSelectedLiveDemoTrackPath(null);
    setDemoTrackResponse({ isOpen: false, title: "", message: "", variant: "primary" });
    setRegenerateLyricsModel("");
  }, [songId]);

  const closeConfirmDialog = () => {
    setConfirmDialog({ isOpen: false, type: null });
    setPendingLiveFeedbackFile(null);
  };

  const handleConfirmAction = () => {
    if (!confirmDialog.type || !song) return;

    if (confirmDialog.type === "regenerate_art") {
      regenerateArtMutation.mutate({ songId: song.id, aspectRatio: regenerateArtAspectRatio });
    } else if (confirmDialog.type === "regenerate_lyrics") {
      regenerateLyricsMutation.mutate({ songId: song.id, lyrics_model: regenerateLyricsModel || regenerateFallbackModel || undefined });
    } else if (confirmDialog.type === "delete_song") {
      deleteMutation.mutate(song.id);
    } else if (confirmDialog.type === "live_listen") {
      if (liveFeedbackSource === "demo" && selectedLiveDemoTrack) {
        void submitLiveFeedbackFromDemo(selectedLiveDemoTrack);
      } else if (pendingLiveFeedbackFile) {
        void submitLiveFeedback(pendingLiveFeedbackFile);
      }
    } else if (confirmDialog.type === "create_demo_track") {
      createDemoTrackMutation.mutate(song.id, {
        onError: (err: any) => {
          console.error(err);
          setDemoTrackResponse({
            isOpen: true,
            title: "Create Demo Track",
            message: err.response?.data?.detail || err.message || "Failed to start demo track generation.",
            variant: "danger",
          });
        },
      });
    }
    closeConfirmDialog();
  };

  const submitLiveFeedbackFromDemo = async (track: SongFile) => {
    if (!song) return;
    setIsLiveFeedbackSubmitting(true);
    try {
      await submitDemoTrackLiveFeedback(song.id, track.file_path);
      queryClient.invalidateQueries({ queryKey: ["song", songId] });
      setLiveFeedbackResponse({
        isOpen: true,
        title: "Live Listen Feedback",
        message: "Feedback received and lyrics updated!",
        variant: "ai-glow",
      });
    } catch (err: any) {
      console.error(err);
      setLiveFeedbackResponse({
        isOpen: true,
        title: "Live Listen Feedback",
        message: "Failed to process demo track: " + (err.response?.data?.detail || err.message),
        variant: "danger",
      });
    } finally {
      setIsLiveFeedbackSubmitting(false);
    }
  };

  const submitLiveFeedback = async (file: File) => {
    if (!song) return;
    setIsLiveFeedbackSubmitting(true);

    try {
      await uploadLiveFeedback(song.id, file);
      queryClient.invalidateQueries({ queryKey: ["song", songId] });
      liveFeedbackFormRef.current?.reset();
      setSelectedFeedbackFileName("No file selected");
      setLiveFeedbackResponse({
        isOpen: true,
        title: "Live Listen Feedback",
        message: "Feedback received and lyrics updated!",
        variant: "ai-glow",
      });
    } catch (err: any) {
      console.error(err);
      setLiveFeedbackResponse({
        isOpen: true,
        title: "Live Listen Feedback",
        message: "Failed to process feedback: " + (err.response?.data?.detail || err.message),
        variant: "danger",
      });
    } finally {
      setIsLiveFeedbackSubmitting(false);
      setPendingLiveFeedbackFile(null);
    }
  };

  const handleCopyStyles = async () => {
    if (!metadata?.suno_styles) return;
    const styles = Array.isArray(metadata.suno_styles)
      ? metadata.suno_styles.join(", ")
      : String(metadata.suno_styles);

    try {
      await copyTextToClipboard(styles);
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
      await copyTextToClipboard(styles);
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

  const buildSongMarkdown = (lyrics: string) => {
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
    if (!viewedLyrics) return;
    const markdown = buildSongMarkdown(viewedLyrics);
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

  const canEditLyrics = song?.status === "completed" && selectedVersionId === "current" && !isDiffMode;
  const lyricsChanged = editedLyrics !== null && editedLyrics !== (song?.lyrics || "");
  const canSaveLyrics = lyricsChanged && (editedLyrics?.trim().length || 0) > 0;
  const hasLyricsDraft = lyricsChanged;
  const displayLyrics = editedLyrics ?? (song?.lyrics || "");
  const viewedLyrics = useMemo(() => {
    if (!song) return "";
    if (selectedVersionId === "current") {
      return displayLyrics;
    }
    return song.versions?.find((version) => version.id === selectedVersionId)?.lyrics || "";
  }, [displayLyrics, selectedVersionId, song]);
  const viewedLyricsModel = useMemo(() => {
    if (!song) return null;
    if (selectedVersionId === "current") {
      return song.lyrics_model || null;
    }
    return song.versions?.find((version) => version.id === selectedVersionId)?.lyrics_model || null;
  }, [selectedVersionId, song]);

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
            {song.status === "completed" && (
              <>
                <select
                  className="input"
                  style={{ width: 150, padding: "7px 10px", fontSize: 13 }}
                  value={regenerateArtAspectRatio}
                  onChange={(event) => setRegenerateArtAspectRatio(event.target.value as AlbumArtAspectRatio)}
                  disabled={regenerateArtMutation.isPending}
                  aria-label="Album art aspect ratio"
                >
                  {ALBUM_ART_ASPECT_RATIO_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <Button
                  variant="secondary"
                  size="sm"
                  isLoading={regenerateArtMutation.isPending}
                  onClick={() => setConfirmDialog({ isOpen: true, type: "regenerate_art" })}
                >
                  {hasAlbumArt ? "Regenerate Art" : "Generate Art"}
                </Button>
              </>
            )}
            {song.status === "completed" && (
              <>
                <select
                  className="input"
                  style={{ width: 260, padding: "7px 10px", fontSize: 13 }}
                  value={regenerateLyricsModel || regenerateFallbackModel || ""}
                  onChange={(event) => setRegenerateLyricsModel(event.target.value)}
                  disabled={regenerateLyricsMutation.isPending}
                  aria-label="Lyrics regeneration model"
                >
                  {regenerateModelOptions.map((model) => (
                    <option key={`${model.source}-${model.id}`} value={model.id}>
                      {modelDisplayName(model.name || model.id)}{model.recommended ? " (recommended)" : ""}
                    </option>
                  ))}
                  {regenerateModelOptions.length === 0 && regenerateFallbackModel && (
                    <option value={regenerateFallbackModel}>{modelDisplayName(regenerateFallbackModel)}</option>
                  )}
                </select>
                <Button
                  variant="secondary"
                  size="sm"
                  isLoading={regenerateLyricsMutation.isPending}
                  onClick={() => setConfirmDialog({ isOpen: true, type: "regenerate_lyrics" })}
                >
                  Regenerate Lyrics
                </Button>
              </>
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
            onRetry={() => regenerateLyricsMutation.mutate({ songId: song.id, lyrics_model: regenerateLyricsModel || regenerateFallbackModel || undefined })}
          />
        )}
      </Card>

      {song.status === "completed" && (
        <div className="grid" style={{ gridTemplateColumns: "2fr 1fr", gap: 16 }}>
          <Card
            title="Song Lyrics"
            action={
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  className={hasLyricsDraft ? "btn lyric-draft-save" : "btn ghost"}
                  style={{ padding: "4px 8px", fontSize: 12, height: "auto", minHeight: 0 }}
                  onClick={() => updateLyricsMutation.mutate(editedLyrics || "")}
                  disabled={!canEditLyrics || !canSaveLyrics || updateLyricsMutation.isPending}
                >
                  Save as New Version
                </button>
                <button
                  className="btn ghost"
                  style={{ padding: "4px 8px", fontSize: 12, height: "auto", minHeight: 0 }}
                  onClick={handleDownloadLyrics}
                  disabled={!viewedLyrics}
                >
                  <Download size={14} style={{ marginRight: 4 }} />
                  Download .md
                </button>
              </div>
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

            <div className="glass" style={{ padding: 10, marginBottom: 12 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase", marginBottom: 3 }}>
                Lyrics Model
              </div>
              <div style={{ fontSize: 13, color: "var(--gray-200)" }}>{modelDisplayName(viewedLyricsModel)}</div>
            </div>

            {hasLyricsDraft && (
              <div className="lyrics-draft-alert">
                <div className="lyrics-draft-alert__content">
                  <AlertTriangle size={18} />
                  <div>
                    <div className="lyrics-draft-alert__title">Unsaved lyric changes</div>
                    <div className="lyrics-draft-alert__message">
                      Create a new version to keep these edits, or discard the draft.
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                    <button
                      className="btn ghost"
                      style={{ padding: "2px 8px", fontSize: 11, height: "auto", minHeight: 0 }}
                      onClick={() => setEditedLyrics(song.lyrics || "")}
                    >
                      Discard
                    </button>
                </div>
              </div>
            )}

            {selectedVersionId === "current" ? (
              <LyricsSectionView
                lyrics={displayLyrics}
                editable={canEditLyrics}
                onDraftChange={(nextLyrics) => setEditedLyrics(nextLyrics)}
              />
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
                selectedArtwork ? (
                  <button
                    className="btn ghost"
                    style={{ padding: "4px 8px", fontSize: 12, height: "auto", minHeight: 0 }}
                    onClick={async () => {
                      const imageUrl = `${API_BASE}/${selectedArtwork.file_path}`;
                      try {
                        const response = await fetch(imageUrl);
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const link = document.createElement("a");
                        link.href = url;
                        link.download = selectedArtwork.file_name || `${song.title.replace(/\s+/g, "_")}_art.png`;
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
              {selectedArtwork ? (
                <>
                  <img
                    src={encodeURI(`${API_BASE}/${selectedArtwork.file_path}`)}
                    alt={`${song.title} cover art`}
                    style={{
                      width: "100%",
                      borderRadius: 12,
                      border: "1px solid rgba(255,255,255,0.1)"
                    }}
                  />
                  {artworkHistory.length > 1 && (
                    <div className="art-history" aria-label="Artwork history">
                      {artworkHistory.map((file, index) => {
                        const isSelected = file.file_path === selectedArtwork.file_path;
                        const isCurrent = file.file_path === song.album_art;
                        return (
                          <button
                            key={file.file_path}
                            type="button"
                            className={`art-history__item ${isSelected ? "is-selected" : ""}`}
                            onClick={() => setSelectedArtPath(file.file_path)}
                            aria-pressed={isSelected}
                            title={isCurrent ? "Current art" : `Previous art ${index}`}
                          >
                            <img
                              src={encodeURI(`${API_BASE}/${file.file_path}`)}
                              alt={isCurrent ? "Current artwork thumbnail" : `Previous artwork ${index}`}
                            />
                            <span>{isCurrent ? "Current" : new Date(file.created_at).toLocaleDateString()}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </>
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
                <div className={`file-field ${uploadArtMutation.isPending ? "is-disabled" : ""}`} style={{ marginBottom: 10 }}>
                  <input
                    ref={uploadArtInputRef}
                    type="file"
                    name="album_art"
                    accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                    className="file-field__input"
                    disabled={uploadArtMutation.isPending}
                    required
                    onChange={(event) => {
                      const file = event.target.files?.[0];
                      setSelectedArtFileName(file ? file.name : "No file selected");
                    }}
                  />
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    className="file-field__button"
                    disabled={uploadArtMutation.isPending}
                    onClick={() => uploadArtInputRef.current?.click()}
                  >
                    Choose Image
                  </Button>
                  <span className={`file-field__name ${selectedArtFileName === "No file selected" ? "is-empty" : ""}`}>
                    {selectedArtFileName}
                  </span>
                </div>
                <button type="submit" className="btn primary" style={{ width: "100%" }} disabled={uploadArtMutation.isPending}>
                  {uploadArtMutation.isPending ? "Uploading..." : "Upload Art"}
                </button>
              </form>
            </Card>

            <DemoTrackCard
              song={song}
              isCreating={createDemoTrackMutation.isPending}
              onRequestCreate={() => setConfirmDialog({ isOpen: true, type: "create_demo_track" })}
            />

            <Card title="Live Listen Feedback">
                <div className="stack" style={{ gap: 12 }}>
                  <p style={{ color: "var(--gray-300)", fontSize: 13, margin: 0, lineHeight: 1.4 }}>
                    Upload an MP3 or choose a saved demo track. The AI will listen and provide feedback to improve the lyrics fit.
                  </p>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 8 }}>
                    <Button
                      type="button"
                      variant={liveFeedbackSource === "upload" ? "primary" : "secondary"}
                      size="sm"
                      onClick={() => setLiveFeedbackSource("upload")}
                    >
                      Upload MP3
                    </Button>
                    <Button
                      type="button"
                      variant={liveFeedbackSource === "demo" ? "primary" : "secondary"}
                      size="sm"
                      disabled={demoTracks.length === 0}
                      onClick={() => setLiveFeedbackSource("demo")}
                    >
                      Demo Track
                    </Button>
                  </div>

                  <form
                    ref={liveFeedbackFormRef}
                    onSubmit={(e) => {
                      e.preventDefault();
                      if (liveFeedbackSource === "demo") {
                        if (!selectedLiveDemoTrack) {
                          setLiveFeedbackResponse({
                            isOpen: true,
                            title: "Live Listen Feedback",
                            message: "Create a demo track before using one for live listen feedback.",
                            variant: "danger",
                          });
                          return;
                        }
                        setConfirmDialog({ isOpen: true, type: "live_listen" });
                        return;
                      }

                      const form = e.target as HTMLFormElement;
                      const fileInput = form.elements.namedItem("file") as HTMLInputElement;
                      if (!fileInput.files?.length) return;

                      setPendingLiveFeedbackFile(fileInput.files[0]);
                      setConfirmDialog({ isOpen: true, type: "live_listen" });
                    }}
                  >
                    {liveFeedbackSource === "upload" ? (
                      <div className="file-field" style={{ marginBottom: 12 }}>
                        <input
                          ref={liveFeedbackInputRef}
                          type="file"
                          name="file"
                          accept=".mp3,audio/mpeg"
                          className="file-field__input"
                          disabled={isLiveFeedbackSubmitting}
                          required={liveFeedbackSource === "upload"}
                          onChange={(event) => {
                            const file = event.target.files?.[0];
                            setSelectedFeedbackFileName(file ? file.name : "No file selected");
                          }}
                        />
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          className="file-field__button"
                          disabled={isLiveFeedbackSubmitting}
                          onClick={() => liveFeedbackInputRef.current?.click()}
                        >
                          Choose MP3
                        </Button>
                        <span className={`file-field__name ${selectedFeedbackFileName === "No file selected" ? "is-empty" : ""}`}>
                          {selectedFeedbackFileName}
                        </span>
                      </div>
                    ) : (
                      <div className="stack" style={{ gap: 8, marginBottom: 12 }}>
                        <select
                          className="input"
                          value={selectedLiveDemoTrack?.file_path ?? ""}
                          disabled={isLiveFeedbackSubmitting || demoTracks.length === 0}
                          onChange={(event) => setSelectedLiveDemoTrackPath(event.target.value || null)}
                        >
                          {demoTracks.length === 0 ? (
                            <option value="">No demo tracks available</option>
                          ) : (
                            demoTracks.map((file, index) => (
                              <option key={file.file_path} value={file.file_path}>
                                {file.is_primary ? "Current Demo" : `Demo ${demoTracks.length - index}`} - {new Date(file.created_at).toLocaleString()}
                              </option>
                            ))
                          )}
                        </select>
                        {selectedLiveDemoTrack && (
                          <audio controls style={{ width: "100%" }} src={encodeURI(`${API_BASE}/${selectedLiveDemoTrack.file_path}`)}>
                            Your browser does not support audio playback.
                          </audio>
                        )}
                      </div>
                    )}
                    <button type="submit" className="btn primary" style={{ width: "100%" }} disabled={isLiveFeedbackSubmitting || (liveFeedbackSource === "demo" && !selectedLiveDemoTrack)}>
                      {isLiveFeedbackSubmitting ? "Analyzing..." : "Submit for Feedback"}
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

                <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                  {[
                    { key: "genre", label: "Genre" },
                    { key: "tempo", label: "Tempo / BPM" },
                    { key: "key", label: "Musical Key" },
                    { key: "mood", label: "Emotional Arc" }
                  ].map(item => metadata?.[item.key] && (
                    <div key={item.key} className="glass" style={{ padding: "10px", flex: "1 1 45%", minWidth: "200px" }}>
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
          confirmDialog.type === "regenerate_art" ? (hasAlbumArt ? "Regenerate Album Art" : "Generate Album Art") :
          confirmDialog.type === "regenerate_lyrics" ? "Regenerate Lyrics" :
          confirmDialog.type === "create_demo_track" ? (hasDemoTrack ? "Regenerate Demo Track" : "Create Demo Track") :
          confirmDialog.type === "live_listen" ? "Live Listen Feedback" :
          "Delete Song"
        }
        message={
          confirmDialog.type === "regenerate_art" ? `Are you sure you want to ${hasAlbumArt ? "regenerate" : "generate"} the cover art for "${song.title}" as ${regenerateArtAspectRatioLabel}?` :
          confirmDialog.type === "regenerate_lyrics" ? `Are you sure you want to regenerate the lyrics for "${song.title}" with ${modelDisplayName(regenerateLyricsModel || regenerateFallbackModel)}? This will use the original request and keep the current album art.` :
          confirmDialog.type === "create_demo_track" ? `This will send the saved lyrics and metadata for "${song.title}" to the MiniMax Music Generation API. Continue?` :
          confirmDialog.type === "live_listen" ? `This will submit ${liveFeedbackSource === "demo" ? "the selected demo track" : "the uploaded audio"} to an external LLM for analysis and regenerate the lyrics based on feedback. Continue?` :
          `Are you sure you want to delete "${song.title}"? This action cannot be undone.`
        }
        confirmText={
          confirmDialog.type === "delete_song" ? "Delete" :
          confirmDialog.type === "live_listen" ? "Submit" :
          confirmDialog.type === "create_demo_track" ? (hasDemoTrack ? "Regenerate" : "Create") :
          confirmDialog.type === "regenerate_art" ? (hasAlbumArt ? "Regenerate" : "Generate") :
          "Regenerate"
        }
        variant={confirmDialog.type === "delete_song" ? "danger" : "ai-glow"}
        isConfirming={
          confirmDialog.type === "regenerate_art" ? regenerateArtMutation.isPending :
          confirmDialog.type === "regenerate_lyrics" ? regenerateLyricsMutation.isPending :
          confirmDialog.type === "create_demo_track" ? createDemoTrackMutation.isPending :
          confirmDialog.type === "live_listen" ? isLiveFeedbackSubmitting :
          deleteMutation.isPending
        }
      />

      <ConfirmationModal
        isOpen={demoTrackResponse.isOpen}
        onClose={() => setDemoTrackResponse({ isOpen: false, title: "", message: "", variant: "primary" })}
        onConfirm={() => setDemoTrackResponse({ isOpen: false, title: "", message: "", variant: "primary" })}
        title={demoTrackResponse.title}
        message={demoTrackResponse.message}
        confirmText="OK"
        variant={demoTrackResponse.variant}
        showCancel={false}
      />

      <ConfirmationModal
        isOpen={liveFeedbackResponse.isOpen}
        onClose={() => setLiveFeedbackResponse({ isOpen: false, title: "", message: "", variant: "primary" })}
        onConfirm={() => setLiveFeedbackResponse({ isOpen: false, title: "", message: "", variant: "primary" })}
        title={liveFeedbackResponse.title}
        message={liveFeedbackResponse.message}
        confirmText="OK"
        variant={liveFeedbackResponse.variant}
        showCancel={false}
      />
    </div>
  );
}
