import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ChevronDown, ChevronRight } from "lucide-react";
import {
  API_BASE,
  createAlbum,
  deleteAlbum,
  fetchAlbums,
  generateAlbumCoverArt,
  updateAlbum,
  uploadAlbumArt,
} from "../../services/api";
import type { Album } from "../../types/api";
import { ConfirmationModal } from "../../components/ui/ConfirmationModal";

function AlbumItem({
  album,
  onDelete,
  onSave,
  onGenerateArt,
  onUploadArt,
  isSaving,
  isGeneratingArt,
  isUploadingArt,
}: {
  album: Album;
  onDelete: (id: number) => void;
  onSave: (albumId: number, payload: { description?: string; art_prompt_direction?: string }) => void;
  onGenerateArt: (albumId: number, artPromptDirection?: string) => void;
  onUploadArt: (albumId: number, file: File) => void;
  isSaving: boolean;
  isGeneratingArt: boolean;
  isUploadingArt: boolean;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [visibleSongsCount, setVisibleSongsCount] = useState(12);
  const [descriptionDraft, setDescriptionDraft] = useState(album.description || "");
  const [artPromptDraft, setArtPromptDraft] = useState(album.art_prompt_direction || "");
  const [selectedArtFileName, setSelectedArtFileName] = useState("No file selected");
  const uploadArtInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setDescriptionDraft(album.description || "");
    setArtPromptDraft(album.art_prompt_direction || "");
  }, [album.description, album.art_prompt_direction]);

  const hasDraftChanges =
    descriptionDraft !== (album.description || "") || artPromptDraft !== (album.art_prompt_direction || "");
  const hasAlbumArt = Boolean(album.album_art);

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
          <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 200px) minmax(0, 1fr)", gap: 14, marginBottom: 14 }}>
            <div className="stack" style={{ gap: 10 }}>
              {hasAlbumArt ? (
                <img
                  src={encodeURI(`${API_BASE}/${album.album_art}`)}
                  alt={`${album.name} album art`}
                  style={{
                    width: "100%",
                    aspectRatio: "9 / 16",
                    objectFit: "cover",
                    borderRadius: 12,
                    border: "1px solid rgba(255,255,255,0.1)"
                  }}
                />
              ) : (
                <div className="glass" style={{ padding: 16, minHeight: 180, display: "grid", placeItems: "center", color: "var(--gray-400)" }}>
                  No album art yet.
                </div>
              )}

              <button
                type="button"
                className="btn secondary"
                disabled={isGeneratingArt}
                onClick={() => onGenerateArt(album.id, artPromptDraft)}
              >
                {isGeneratingArt ? "Generating..." : hasAlbumArt ? "Regenerate Art" : "Generate Art"}
              </button>

              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  const file = uploadArtInputRef.current?.files?.[0];
                  if (!file) {
                    return;
                  }

                  const isValidType = ["image/jpeg", "image/png"].includes(file.type);
                  const isValidName = /\.(jpe?g|png)$/i.test(file.name);
                  if (!isValidType && !isValidName) {
                    alert("Please upload a JPEG or PNG image.");
                    return;
                  }

                  onUploadArt(album.id, file);
                }}
              >
                <div className={`file-field ${isUploadingArt ? "is-disabled" : ""}`} style={{ marginBottom: 10 }}>
                  <input
                    ref={uploadArtInputRef}
                    type="file"
                    name="album_art"
                    accept=".jpg,.jpeg,.png,image/jpeg,image/png"
                    className="file-field__input"
                    disabled={isUploadingArt}
                    required
                    onChange={(event) => {
                      const file = event.target.files?.[0];
                      setSelectedArtFileName(file ? file.name : "No file selected");
                    }}
                  />
                  <button
                    type="button"
                    className="btn secondary file-field__button"
                    disabled={isUploadingArt}
                    onClick={() => uploadArtInputRef.current?.click()}
                  >
                    Choose Image
                  </button>
                  <span className={`file-field__name ${selectedArtFileName === "No file selected" ? "is-empty" : ""}`}>
                    {selectedArtFileName}
                  </span>
                </div>

                <button type="submit" className="btn primary" style={{ width: "100%" }} disabled={isUploadingArt}>
                  {isUploadingArt ? "Uploading..." : "Upload Art"}
                </button>
              </form>
            </div>

            <div className="stack" style={{ gap: 12 }}>
              <div className="stack" style={{ gap: 6 }}>
                <label style={{ fontSize: 11, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>
                  Album Description
                </label>
                <textarea
                  className="input"
                  value={descriptionDraft}
                  onChange={(event) => setDescriptionDraft(event.target.value)}
                  placeholder="Give the album a short concept or summary"
                  style={{ minHeight: 82 }}
                />
              </div>

              <div className="stack" style={{ gap: 6 }}>
                <label style={{ fontSize: 11, fontWeight: 700, color: "var(--gray-500)", textTransform: "uppercase" }}>
                  Album Art Direction
                </label>
                <textarea
                  className="input"
                  value={artPromptDraft}
                  onChange={(event) => setArtPromptDraft(event.target.value)}
                  placeholder="Add custom direction before generating the cover art"
                  style={{ minHeight: 110 }}
                />
                <div style={{ fontSize: 12, color: "var(--gray-500)", lineHeight: 1.5 }}>
                  The generator will combine this direction with persona visual styles used on the album and imagery pulled from the songs’ lyrics.
                </div>
              </div>

              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="btn"
                  disabled={!hasDraftChanges || isSaving}
                  onClick={() => onSave(album.id, { description: descriptionDraft, art_prompt_direction: artPromptDraft })}
                >
                  {isSaving ? "Saving..." : "Save Details"}
                </button>
                <button
                  type="button"
                  className="btn secondary"
                  disabled={isGeneratingArt}
                  onClick={() => onGenerateArt(album.id, artPromptDraft)}
                >
                  {isGeneratingArt ? "Generating..." : "Generate With Current Direction"}
                </button>
              </div>
            </div>
          </div>

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
  const [newArtPromptDirection, setNewArtPromptDirection] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

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
      setNewArtPromptDirection("");
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ albumId, payload }: { albumId: number; payload: { description?: string; art_prompt_direction?: string } }) =>
      updateAlbum(albumId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["albums"] });
    }
  });

  const generateArtMutation = useMutation({
    mutationFn: ({ albumId, artPromptDirection }: { albumId: number; artPromptDirection?: string }) =>
      generateAlbumCoverArt(albumId, { art_prompt_direction: artPromptDirection }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["albums"] });
    }
  });

  const uploadArtMutation = useMutation({
    mutationFn: ({ albumId, file }: { albumId: number; file: File }) => uploadAlbumArt(albumId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["albums"] });
    }
  });

  const handleDelete = (id: number) => {
    setConfirmDeleteId(id);
  };

  const confirmDelete = () => {
    if (confirmDeleteId !== null) {
      deleteMutation.mutate(confirmDeleteId);
      setConfirmDeleteId(null);
    }
  };

  const handleSaveAlbum = (albumId: number, payload: { description?: string; art_prompt_direction?: string }) => {
    updateMutation.mutate({ albumId, payload });
  };

  const handleGenerateAlbumArt = (albumId: number, artPromptDirection?: string) => {
    generateArtMutation.mutate({ albumId, artPromptDirection });
  };

  const handleUploadAlbumArt = (albumId: number, file: File) => {
    uploadArtMutation.mutate({ albumId, file });
  };

  if (isLoading) {
    return <p style={{ color: "var(--gray-400)" }}>Loading albums...</p>;
  }

  return (
    <div className="stack" style={{ gap: 14 }}>
      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit,minmax(300px,1fr))", gap: 14 }}>
        {albums.map((album: Album) => (
          <AlbumItem
            key={album.id}
            album={album}
            onDelete={handleDelete}
            onSave={handleSaveAlbum}
            onGenerateArt={handleGenerateAlbumArt}
            onUploadArt={handleUploadAlbumArt}
            isSaving={updateMutation.isPending && updateMutation.variables?.albumId === album.id}
            isGeneratingArt={generateArtMutation.isPending && generateArtMutation.variables?.albumId === album.id}
            isUploadingArt={uploadArtMutation.isPending && uploadArtMutation.variables?.albumId === album.id}
          />
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
            <textarea
              className="input"
              placeholder="Album art direction (optional)"
              value={newArtPromptDirection}
              onChange={(e) => setNewArtPromptDirection(e.target.value)}
              style={{ minHeight: 90 }}
            />
            <div style={{ display: "flex", gap: 8 }}>
              <button
                className="btn"
                disabled={!newName || createMutation.isPending}
                onClick={() => createMutation.mutate({
                  name: newName,
                  description: newDesc,
                  art_prompt_direction: newArtPromptDirection,
                })}
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

      <ConfirmationModal
        isOpen={confirmDeleteId !== null}
        onClose={() => setConfirmDeleteId(null)}
        onConfirm={confirmDelete}
        title="Delete Album"
        message={`Are you sure you want to delete the album "${albums.find(a => a.id === confirmDeleteId)?.name}"? This will NOT delete its songs, they will just be unassigned.`}
        confirmText="Delete"
        variant="danger"
        isConfirming={deleteMutation.isPending}
      />
    </div>
  );
}
