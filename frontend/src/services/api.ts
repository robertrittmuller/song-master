import axios from "axios";

import type {
  BackupRestoreResult,
  Persona,
  Album,
  Settings,
  Song,
  SongProposal,
  SongStatus
} from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" }
});

type FetchSongsOptions = {
  limit?: number;
  offset?: number;
};

export async function fetchPersonas(): Promise<Persona[]> {
  const { data } = await client.get<Persona[]>("/api/personas");
  return data;
}

export async function fetchPersona(name: string): Promise<Persona> {
  const { data } = await client.get<Persona>(`/api/personas/${name}`);
  return data;
}

export async function createPersona(payload: {
  name: string;
  styles: string;
  visual_styles?: string;
}): Promise<Persona> {
  const { data } = await client.post<Persona>("/api/personas", payload);
  return data;
}

export async function updatePersona(
  name: string,
  payload: Partial<{ styles: string; visual_styles: string }>
): Promise<Persona> {
  const { data } = await client.put<Persona>(`/api/personas/${name}`, payload);
  return data;
}

export async function deletePersona(name: string): Promise<void> {
  await client.delete(`/api/personas/${name}`);
}

export async function fetchSettings(): Promise<Settings> {
  const { data } = await client.get<Settings>("/api/settings");
  return data;
}

export async function fetchStyles(): Promise<string[]> {
  const { data } = await client.get<string[]>("/api/styles");
  return data;
}

export async function fetchInstruments(): Promise<string[]> {
  const { data } = await client.get<string[]>("/api/instruments");
  return data;
}

export async function fetchAlbums(): Promise<Album[]> {
  const { data } = await client.get<Album[]>("/api/albums");
  return data;
}

export async function createAlbum(payload: { name: string; description?: string }): Promise<Album> {
  const { data } = await client.post<Album>("/api/albums", payload);
  return data;
}

export async function deleteAlbum(albumId: number): Promise<void> {
  await client.delete(`/api/albums/${albumId}`);
}

export async function fetchSongs(options: FetchSongsOptions = {}): Promise<Song[]> {
  const { data } = await client.get<Song[]>("/api/songs", {
    params: options
  });
  return data;
}

export async function fetchSong(songId: number): Promise<Song> {
  const { data } = await client.get<Song>(`/api/songs/${songId}`);
  return data;
}

export async function deleteSong(songId: number): Promise<void> {
  await client.delete(`/api/songs/${songId}`);
}

export async function fetchSongProposals(): Promise<SongProposal[]> {
  const { data } = await client.get<SongProposal[]>("/api/song-proposals");
  return data;
}

export async function generateSongProposals(payload: {
  source_prompt: string;
  count: 5 | 10;
  use_local?: boolean;
}): Promise<SongProposal[]> {
  const { data } = await client.post<{ proposals: SongProposal[] }>(
    "/api/song-proposals/generate",
    payload
  );
  return data.proposals;
}

export async function deleteSongProposal(proposalId: number): Promise<void> {
  await client.delete(`/api/song-proposals/${proposalId}`);
}

export async function createSong(payload: {
  user_prompt: string;
  title: string;
  proposal_id?: number;
  persona?: string;
  style?: string;
  genre?: string;
  tempo?: string;
  key?: string;
  instruments?: string;
  mood?: string;
  use_local?: boolean;
  album_id?: number;
  vocal_gender?: string;
  rhyme_scheme?: string;
  generate_album_art?: boolean;
  generation_config?: {
    auto_select_fields?: string[];
    no_live_performance?: boolean;
  };
}) {
  const { data } = await client.post<Song>("/api/songs/generate", payload);
  return data;
}

export async function updateSong(songId: number, payload: Partial<Song>): Promise<Song> {
  const { data } = await client.patch<Song>(`/api/songs/${songId}`, payload);
  return data;
}

export async function updateSongLyrics(songId: number, lyrics: string): Promise<Song> {
  const { data } = await client.post<Song>(`/api/songs/${songId}/lyrics`, { lyrics });
  return data;
}

export async function fetchSongStatus(songId: number): Promise<SongStatus> {
  const { data } = await client.get<SongStatus>(`/api/songs/${songId}/status`);
  return data;
}

export const websocketUrl = (songId: number) =>
  (API_BASE.replace("http", "ws") + `/ws/songs/${songId}/progress`).replace("///", "//");

export async function regenerateAlbumArt(songId: number): Promise<Song> {
  const { data } = await client.post<Song>(`/api/songs/${songId}/regenerate-art`);
  return data;
}

export async function regenerateLyrics(songId: number): Promise<Song> {
  const { data } = await client.post<Song>(`/api/songs/${songId}/regenerate-lyrics`);
  return data;
}

export async function uploadSongArt(songId: number, file: File): Promise<Song> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await client.post<Song>(`/api/songs/${songId}/upload-art`, formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function uploadLiveFeedback(songId: number, file: File): Promise<Song> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await client.post<Song>(`/api/songs/${songId}/live-feedback`, formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function importSongMarkdown(file: File): Promise<Song> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await client.post<Song>("/api/songs/import", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function downloadBackup(): Promise<void> {
  const response = await client.get<Blob>("/api/backups/export", {
    responseType: "blob"
  });
  const disposition = response.headers["content-disposition"] as string | undefined;
  const filenameMatch = disposition?.match(/filename="?([^"]+)"?/);
  const filename = filenameMatch?.[1] || "song-master-backup.zip";
  const url = window.URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export async function restoreBackup(file: File, dryRun = false): Promise<BackupRestoreResult> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await client.post<BackupRestoreResult>("/api/backups/restore", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    params: { dry_run: dryRun }
  });
  return data;
}
