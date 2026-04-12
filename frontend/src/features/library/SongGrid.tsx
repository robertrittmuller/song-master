import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";

import { Card } from "../../components/ui/Card";
import type { Song } from "../../types/api";

type Props = {
  songs?: Song[];
  viewMode?: "grid" | "list";
  maxRows?: number;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export function SongGrid({ songs = [], viewMode = "grid", maxRows }: Props) {
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

  const gridStyle = viewMode === "grid"
    ? { gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))" }
    : { gridTemplateColumns: "1fr" };

  return (
    <Card title={`Songs (${displayedSongs.length}${maxRows ? ` of ${songs.length}` : ""})`}>
      <div ref={gridRef} className="grid" style={gridStyle}>
        {displayedSongs.map((song: Song) => (
          <Link
            key={song.id}
            to={`/songs/${song.id}`}
            className="song-grid__item-link"
          >
            <div
              className={`glass song-grid__item song-grid__item--${viewMode}`}
            >
              {viewMode === "grid" && (
                <div
                  className="song-grid__thumbnail"
                  style={{
                    backgroundImage: song.album_art
                      ? `url("${encodeURI(`${API_BASE}/${song.album_art}?t=${new Date().getTime()}`)}")`
                      : "linear-gradient(135deg, rgba(14,165,233,0.2), rgba(8,47,73,0.5))"
                  }}
                />
              )}
              <div className="song-grid__meta">
                <div className="song-grid__title">{song.title}</div>
                <div className="song-grid__persona">
                  {song.persona || "No persona"}
                </div>
              </div>
              <div className={`tag status-${song.status} song-grid__status`}>
                {song.status}
              </div>
            </div>
          </Link>
        ))}
        {displayedSongs.length === 0 && (
          <p style={{ color: "var(--gray-500)" }}>No songs match your criteria.</p>
        )}
      </div>
    </Card>
  );
}
