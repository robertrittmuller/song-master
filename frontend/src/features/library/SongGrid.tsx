import { useState, useEffect, useRef, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { Card } from "../../components/ui/Card";
import type { Song } from "../../types/api";

type Props = {
  songs?: Song[];
  viewMode?: "grid" | "list";
  maxRows?: number;
  totalSongsCount?: number;
  headerAction?: ReactNode;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

function formatSongDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric"
  }).format(new Date(value));
}

export function SongGrid({ songs = [], viewMode = "grid", maxRows, totalSongsCount, headerAction }: Props) {
  const [columns, setColumns] = useState(1);
  const gridRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const updateColumns = () => {
      if (gridRef.current) {
        const width = gridRef.current.offsetWidth;
        if (viewMode === "list") {
          setColumns(1);
        } else {
          // Approximate columns based on min-width of 220px
          const calculatedColumns = Math.max(1, Math.floor(width / 220));
          setColumns(calculatedColumns);
        }
      }
    };

    updateColumns(); // Initial calculation

    const resizeObserver = new ResizeObserver(updateColumns);
    if (gridRef.current) {
      resizeObserver.observe(gridRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, [viewMode]);

  const displayedSongs = maxRows ? songs.slice(0, maxRows * columns) : songs;
  const songCountLabel = typeof totalSongsCount === "number"
    ? `${totalSongsCount}`
    : displayedSongs.length < songs.length
      ? `${displayedSongs.length} of ${songs.length}`
      : `${displayedSongs.length}`;

  const gridStyle = viewMode === "grid"
    ? { gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))" }
    : { gridTemplateColumns: "1fr" };

  const cacheBust = Date.now();

  return (
    <Card title={`Songs (${songCountLabel})`} action={headerAction}>
      <div ref={gridRef} className="grid" style={gridStyle}>
        {displayedSongs.map((song: Song) => {
          const previewText = song.user_prompt?.trim() || song.error_message?.trim() || "No prompt preview available.";
          const createdLabel = formatSongDate(song.created_at);
          const showErrorPreview = Boolean(song.error_message) && !song.user_prompt?.trim();

          return (
            <Link
              key={song.id}
              to={`/songs/${song.id}`}
              className="song-grid__item-link"
            >
              <div
                className={`glass song-grid__item song-grid__item--${viewMode}`}
              >
                <div
                  className={`song-grid__thumbnail song-grid__thumbnail--${viewMode}`}
                  style={{
                    backgroundImage: song.album_art
                      ? `url("${encodeURI(`${API_BASE}/${song.album_art}?t=${cacheBust}`)}")`
                      : "linear-gradient(135deg, rgba(14,165,233,0.2), rgba(8,47,73,0.5))"
                  }}
                />
                <div className="song-grid__meta">
                  <div className="song-grid__title-row">
                    <div className="song-grid__title">{song.title}</div>
                    {viewMode === "list" && (
                      <div className={`tag status-${song.status} song-grid__status`}>
                        {song.status}
                      </div>
                    )}
                  </div>
                  {viewMode === "list" ? (
                    <>
                      <div className="song-grid__meta-line">
                        <span className="song-grid__meta-pill">{song.persona || "No persona"}</span>
                        <span className="song-grid__meta-pill">{song.use_local ? "Local" : "Remote"}</span>
                        <span className="song-grid__meta-pill">{createdLabel}</span>
                        {typeof song.score === "number" && (
                          <span className="song-grid__meta-pill">Score {song.score}</span>
                        )}
                      </div>
                      <p className={`song-grid__summary${showErrorPreview ? " is-error" : ""}`}>
                        {previewText}
                      </p>
                    </>
                  ) : (
                    <div className="song-grid__persona">
                      {song.persona || "No persona"}
                    </div>
                  )}
                </div>
                {viewMode === "grid" && (
                  <div className={`tag status-${song.status} song-grid__status`}>
                    {song.status}
                  </div>
                )}
              </div>
            </Link>
          );
        })}
        {displayedSongs.length === 0 && (
          <p style={{ color: "var(--gray-500)" }}>No songs match your criteria.</p>
        )}
      </div>
    </Card>
  );
}
