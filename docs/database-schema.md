# Song Master Web GUI - Database Schema Design

## Overview

The database schema is designed to support a multi-user song generation platform with project management, real-time progress tracking, and comprehensive metadata storage. The schema uses SQLite with JSON support for flexible metadata storage.

## Entity Relationship Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│    Users    │────▶│   Projects   │────▶│    Songs    │────▶│  SongFiles   │
│             │     │              │     │             │     │              │
│ - id        │     │ - id         │     │ - id        │     │ - id         │
│ - username  │     │ - user_id    │     │ - project_id│     │ - song_id    │
│ - email     │     │ - name       │     │ - title     │     │ - file_type  │
│ - password  │     │ - description│     │ - user_prompt│    │ - file_path  │
│ - created   │     │ - settings   │     │ - persona   │     │ - file_size  │
│ - updated   │     │ - created    │     │ - lyrics    │     │ - mime_type  │
└─────────────┘     │ - updated    │     │ - metadata  │     │ - created    │
                    └──────────────┘     │ - score     │     └──────────────┘
                                          │ - status    │
                                          │ - config    │
                                          │ - created   │
                                          │ - updated   │
                                          └─────────────┘
                                                 │
                                                 │
                                          ┌──────────────┐
                                          │ UserSettings │
                                          │              │
                                          │ - id         │
                                          │ - user_id    │
                                          │ - key        │
                                          │ - value      │
                                          │ - created    │
                                          │ - updated    │
                                          └──────────────┘
```

## Database Schema

### 1. Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created ON users(created_at);
```

### 2. Projects Table
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    settings JSON, -- Project-specific settings and preferences
    is_public BOOLEAN DEFAULT FALSE,
    tags TEXT, -- JSON array of tags
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_created ON projects(created_at);
CREATE INDEX idx_projects_public ON projects(is_public);
```

### 3. Songs Table
```sql
CREATE TABLE songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    user_prompt TEXT NOT NULL,
    persona VARCHAR(100),
    use_local BOOLEAN DEFAULT FALSE,
    lyrics TEXT,
    clean_lyrics TEXT, -- Lyrics without style tags
    metadata JSON, -- AI-generated metadata (description, styles, etc.)
    score REAL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, generating, completed, failed, cancelled
    generation_config JSON, -- Generation parameters and settings
    error_message TEXT,
    generation_started_at TIMESTAMP,
    generation_completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_songs_project_id ON songs(project_id);
CREATE INDEX idx_songs_status ON songs(status);
CREATE INDEX idx_songs_score ON songs(score);
CREATE INDEX idx_songs_created ON songs(created_at);
CREATE INDEX idx_songs_persona ON songs(persona);
CREATE INDEX idx_songs_title ON songs(title);
```

### 4. SongFiles Table
```sql
CREATE TABLE song_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id INTEGER NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- 'lyrics', 'metadata', 'artwork', 'audio', 'export'
    file_path TEXT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    checksum VARCHAR(64), -- SHA-256 for integrity verification
    is_primary BOOLEAN DEFAULT FALSE, -- Primary file for this type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_song_files_song_id ON song_files(song_id);
CREATE INDEX idx_song_files_type ON song_files(file_type);
CREATE INDEX idx_song_files_primary ON song_files(is_primary);
```

### 5. UserSettings Table
```sql
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    key VARCHAR(100) NOT NULL,
    value JSON NOT NULL,
    category VARCHAR(50) DEFAULT 'general', -- general, llm, generation, ui
    description TEXT,
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, key)
);

-- Indexes
CREATE INDEX idx_user_settings_user_id ON user_settings(user_id);
CREATE INDEX idx_user_settings_key ON user_settings(key);
CREATE INDEX idx_user_settings_category ON user_settings(category);
```

### 6. GenerationSessions Table (for real-time tracking)
```sql
CREATE TABLE generation_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id INTEGER NOT NULL,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    current_stage VARCHAR(100),
    progress_percentage REAL DEFAULT 0.0,
    stage_details JSON, -- Detailed information about current stage
    logs JSON, -- Array of log entries
    error_log TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_generation_sessions_song_id ON generation_sessions(song_id);
CREATE INDEX idx_generation_sessions_session_id ON generation_sessions(session_id);
CREATE INDEX idx_generation_sessions_status ON generation_sessions(current_stage);
```

### 7. Personas Table (cached from file system)
```sql
CREATE TABLE personas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    persona_styles TEXT, -- Extracted styles from persona file
    visual_styles TEXT, -- Visual style descriptions
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_personas_name ON personas(name);
CREATE INDEX idx_personas_active ON personas(is_active);
CREATE INDEX idx_personas_usage ON personas(usage_count);
```

### 8. SystemSettings Table (global application settings)
```sql
CREATE TABLE system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSON NOT NULL,
    category VARCHAR(50) DEFAULT 'general',
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE, -- Can be accessed by frontend
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_system_settings_key ON system_settings(key);
CREATE INDEX idx_system_settings_category ON system_settings(category);
CREATE INDEX idx_system_settings_public ON system_settings(is_public);
```

## SQLAlchemy Model Definitions

### 1. User Model
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    avatar_url = Column(Text)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSetting", back_populates="user", cascade="all, delete-orphan")
```

