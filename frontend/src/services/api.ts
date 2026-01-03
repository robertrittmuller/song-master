import axios from "axios";

import type { Persona, Album, Settings, Song, SongStatus } from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" }
});

export async function fetchPersonas(): Promise<Persona[]> {
  const { data } = await client.get<Persona[]>("/api/personas");
  return data;
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

export async function fetchSongs(): Promise<Song[]> {
  const { data } = await client.get<Song[]>("/api/songs");
  return data;
}

export async function fetchSong(songId: number): Promise<Song> {
  const { data } = await client.get<Song>(`/api/songs/${songId}`);
  return data;
}

export async function deleteSong(songId: number): Promise<void> {
  await client.delete(`/api/songs/${songId}`);
}

export async function createSong(payload: {
  user_prompt: string;
  title?: string;
  persona?: string;
  style?: string;
  genre?: string;
  tempo?: string;
  key?: string;
  instruments?: string;
  mood?: string;
  use_local?: boolean;
  album_id?: number;
  generate_album_art?: boolean;
}) {
  const { data } = await client.post<Song>("/api/songs/generate", payload);
  return data;
}

export async function updateSong(songId: number, payload: Partial<Song>): Promise<Song> {
  const { data } = await client.patch<Song>(`/api/songs/${songId}`, payload);
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
