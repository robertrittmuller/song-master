import axios from "axios";

import type {
  AuthResponse,
  AuthUser,
  BackupRestoreResult,
  DemoTrackStatus,
  AlbumArtAspectRatio,
  Persona,
  Album,
  Settings,
  Song,
  SongProposal,
  SongStatus
} from "../types/api";

function getDefaultApiBase(): string {
  if (typeof window === "undefined") {
    return "http://localhost:8000";
  }

  const protocol = window.location.protocol === "https:" ? "https:" : "http:";
  return `${protocol}//${window.location.hostname}:8000`;
}

function normalizeApiBase(candidate?: string): string {
  if (!candidate) {
    return getDefaultApiBase();
  }

  if (typeof window === "undefined") {
    return candidate;
  }

  try {
    const parsed = new URL(candidate);
    const browserHost = window.location.hostname;
    const browserProtocol = window.location.protocol === "https:" ? "https:" : "http:";
    const isLocalOnlyHost = ["localhost", "127.0.0.1"].includes(parsed.hostname);
    const browserIsRemote = !["localhost", "127.0.0.1"].includes(browserHost);

    if (isLocalOnlyHost && browserIsRemote) {
      parsed.hostname = browserHost;
      parsed.protocol = browserProtocol;
      return parsed.toString().replace(/\/$/, "");
    }

    return parsed.toString().replace(/\/$/, "");
  } catch {
    return getDefaultApiBase();
  }
}

export const API_BASE = normalizeApiBase(import.meta.env.VITE_API_BASE);
const AUTH_STORAGE_KEY = "song-master-access-token";

let accessToken = typeof window !== "undefined"
  ? window.localStorage.getItem(AUTH_STORAGE_KEY)
  : null;

const client = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" }
});

client.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const requestUrl = String(error?.config?.url ?? "");
    const isPublicAuthRequest = ["/api/auth/login", "/api/auth/signup"].some((path) =>
      requestUrl.includes(path)
    );

    if (status === 401 && !isPublicAuthRequest) {
      clearStoredAccessToken();
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("song-master-auth-expired"));
      }
    }

    return Promise.reject(error);
  }
);

export function getStoredAccessToken(): string | null {
  return accessToken;
}

export function storeAccessToken(token: string): void {
  accessToken = token;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(AUTH_STORAGE_KEY, token);
  }
}

export function clearStoredAccessToken(): void {
  accessToken = null;
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
  }
}

export async function login(payload: {
  identifier: string;
  password: string;
}): Promise<AuthResponse> {
  const { data } = await client.post<AuthResponse>("/api/auth/login", payload);
  return data;
}

export async function signup(payload: {
  username: string;
  email: string;
  password: string;
}): Promise<AuthResponse> {
  const { data } = await client.post<AuthResponse>("/api/auth/signup", payload);
  return data;
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const { data } = await client.get<AuthUser>("/api/auth/me");
  return data;
}

export async function changePassword(payload: {
  current_password: string;
  new_password: string;
}): Promise<{ message: string }> {
  const { data } = await client.post<{ message: string }>("/api/auth/change-password", payload);
  return data;
}

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

export async function fetchLyricTags(): Promise<string[]> {
  const { data } = await client.get<string[]>("/api/tags");
  return data;
}

export async function fetchAlbums(): Promise<Album[]> {
  const { data } = await client.get<Album[]>("/api/albums");
  return data;
}

export async function createAlbum(payload: {
  name: string;
  description?: string;
  art_prompt_direction?: string;
}): Promise<Album> {
  const { data } = await client.post<Album>("/api/albums", payload);
  return data;
}

export async function updateAlbum(
  albumId: number,
  payload: { name?: string; description?: string; art_prompt_direction?: string }
): Promise<Album> {
  const { data } = await client.patch<Album>(`/api/albums/${albumId}`, payload);
  return data;
}

export async function generateAlbumCoverArt(
  albumId: number,
  payload: { art_prompt_direction?: string } = {}
): Promise<Album> {
  const { data } = await client.post<Album>(`/api/albums/${albumId}/generate-art`, payload);
  return data;
}

export async function uploadAlbumArt(albumId: number, file: File): Promise<Album> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await client.post<Album>(`/api/albums/${albumId}/upload-art`, formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
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
  lyrics_model?: string;
  album_id?: number;
  vocal_gender?: string;
  rhyme_scheme?: string;
  generate_album_art?: boolean;
  generation_config?: {
    auto_select_fields?: string[];
    no_live_performance?: boolean;
    art_aspect_ratio?: AlbumArtAspectRatio;
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

export async function fetchDemoTrackStatus(songId: number): Promise<DemoTrackStatus> {
  const { data } = await client.get<DemoTrackStatus>(`/api/songs/${songId}/demo-track/status`);
  return data;
}

export const websocketUrl = (songId: number) =>
  {
    const base = API_BASE.replace(/^http/, "ws");
    const url = new URL(`/ws/songs/${songId}/progress`, `${base}/`);
    if (accessToken) {
      url.searchParams.set("token", accessToken);
    }
    return url.toString();
  };

export async function regenerateAlbumArt(
  songId: number,
  payload: { aspect_ratio?: AlbumArtAspectRatio } = {}
): Promise<Song> {
  const { data } = await client.post<Song>(`/api/songs/${songId}/regenerate-art`, payload);
  return data;
}

export async function regenerateLyrics(songId: number, payload: { lyrics_model?: string } = {}): Promise<Song> {
  const { data } = await client.post<Song>(`/api/songs/${songId}/regenerate-lyrics`, payload);
  return data;
}

export async function createDemoTrack(songId: number): Promise<DemoTrackStatus> {
  const { data } = await client.post<DemoTrackStatus>(`/api/songs/${songId}/demo-track`);
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

export async function submitDemoTrackLiveFeedback(songId: number, filePath: string): Promise<Song> {
  const { data } = await client.post<Song>(`/api/songs/${songId}/live-feedback/demo-track`, {
    file_path: filePath,
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