### 2. Project Model
```python
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    settings = Column(Text)  # JSON string
    is_public = Column(Boolean, default=False)
    tags = Column(Text)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="projects")
    songs = relationship("Song", back_populates="project", cascade="all, delete-orphan")
```

### 3. Song Model
```python
class Song(Base):
    __tablename__ = "songs"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    user_prompt = Column(Text, nullable=False)
    persona = Column(String(100))
    use_local = Column(Boolean, default=False)
    lyrics = Column(Text)
    clean_lyrics = Column(Text)
    metadata = Column(Text)  # JSON string
    score = Column(Integer)  # Store as integer (0-100)
    status = Column(String(50), default="pending")
    generation_config = Column(Text)  # JSON string
    error_message = Column(Text)
    generation_started_at = Column(DateTime(timezone=True))
    generation_completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="songs")
    files = relationship("SongFile", back_populates="song", cascade="all, delete-orphan")
    generation_session = relationship("GenerationSession", back_populates="song", uselist=False)
```

### 4. SongFile Model
```python
class SongFile(Base):
    __tablename__ = "song_files"
    
    id = Column(Integer, primary_key=True, index=True)
    song_id = Column(Integer, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(Text, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    checksum = Column(String(64))
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    song = relationship("Song", back_populates="files")
```

### 5. UserSetting Model
```python
class UserSetting(Base):
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)  # JSON string
    category = Column(String(50), default="general")
    description = Column(Text)
    is_encrypted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="settings")
    
    # Constraints
    __table_args__ = (
        {"extend_existing": True},
    )
```

### 6. GenerationSession Model
```python
class GenerationSession(Base):
    __tablename__ = "generation_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    song_id = Column(Integer, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(255), unique=True, nullable=False)
    current_stage = Column(String(100))
    progress_percentage = Column(Integer, default=0)
    stage_details = Column(Text)  # JSON string
    logs = Column(Text)  # JSON string
    error_log = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    song = relationship("Song", back_populates="generation_session")
```

### 7. Persona Model
```python
class Persona(Base):
    __tablename__ = "personas"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    file_path = Column(Text, nullable=False)
    persona_styles = Column(Text)
    visual_styles = Column(Text)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 8. SystemSetting Model
```python
class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)  # JSON string
    category = Column(String(50), default="general")
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

## Database Migrations

### Initial Migration (001_initial_schema.sql)
```sql
-- Create all tables
-- (Include all CREATE TABLE statements from above)

-- Insert default system settings
INSERT INTO system_settings (key, value, category, description, is_public) VALUES
('app_version', '"1.0.0"', 'general', 'Application version', true),
('max_songs_per_user', '100', 'limits', 'Maximum songs per user', true),
('max_file_size_mb', '50', 'limits', 'Maximum file upload size in MB', true),
('supported_file_types', '["txt", "md", "json", "jpg", "png"]', 'general', 'Supported file types', true),
('default_generation_config', '{"max_rounds": 3, "score_threshold": 8.0}', 'generation', 'Default generation parameters', false);

-- Insert default personas (will be populated from file system)
-- This will be done by the application on startup
```

### Sample Data Migration (002_sample_data.sql)
```sql
-- Create a sample user for testing
INSERT INTO users (username, email, password_hash, first_name, last_name) VALUES
('demo_user', 'demo@example.com', '$2b$12$...', 'Demo', 'User');

-- Create a sample project
INSERT INTO projects (user_id, name, description, settings) VALUES
(1, 'My First Project', 'A demo project for testing', '{"theme": "dark", "auto_save": true}');

-- Create sample songs
INSERT INTO songs (project_id, title, user_prompt, persona, status, score) VALUES
(1, 'Summer Dreams', 'An upbeat pop song about summer love', 'antidote', 'completed', 85),
(1, 'Midnight Drive', 'A rock song about late night adventures', 'bleached_to_perfection', 'completed', 92);

-- Create sample settings
INSERT INTO user_settings (user_id, key, value, category) VALUES
(1, 'llm_provider', '"openai"', 'llm'),
(1, 'default_model', '"gpt-3.5-turbo"', 'llm'),
(1, 'theme', '"dark"', 'ui'),
(1, 'auto_save', 'true', 'ui');
```

## Performance Optimizations

