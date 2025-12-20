export type Persona = {
  name: string;
  description?: string;
  styles?: string;
};

export type Project = {
  id: number;
  name: string;
  description?: string;
  created_at: string;
};

export type Song = {
  id: number;
  title: string;
  status: string;
  score?: number;
  persona?: string;
  use_local: boolean;
  created_at: string;
  user_prompt?: string;
  lyrics?: string;
  metadata?: string;
  metadata_json?: string;
  album_art?: string;
  project_id?: number;
  generation_config?: string;
};

export type SongStatus = {
  song_id: number;
  progress: number;
  current_stage?: string;
  status: string;
  estimated_seconds_remaining?: number | null;
  logs: { timestamp: string; message: string }[];
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
  };
  ui: Record<string, unknown>;
};
