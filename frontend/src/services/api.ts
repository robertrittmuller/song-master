import axios from "axios";

import type { Persona, Project, Settings, Song, SongStatus } from "../types/api";

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

export async function fetchProjects(): Promise<Project[]> {
  const { data } = await client.get<Project[]>("/api/projects");
  return data;
}

export async function deleteProject(projectId: number): Promise<void> {
  await client.delete(`/api/projects/${projectId}`);
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
  use_local?: boolean;
  project_id?: number;
}) {
  const { data } = await client.post<Song>("/api/songs/generate", payload);
  return data;
}

export async function fetchSongStatus(songId: number): Promise<SongStatus> {
  const { data } = await client.get<SongStatus>(`/api/songs/${songId}/status`);
  return data;
}

export const websocketUrl = (songId: number) =>
  (API_BASE.replace("http", "ws") + `/ws/songs/${songId}/progress`).replace("///", "//");