### 1. Indexes Strategy
```sql
-- Composite indexes for common query patterns
CREATE INDEX idx_songs_project_status ON songs(project_id, status);
CREATE INDEX idx_songs_user_created ON songs(project_id, created_at DESC);
CREATE INDEX idx_songs_status_score ON songs(status, score DESC);

-- Full-text search indexes (if using SQLite FTS5)
CREATE VIRTUAL TABLE songs_fts USING fts5(title, user_prompt, lyrics, content='songs', content_rowid='id');
CREATE TRIGGER songs_fts_insert AFTER INSERT ON songs BEGIN
  INSERT INTO songs_fts(rowid, title, user_prompt, lyrics) VALUES (new.id, new.title, new.user_prompt, new.lyrics);
END;
CREATE TRIGGER songs_fts_delete AFTER DELETE ON songs BEGIN
  INSERT INTO songs_fts(songs_fts, rowid, title, user_prompt, lyrics) VALUES ('delete', old.id, old.title, old.user_prompt, old.lyrics);
END;
CREATE TRIGGER songs_fts_update AFTER UPDATE ON songs BEGIN
  INSERT INTO songs_fts(songs_fts, rowid, title, user_prompt, lyrics) VALUES ('delete', old.id, old.title, old.user_prompt, old.lyrics);
  INSERT INTO songs_fts(rowid, title, user_prompt, lyrics) VALUES (new.id, new.title, new.user_prompt, new.lyrics);
END;
```

### 2. Query Optimization Examples

#### Get user's songs with project info
```sql
SELECT s.*, p.name as project_name 
FROM songs s 
JOIN projects p ON s.project_id = p.id 
WHERE p.user_id = ? 
ORDER BY s.created_at DESC 
LIMIT 20 OFFSET ?;
```

#### Get generation progress for a song
```sql
SELECT current_stage, progress_percentage, stage_details, logs 
FROM generation_sessions 
WHERE song_id = ? 
ORDER BY updated_at DESC 
LIMIT 1;
```

#### Search songs by title and content
```sql
SELECT s.*, p.name as project_name 
FROM songs_fts f 
JOIN songs s ON f.rowid = s.id 
JOIN projects p ON s.project_id = p.id 
WHERE songs_fts MATCH ? 
AND p.user_id = ? 
ORDER BY rank;
```

## Data Integrity Constraints

### 1. Check Constraints
```sql
-- Ensure score is between 0 and 100
ALTER TABLE songs ADD CONSTRAINT chk_score_range CHECK (score >= 0 AND score <= 100);

-- Ensure status is valid
ALTER TABLE songs ADD CONSTRAINT chk_valid_status CHECK (status IN ('pending', 'generating', 'completed', 'failed', 'cancelled'));

-- Ensure file types are valid
ALTER TABLE song_files ADD CONSTRAINT chk_valid_file_type CHECK (file_type IN ('lyrics', 'metadata', 'artwork', 'audio', 'export'));

-- Ensure progress percentage is valid
ALTER TABLE generation_sessions ADD CONSTRAINT chk_progress_range CHECK (progress_percentage >= 0 AND progress_percentage <= 100);
```

### 2. Foreign Key Constraints
```sql
-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- All foreign key constraints are defined in the CREATE TABLE statements above
```

## Backup and Recovery Strategy

### 1. Automated Backups
```bash
#!/bin/bash
# backup_database.sh

DB_PATH="/path/to/song_master.db"
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
cp "$DB_PATH" "$BACKUP_DIR/song_master_$DATE.db"

# Compress backup
gzip "$BACKUP_DIR/song_master_$DATE.db"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "song_master_*.db.gz" -mtime +30 -delete
```

### 2. Data Export/Import
```python
def export_user_data(user_id: int) -> dict:
    """Export all user data for GDPR compliance"""
    user = db.query(User).filter(User.id == user_id).first()
    projects = db.query(Project).filter(Project.user_id == user_id).all()
    
    export_data = {
        'user': user.__dict__,
        'projects': [p.__dict__ for p in projects],
        'songs': [],
        'settings': []
    }
    
    for project in projects:
        songs = db.query(Song).filter(Song.project_id == project.id).all()
        export_data['songs'].extend([s.__dict__ for s in songs])
        
        settings = db.query(UserSetting).filter(UserSetting.user_id == user_id).all()
        export_data['settings'].extend([s.__dict__ for s in settings])
    
    return export_data
```

## Security Considerations

### 1. Data Encryption
```python
from cryptography.fernet import Fernet

class EncryptedSetting:
    def __init__(self, key: str):
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

### 2. Input Validation
```python
from pydantic import BaseModel, validator

class SongCreate(BaseModel):
    title: str
    user_prompt: str
    persona: Optional[str] = None
    use_local: bool = False
    
    @validator('title')
    def validate_title(cls, v):
        if len(v) > 255:
            raise ValueError('Title too long')
        return v
    
    @validator('user_prompt')
    def validate_prompt(cls, v):
        if len(v) < 10:
            raise ValueError('Prompt too short')
        if len(v) > 5000:
            raise ValueError('Prompt too long')
        return v
```

This comprehensive database schema provides a solid foundation for the Song Master Web GUI with proper relationships, indexing, constraints, and security considerations.