export type Persona = {
  name: string;
  description?: string;
  styles?: string;
  visual_styles?: string;
};

export type AuthUser = {
  id: number;
  username: string;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  created_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: AuthUser;
};

export type Album = {
  id: number;
  name: string;
  description?: string;
  album_art?: string;
  art_prompt_direction?: string;
  created_at: string;
  songs: Song[];
};

export type SongVersion = {
  id: number;
  version_number: number;
  lyrics_model?: string | null;
  lyrics: string;
  created_at: string;
};

export type SongFile = {
  id: number;
  file_type: string;
  file_path: string;
  file_name: string;
  file_size?: number | null;
  mime_type?: string | null;
  is_primary?: boolean | null;
  created_at: string;
};

export type AlbumArtAspectRatio = "1:1" | "4:5" | "3:4" | "4:3" | "16:9" | "9:16";

export type Song = {
  id: number;
  title: string;
  status: string;
  score?: number;
  persona?: string;
  description?: string;
  use_local: boolean;
  lyrics_model?: string | null;
  created_at: string;
  user_prompt?: string;
  lyrics?: string;
  clean_lyrics?: string;
  metadata?: string;
  metadata_json?: string;
  album_art?: string;
  album_id?: number | null;
  vocal_gender?: string;
  generation_config?: string;
  error_message?: string;
  live_feedback?: string;
  versions?: SongVersion[];
  files?: SongFile[];
};

export type SongStatus = {
  song_id: number;
  progress: number;
  current_stage?: string;
  status: string;
  estimated_seconds_remaining?: number | null;
  logs: { timestamp: string; message: string }[];
  error_message?: string | null;
};

export type DemoTrackStatus = {
  song_id: number;
  progress: number;
  current_stage?: string;
  status: string;
  estimated_seconds_remaining?: number | null;
  logs: { timestamp: string; message: string }[];
  error_message?: string | null;
};

export type SongProposal = {
  id: number;
  title: string;
  prompt: string;
  source_prompt: string;
  use_local: boolean;
  status: string;
  accepted_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type Settings = {
  llm_provider: string;
  model: string;
  local_model: string;
  regenerate_model?: string | null;
  temperature: number;
  max_tokens: number;
  use_local: boolean;
  local_url?: string | null;
  recommended_models: string[];
  recommended_local_models: string[];
  models: {
    id: string;
    name?: string | null;
    source: "remote" | "local" | string;
    recommended: boolean;
  }[];
  generation: {
    genre?: string;
    persona?: string;
    tempo?: string;
    key?: string;
    instruments?: string;
    mood?: string;
    vocal_gender?: string;
    rhyme_scheme?: string;
  };
  ui: Record<string, unknown>;
};

export type BackupRestoreResult = {
  dry_run: boolean;
  imported: Record<string, number>;
  skipped: Record<string, number>;
  restored_files: number;
  skipped_files: number;
  warnings: string[];
};
