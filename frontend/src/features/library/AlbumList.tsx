import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ChevronDown, ChevronRight } from "lucide-react";
import { deleteAlbum, fetchAlbums, createAlbum } from "../../services/api";
import type { Album } from "../../types/api";

function AlbumItem({ album, onDelete }: { album: Album; onDelete: (id: number) => void }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const [visibleSongsCount, setVisibleSongsCount] = useState(12);

  return (
    <div key={album.id} className="glass" style={{ padding: 16, borderRadius: 14, display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div
          style={{ cursor: "pointer", flex: 1 }}
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            {isExpanded ? <ChevronDown size={18} color="var(--gray-400)" /> : <ChevronRight size={18} color="var(--gray-400)" />}
            <div style={{ fontWeight: 800, fontSize: 16 }}>{album.name}</div>
          </div>
          <div style={{ color: "var(--gray-400)", fontSize: 13, marginTop: 2, paddingLeft: 24 }}>{album.description || "No description"}</div>
        </div>
        <button
          type="button"
          className="btn secondary"
          style={{ padding: "6px 8px", fontSize: 12 }}
          onClick={(e) => {
            e.preventDefault();
            onDelete(album.id);
          }}
        >
          Delete
        </button>
      </div>

      {isExpanded && (
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 10, paddingLeft: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase", marginBottom: 6 }}>
            Songs ({album.songs?.length || 0})
          </div>
          {album.songs && album.songs.length > 0 ? (
            <div className="stack" style={{ gap: 8 }}>
              <div className="stack" style={{ gap: 4 }}>
                {album.songs.slice(0, visibleSongsCount).map((song) => (
                  <Link
                    key={song.id}
                    to={`/songs/${song.id}`}
                    style={{
                      fontSize: 13,
                      color: "var(--gray-300)",
                      textDecoration: "none",
                      padding: "4px 6px",
                      borderRadius: 6,
                      background: "rgba(255,255,255,0.03)",
                      border: "1px solid rgba(255,255,255,0.05)"
                    }}
                    className="hover-card"
                  >
                    {song.title}
                  </Link>
                ))}
              </div>

              {album.songs.length > visibleSongsCount && (
                <button
                  className="btn secondary"
                  style={{ alignSelf: "flex-start", padding: "4px 8px", fontSize: 11 }}
                  onClick={() => setVisibleSongsCount(prev => prev + 12)}
                >
                  Show More ({album.songs.length - visibleSongsCount} remaining)
                </button>
              )}
            </div>
          ) : (
            <div style={{ fontSize: 12, color: "var(--gray-600)", fontStyle: "italic" }}>
              No songs in this album yet.
            </div>
          )}
        </div>
      )}

      <div style={{ color: "var(--gray-600)", fontSize: 11, marginTop: "auto", paddingLeft: 24 }}>
        Created: {new Date(album.created_at).toLocaleDateString()}
      </div>
    </div>
  );
}

export function AlbumList() {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");

  const { data: albums = [], isLoading } = useQuery({ queryKey: ["albums"], queryFn: fetchAlbums });

  const deleteMutation = useMutation({
    mutationFn: deleteAlbum,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["albums"] });
    }
  });

  const createMutation = useMutation({
    mutationFn: createAlbum,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["albums"] });
      setIsCreating(false);
      setNewName("");
      setNewDesc("");
    }
  });

  const handleDelete = (id: number) => {
    const album = albums.find(a => a.id === id);
    if (!album) return;
    if (deleteMutation.isPending) return;
    if (!confirm(`Delete album "${album.name}"? This will NOT delete its songs, they will just be unassigned.`)) return;
    deleteMutation.mutate(id);
  };

  if (isLoading) {
    return <p style={{ color: "var(--gray-400)" }}>Loading albums...</p>;
  }

  return (
    <div className="stack" style={{ gap: 14 }}>
      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(300px,1fr))", gap: 14 }}>
        {albums.map((album: Album) => (
          <AlbumItem key={album.id} album={album} onDelete={handleDelete} />
        ))}
        {albums.length === 0 && !isCreating && <p style={{ color: "var(--gray-500)" }}>No albums yet.</p>}
      </div>

      {!isCreating ? (
        <button className="btn secondary" style={{ alignSelf: "flex-start" }} onClick={() => setIsCreating(true)}>
          + Create New Album
        </button>
      ) : (
        <div className="glass" style={{ padding: 16, borderRadius: 14, maxWidth: 400 }}>
          <h4 style={{ marginBottom: 12 }}>New Album</h4>
          <div className="stack" style={{ gap: 12 }}>
            <input
              className="input"
              placeholder="Album Name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
            <textarea
              className="input"
              placeholder="Description (optional)"
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              style={{ minHeight: 60 }}
            />
            <div style={{ display: "flex", gap: 8 }}>
              <button
                className="btn"
                disabled={!newName || createMutation.isPending}
                onClick={() => createMutation.mutate({ name: newName, description: newDesc })}
              >
                {createMutation.isPending ? "Creating..." : "Save Album"}
              </button>
              <button className="btn secondary" onClick={() => setIsCreating(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
