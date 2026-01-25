import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { ProgressBar } from "../../components/ui/ProgressBar";
import { fetchSongStatus, websocketUrl } from "../../services/api";
import type { SongStatus } from "../../types/api";

type Props = {
  songId: number;
  onRetry?: () => void;
};

export function LiveProgress({ songId, onRetry }: Props) {
  const [wsStatus, setWsStatus] = useState<SongStatus | null>(null);

  const { data: httpStatus } = useQuery({
    queryKey: ["song-status", songId],
    queryFn: () => fetchSongStatus(songId),
    refetchInterval: 2000,
    enabled: !wsStatus
  });

  useEffect(() => {
    const ws = new WebSocket(websocketUrl(songId));
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as SongStatus;
        setWsStatus(payload);
      } catch {
        // ignore parse issues from dev server noise
      }
    };
    ws.onerror = () => ws.close();
    return () => ws.close();
  }, [songId]);

  const status = wsStatus ?? httpStatus;
  const logs = useMemo(() => status?.logs ?? [], [status]);

  if (!status) {
    return <p style={{ color: "var(--gray-400)" }}>Waiting for status...</p>;
  }

  return (
    <div className="stack">
      <ProgressBar value={status.progress} label={status.current_stage || "Preparing"} />
      <div className="glass">
        <div className="section-title">
          <span>Live Logs</span>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {(status.status === "failed" || status.status === "error") && onRetry && (
              <button
                type="button"
                className="btn secondary"
                style={{ padding: "4px 10px", fontSize: 13 }}
                onClick={onRetry}
              >
                Retry Generation
              </button>
            )}
            <span className="pill" style={{
              background: (status.status === "failed" || status.status === "error") ? "rgba(239, 68, 68, 0.1)" : undefined,
              color: (status.status === "failed" || status.status === "error") ? "#fca5a5" : undefined,
              borderColor: (status.status === "failed" || status.status === "error") ? "rgba(239, 68, 68, 0.2)" : undefined,
            }}>
              {status.status}
            </span>
          </div>
        </div>

        {(status.status === "failed" || status.status === "error") && status.error_message && (
          <div style={{
            margin: "12px 0",
            padding: 12,
            borderRadius: 12,
            background: "rgba(239, 68, 68, 0.05)",
            border: "1px solid rgba(239, 68, 68, 0.1)",
            color: "#fca5a5",
            fontSize: 14
          }}>
            <strong>Error:</strong> {status.error_message}
          </div>
        )}

        <div className="stack" style={{ marginTop: 12, maxHeight: 260, overflow: "auto" }}>
          {logs.map((log) => (
            <div
              key={`${log.timestamp}-${log.message}`}
              style={{
                padding: "8px 10px",
                borderRadius: 10,
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.05)"
              }}
            >
              <div style={{ color: "var(--gray-400)", fontSize: 12 }}>{log.timestamp}</div>
              <div style={{ color: "var(--gray-100)" }}>{log.message}</div>
            </div>
          ))}
          {logs.length === 0 && <p style={{ color: "var(--gray-500)" }}>No events yet.</p>}
        </div>
      </div>
    </div>
  );
}
