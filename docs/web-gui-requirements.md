# Song Master Web GUI - Requirements Specification

## Album Overview
Create a visually stunning and functional web-based GUI for the Song Master Python CLI tool, enabling users to generate AI-powered songs through an intuitive web interface.

## Current CLI Architecture Analysis

### Core Features to Web-ify
1. **Multi-stage AI Song Generation Pipeline**
2. **Persona-based Style Application**
3. **Real-time Progress Tracking**
4. **File Management & Export**
5. **Configuration & Settings Management**
6. **Album Art Generation & Display**

### Technical Stack
- **Backend**: Python with FastAPI (already in requirements)
- **Frontend**: React with TypeScript
- **Database**: SQLite with SQLAlchemy
- **Real-time Communication**: WebSockets
- **State Management**: React Query + local React state
- **Styling**: Custom CSS plus component-level styling
- **Build Tool**: Vite

## Functional Requirements

### 1. User Interface Requirements

#### 1.1 Landing Page
- Clean, modern design with song generation preview
- Quick start guide and feature highlights
- Access to existing albums
- Settings and configuration access

#### 1.2 Song Generation Workflow
- **Input Form**:
  - Text area for song description/prompt
  - File upload option for prompt files
  - Optional song name/title field
  - Persona selection dropdown with preview
  - Local vs Remote LLM mode toggle
  - Advanced settings expandable panel

#### 1.3 Real-time Progress Tracking
- Multi-stage progress indicator showing:
  1. Parsing user input and persona
  2. Loading resources (styles, tags, personas)
  3. Generating initial song draft
  4. Reviewing and refining lyrics
  5. Applying critic feedback
  6. Running preflight checks
  7. Generating metadata summary
  8. Generating album artwork
  9. Formatting and saving final song
- Live updates via WebSocket
- Current stage details and logs

#### 1.4 Results Display
- **Song Viewer**:
  - Formatted lyrics with proper section headers
  - Metadata display (description, styles, target audience)
  - Clean lyrics view (no style tags)
  - Technical parameters (BPM, key, instruments)
- **Album Art Display**:
  - Generated artwork preview
  - Download options
  - Regeneration capability
- **Export Options**:
  - Markdown file download
  - JSON data export
  - Album art download

### 2. Album Management

#### 2.1 Album Dashboard
- Grid/list view of all generated songs
- Search and filter capabilities
- Sorting by date, name, genre, score
- Bulk operations (delete, export)

#### 2.2 Song Library
- Organized song storage
- Tag and category system
- Favorites and recently viewed
- Sharing capabilities

### 3. Configuration Management

#### 3.1 Settings Panel
- **LLM Configuration**:
  - API key management
  - Model selection
  - Temperature and token limits
  - Local vs remote mode settings
- **Generation Parameters**:
  - Review max rounds
  - Score threshold
  - Default song parameters (genre, tempo, key, instruments, mood)
- **UI Preferences**:
  - Theme selection
  - Notification settings
  - Auto-save preferences

#### 3.2 Resource Management
- **Personas**:
  - View all available personas
  - Preview persona styles
  - Add/edit custom personas
- **Styles & Tags**:
  - Browse available styles
  - Tag library management
  - Custom style creation

### 4. File Management System

#### 4.1 Upload/Download
- Prompt file upload with validation
- Bulk export of multiple songs
- Album art management
- Template management

#### 4.2 File Operations
- View generated files
- Regenerate album art for existing songs
- Edit song metadata
- Delete and archive songs

## Non-Functional Requirements

### 1. Performance Requirements
- Initial page load < 3 seconds
- Song generation progress updates < 1 second latency
- Support for concurrent song generations
- Efficient file handling for large lyrics

### 2. Usability Requirements
- Intuitive workflow matching CLI experience
- Responsive design for desktop and tablet
- Accessibility compliance (WCAG 2.1 AA)
- Error handling with clear user feedback

### 3. Reliability Requirements
- Graceful handling of API failures
- Auto-save functionality
- Data persistence and backup
- Error recovery and retry mechanisms

### 4. Security Requirements
- Secure API key storage
- Input validation and sanitization
- File upload restrictions
- Session management

## Technical Architecture

### 1. Backend Architecture (FastAPI)

#### 1.1 API Endpoints
```
GET  /api/songs - List songs
POST /api/songs/generate - Start song generation
POST /api/songs/import - Import a markdown song
GET  /api/songs/{id} - Get song details
GET  /api/songs/{id}/status - Get generation status
PATCH /api/songs/{id} - Update song metadata
POST /api/songs/{id}/lyrics - Update lyrics
POST /api/songs/{id}/regenerate-art - Regenerate album art
POST /api/songs/{id}/upload-art - Upload custom album art
POST /api/songs/{id}/regenerate-lyrics - Regenerate lyrics
POST /api/songs/{id}/live-feedback - Submit audio for Live Listen feedback
DELETE /api/songs/{id} - Delete song

GET  /api/personas - List all personas
GET  /api/personas/{name} - Get persona details
POST /api/personas - Create persona
PUT  /api/personas/{name} - Update persona
DELETE /api/personas/{name} - Delete persona

GET  /api/styles - List available styles
GET  /api/instruments - List available instruments

GET  /api/settings - Get frontend settings payload

GET  /api/albums - List albums
POST /api/albums - Create new album
GET  /api/albums/{id} - Get album details
DELETE /api/albums/{id} - Delete album
```

