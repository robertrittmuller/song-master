export type Persona = {
  name: string;
  description?: string;
  styles?: string;
  visual_styles?: string;
};

export type Album = {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  songs: Song[];
};

export type SongVersion = {
  id: number;
  version_number: number;
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

export type Song = {
  id: number;
  title: string;
  status: string;
  score?: number;
  persona?: string;
  description?: string;
  use_local: boolean;
  created_at: string;
  user_prompt?: string;
  lyrics?: string;
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

export type Settings = {
  llm_provider: string;
  model: string;
  temperature: number;
  max_tokens: number;
  use_local: boolean;
  local_url?: string | null;
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
