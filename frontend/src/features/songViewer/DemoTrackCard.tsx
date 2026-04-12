import { useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Download } from "lucide-react";

import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { ProgressBar } from "../../components/ui/ProgressBar";
import { API_BASE, fetchDemoTrackStatus } from "../../services/api";
import type { Song, SongFile } from "../../types/api";

type Props = {
  song: Song;
  isCreating: boolean;
  onRequestCreate: () => void;
};

export function DemoTrackCard({ song, isCreating, onRequestCreate }: Props) {
  const queryClient = useQueryClient();
  const [selectedTrackPath, setSelectedTrackPath] = useState<string | null>(null);

  const demoTracks = useMemo<SongFile[]>(() => {
    return [...(song.files ?? [])]
      .filter((file) => file.file_type === "demo_track" && file.file_path)
      .sort((a, b) => {
        const aIsPrimary = a.is_primary ? 1 : 0;
        const bIsPrimary = b.is_primary ? 1 : 0;
        if (aIsPrimary !== bIsPrimary) {
          return bIsPrimary - aIsPrimary;
        }
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      });
  }, [song.files]);

  const selectedTrack = demoTracks.find((file) => file.file_path === selectedTrackPath) ?? demoTracks[0] ?? null;
  const canCreate = !song.use_local && Boolean(song.clean_lyrics || song.lyrics);

  useEffect(() => {
    setSelectedTrackPath((current) => {
      if (current && demoTracks.some((file) => file.file_path === current)) {
        return current;
      }
      return demoTracks[0]?.file_path ?? null;
    });
  }, [demoTracks, song.id]);

  const { data: demoStatus } = useQuery({
    queryKey: ["demo-track-status", song.id],
    queryFn: () => fetchDemoTrackStatus(song.id),
    enabled: song.status === "completed",
    refetchInterval: (query) => {
      const currentStatus = query.state.data?.status;
      return currentStatus === "queued" || currentStatus === "generating" ? 2000 : false;
    },
  });

  useEffect(() => {
    if (demoStatus?.status === "completed" && demoStatus.logs.length > 0) {
      void queryClient.invalidateQueries({ queryKey: ["song", song.id] });
    }
  }, [demoStatus?.logs.length, demoStatus?.status, queryClient, song.id]);

  const handleDownload = async () => {
    if (!selectedTrack) {
      return;
    }

    const audioUrl = `${API_BASE}/${selectedTrack.file_path}`;
    try {
      const response = await fetch(audioUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = selectedTrack.file_name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to download demo track:", error);
      window.open(audioUrl, "_blank");
    }
  };

  const isActive = demoStatus?.status === "queued" || demoStatus?.status === "generating";
  const isFailed = demoStatus?.status === "failed";

  return (
    <Card
      title="Demo Track"
      action={
        <Button
          variant="ai-glow"
          size="sm"
          isLoading={isCreating}
          disabled={!canCreate || isActive}
          onClick={onRequestCreate}
        >
          {demoTracks.length > 0 ? "Regenerate" : "Create Demo Track"}
        </Button>
      }
    >
      <div className="stack" style={{ gap: 12 }}>
        <p style={{ color: "var(--gray-300)", fontSize: 13, margin: 0, lineHeight: 1.4 }}>
          Generate an MP3 demo track with MiniMax Music Generation using the current saved lyrics and song metadata.
        </p>

        {song.use_local && (
          <div className="glass" style={{ padding: 12, color: "var(--gray-300)", fontSize: 13 }}>
            Demo track generation is disabled for songs created in local-only mode.
          </div>
        )}

        {!song.use_local && !canCreate && (
          <div className="glass" style={{ padding: 12, color: "var(--gray-300)", fontSize: 13 }}>
            Save lyrics on this song before creating a demo track.
          </div>
        )}

        {demoStatus && (isActive || isFailed) && (
          <div className="stack" style={{ gap: 10 }}>
            <ProgressBar value={demoStatus.progress} label={demoStatus.current_stage || "Preparing demo track"} />
            <div className="glass" style={{ padding: 12 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, marginBottom: 10 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>
                  Demo Track Status
                </div>
                <span className="tag">{demoStatus.status}</span>
              </div>
              {demoStatus.error_message && (
                <div style={{ marginBottom: 10, color: "#fca5a5", fontSize: 13 }}>
                  {demoStatus.error_message}
                </div>
              )}
              <div className="stack" style={{ gap: 8, maxHeight: 180, overflow: "auto" }}>
                {demoStatus.logs.map((log) => (
                  <div
                    key={`${log.timestamp}-${log.message}`}
                    style={{
                      padding: "8px 10px",
                      borderRadius: 10,
                      background: "rgba(255,255,255,0.03)",
                      border: "1px solid rgba(255,255,255,0.05)",
                    }}
                  >
                    <div style={{ color: "var(--gray-400)", fontSize: 12 }}>{log.timestamp}</div>
                    <div style={{ color: "var(--gray-100)", fontSize: 13 }}>{log.message}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {selectedTrack ? (
          <>
            <audio controls style={{ width: "100%" }} src={encodeURI(`${API_BASE}/${selectedTrack.file_path}`)}>
              Your browser does not support audio playback.
            </audio>

            <Button variant="secondary" size="sm" onClick={handleDownload} iconLeft={<Download size={14} />}>
              Download MP3
            </Button>

            {demoTracks.length > 1 && (
              <div className="stack" style={{ gap: 8 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>
                  Demo History
                </div>
                <div className="stack" style={{ gap: 6 }}>
                  {demoTracks.map((file) => {
                    const isSelected = file.file_path === selectedTrack.file_path;
                    return (
                      <button
                        key={file.file_path}
                        type="button"
                        className="btn ghost"
                        style={{
                          justifyContent: "space-between",
                          padding: "8px 10px",
                          border: isSelected ? "1px solid rgba(34, 211, 238, 0.35)" : undefined,
                        }}
                        onClick={() => setSelectedTrackPath(file.file_path)}
                      >
                        <span>{file.is_primary ? "Current Demo" : new Date(file.created_at).toLocaleString()}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="glass" style={{ padding: 16, textAlign: "center", color: "var(--gray-400)" }}>
            No demo track yet.
          </div>
        )}
      </div>
    </Card>
  );
}