#### 1.2 WebSocket Endpoints
```
WS /ws/songs/{id}/progress - Real-time generation updates
```

#### 1.3 Database Schema
```sql
-- Albums table
CREATE TABLE albums (
    id INTEGER PRIMARY KEY,
    user_id INTEGER, -- nullable in the current implementation
    name TEXT NOT NULL,
    description TEXT,
    settings TEXT, -- JSON string
    is_public BOOLEAN DEFAULT FALSE,
    tags TEXT, -- JSON string
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Songs table
CREATE TABLE songs (
    id INTEGER PRIMARY KEY,
    album_id INTEGER, -- nullable so songs can survive album deletion
    title TEXT NOT NULL,
    user_prompt TEXT NOT NULL,
    persona TEXT,
    style TEXT,
    vocal_gender TEXT,
    use_local BOOLEAN DEFAULT FALSE,
    lyrics TEXT,
    clean_lyrics TEXT,
    metadata TEXT, -- JSON
    album_art TEXT,
    score INTEGER,
    status TEXT,
    generation_config TEXT, -- JSON
    error_message TEXT,
    live_feedback TEXT,
    generation_started_at TIMESTAMP,
    generation_completed_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (album_id) REFERENCES albums (id) ON DELETE SET NULL
);

-- Song files table
CREATE TABLE song_files (
    id INTEGER PRIMARY KEY,
    song_id INTEGER NOT NULL,
    file_type TEXT NOT NULL, -- 'lyrics', 'metadata', 'artwork'
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (song_id) REFERENCES songs (id)
);

-- Song versions table
CREATE TABLE song_versions (
    id INTEGER PRIMARY KEY,
    song_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    lyrics TEXT NOT NULL,
    created_at TIMESTAMP,
    FOREIGN KEY (song_id) REFERENCES songs (id)
);

-- Generation sessions table
CREATE TABLE generation_sessions (
    id INTEGER PRIMARY KEY,
    song_id INTEGER NOT NULL,
    session_id TEXT UNIQUE NOT NULL,
    current_stage TEXT,
    progress_percentage INTEGER DEFAULT 0,
    stage_details TEXT, -- JSON
    logs TEXT, -- JSON
    error_log TEXT,
    started_at TIMESTAMP,
    updated_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (song_id) REFERENCES songs (id)
);

-- User settings table
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT, -- JSON
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### 2. Frontend Architecture (React)

#### 2.1 Component Hierarchy
```
App
├── Layout
│   ├── Header
│   ├── Navigation
│   └── Footer
├── Dashboard
│   ├── AlbumGrid
│   ├── QuickActions
│   └── RecentSongs
├── SongGeneration
│   ├── InputForm
│   ├── ProgressTracker
│   └── SettingsPanel
├── SongViewer
│   ├── LyricsDisplay
│   ├── MetadataPanel
│   ├── AlbumArt
│   └── ExportOptions
├── AlbumManager
│   ├── AlbumList
│   ├── SongLibrary
│   └── SearchFilters
├── Settings
│   ├── LLMConfig
│   ├── GenerationParams
│   └── UIPreferences
└── Shared
    ├── FileUpload
    ├── ProgressBar
    ├── ToastNotifications
    └── ModalDialogs
```

#### 2.2 State Management
- **Global State**: React Query cache plus route-driven page state
- **Component State**: Form data, UI preferences, loading states
- **Server State**: Songs, albums, personas, styles, instruments, and settings (React Query)

### 3. Real-time Features

#### 3.1 WebSocket Implementation
- Connection management and reconnection
- Progress event handling
- Error handling and recovery

#### 3.2 Progress Tracking
- Stage-based progress indication
- Detailed logs and status messages
- Time estimation algorithms
- Cancellation capability

## User Experience Design

### 1. Design Principles
- **Simplicity**: Clean, uncluttered interface
- **Feedback**: Clear progress indication and status updates
- **Consistency**: Uniform design patterns and behaviors
- **Accessibility**: Support for screen readers and keyboard navigation

### 2. Visual Design
- **Color Scheme**: Dark theme with accent colors
- **Typography**: Modern, readable fonts
- **Layout**: Grid-based responsive design
- **Icons**: Consistent icon system (Heroicons/Lucide)
- **Animations**: Subtle transitions and micro-interactions

### 3. Workflow Design
- **Guided Generation**: Step-by-step wizard for new users
- **Quick Generation**: Streamlined process for experienced users
- **Batch Operations**: Handle multiple songs efficiently
- **Error Recovery**: Clear error messages with recovery options

## Implementation Phases

### Phase 1: Core Infrastructure
- Backend API setup
- Database schema implementation
- Basic React app structure
- Shared backend generation flow for web and CLI

### Phase 2: Song Generation
- Input form and validation
- Song generation pipeline integration
- Progress tracking implementation
- Basic results display

### Phase 3: Album Management
- Album dashboard
- Song library and organization
- File management system
- Export functionality

### Phase 4: Advanced Features
- Settings and configuration
- Persona and style management
- Album art generation interface
- Real-time notifications

### Phase 5: Polish and Optimization
- UI/UX refinements
- Performance optimization
- Mobile responsiveness
- Testing and deployment

## Success Metrics
- User adoption and engagement
- Song generation success rate
- User satisfaction scores
- Performance benchmarks
- Error rates and recovery

## Future Enhancements
- Collaborative song editing
- Advanced analytics and insights
- Integration with music platforms
- Mobile app development
- AI model fine-tuning interface
