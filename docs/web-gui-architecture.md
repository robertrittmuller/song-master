# Song Master Web GUI - Technical Architecture

## System Overview

The Song Master Web GUI is a full-stack web application that transforms the CLI tool into a modern, user-friendly web interface. The architecture follows a client-server pattern with real-time capabilities for progress tracking.

## Technology Stack

### Backend Stack
- **Framework**: FastAPI (Python)
  - High performance async framework
  - Automatic API documentation
  - Built-in validation and serialization
  - WebSocket support
- **Database**: SQLite with SQLAlchemy ORM
  - Simple deployment and maintenance
  - ACID compliance for data integrity
  - JSON support for metadata storage
- **Authentication**: JWT tokens with FastAPI security
- **File Storage**: Local filesystem with organized directory structure
- **Real-time**: WebSockets for progress updates
- **Background Tasks**: Celery with Redis for long-running operations

### Frontend Stack
- **Framework**: React 18 with TypeScript
  - Component-based architecture
  - Type safety and better developer experience
  - Large ecosystem and community support
- **Build Tool**: Vite
  - Fast development server and hot reload
  - Optimized production builds
  - Modern ES modules support
- **Styling**: Tailwind CSS + Headless UI
  - Utility-first CSS framework
  - Rapid prototyping and consistent design
  - Accessible component primitives
- **State Management**: React Query + Zustand
  - Server state synchronization
  - Client-side state management
  - Caching and background updates
- **Real-time**: Socket.io-client
  - Reliable WebSocket communication
  - Automatic reconnection
  - Event-based architecture

### Development Tools
- **Package Manager**: pnpm (faster, disk efficient)
- **Code Quality**: ESLint + Prettier + TypeScript
- **Testing**: Vitest + React Testing Library + Playwright
- **API Documentation**: OpenAPI/Swagger (auto-generated)

## Architecture Patterns

### 1. Backend Architecture

#### Layered Architecture
```
┌─────────────────────────────────────┐
│           Presentation Layer         │  ← FastAPI Routes & WebSockets
├─────────────────────────────────────┤
│            Business Logic           │  ← Service Layer & CLI Integration
├─────────────────────────────────────┤
│            Data Access              │  ← SQLAlchemy Models & Repositories
├─────────────────────────────────────┤
│            Infrastructure           │  ← Database, File System, External APIs
└─────────────────────────────────────┘
```

#### Core Components

**1. API Layer (FastAPI Routes)**
```python
# Main application structure
app/
├── main.py                 # FastAPI app initialization
├── api/
│   ├── __init__.py
│   ├── deps.py            # Dependencies and authentication
│   ├── songs.py           # Song-related endpoints
│   ├── projects.py        # Project management endpoints
│   ├── personas.py        # Persona management
│   ├── styles.py          # Style and tag endpoints
│   ├── settings.py        # User settings endpoints
│   └── websocket.py       # WebSocket handlers
├── core/
│   ├── config.py          # Application configuration
│   ├── security.py        # Authentication & authorization
│   └── database.py        # Database connection
├── models/
│   ├── __init__.py
│   ├── song.py            # Song data models
│   ├── project.py         # Project models
│   └── user.py            # User models
├── schemas/
│   ├── __init__.py
│   ├── song.py            # Pydantic schemas for API
│   └── project.py
├── services/
│   ├── __init__.py
│   ├── song_generator.py  # CLI integration service
│   ├── file_manager.py    # File operations
│   └── progress_tracker.py # Real-time progress
└── utils/
    ├── cli_wrapper.py     # CLI tool integration
    └── file_utils.py      # File handling utilities
```

**2. Service Layer**
- **SongGeneratorService**: Orchestrates the CLI song generation process
- **ProgressTrackerService**: Manages real-time progress updates
- **FileManagerService**: Handles file operations and storage
- **PersonaService**: Manages persona loading and application
- **SettingsService**: User configuration management

**3. Data Layer**
- **SQLAlchemy Models**: Database entity definitions
- **Repository Pattern**: Data access abstraction
- **Migration System**: Database schema evolution

### 2. Frontend Architecture

#### Component Architecture
```
┌─────────────────────────────────────┐
│              App                    │
├─────────────────────────────────────┤
│           Layout Components         │
├─────────────────────────────────────┤
│         Feature Components          │
├─────────────────────────────────────┤
│          Shared Components          │
├─────────────────────────────────────┤
│           Hooks & Utils             │
└─────────────────────────────────────┘
```

#### Directory Structure
```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Reusable UI components
│   │   ├── layout/          # Layout components
│   │   ├── features/        # Feature-specific components
│   │   └── shared/          # Shared components
│   ├── pages/               # Page components
│   ├── hooks/               # Custom React hooks
│   ├── services/            # API client services
│   ├── stores/              # State management
│   ├── types/               # TypeScript type definitions
│   ├── utils/               # Utility functions
│   └── styles/              # Global styles and Tailwind config
├── public/                  # Static assets
└── tests/                   # Test files
```

#### State Management Strategy

**1. Server State (React Query)**
- Songs, projects, personas data
- Caching and background updates
- Optimistic updates
- Error handling and retry logic

**2. Client State (Zustand)**
- UI state (modals, notifications)
- User preferences
- Form data
- Real-time connection status

**3. Component State**
- Local component state
- Form state management
- Loading and error states

### 3. Real-time Communication

#### WebSocket Architecture
```
Client ←→ WebSocket Server ←→ Background Tasks
   ↓           ↓                    ↓
React App ←→ FastAPI ←→ Song Generation Pipeline
```

#### Event Types
- **progress**: Stage updates with percentage and status
- **log**: Detailed logging information
- **error**: Error notifications with recovery options
- **complete**: Generation completion with results
- **notification**: System-wide notifications

### 4. Database Design

#### Entity Relationship Model
```
Users (1) ←→ (M) Projects (1) ←→ (M) Songs (1) ←→ (M) SongFiles
    ↓              ↓              ↓              ↓
Settings        Metadata       Lyrics         Album Art
```

#### Core Tables

**1. Users Table**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**2. Projects Table**
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    settings JSON, -- Project-specific settings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

**3. Songs Table**
```sql
CREATE TABLE songs (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    user_prompt TEXT NOT NULL,
    persona TEXT,
    use_local BOOLEAN DEFAULT FALSE,
    lyrics TEXT,
    metadata JSON, -- AI-generated metadata
    score REAL,
    status TEXT DEFAULT 'pending', -- pending, generating, completed, failed
    generation_config JSON, -- Generation parameters
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (id)
);
```

**4. SongFiles Table**
```sql
CREATE TABLE song_files (
    id INTEGER PRIMARY KEY,
    song_id INTEGER NOT NULL,
    file_type TEXT NOT NULL, -- 'lyrics', 'metadata', 'artwork', 'audio'
    file_path TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (song_id) REFERENCES songs (id)
);
```

**5. UserSettings Table**
```sql
CREATE TABLE user_settings (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE(user_id, key)
);
```

### 5. File Storage Strategy

#### Directory Structure
```
storage/
├── users/
│   └── {user_id}/
│       ├── projects/
│       │   └── {project_id}/
│       │       ├── songs/
│       │       │   └── {song_id}/
│       │       │       ├── lyrics.md
│       │       │       ├── metadata.json
│       │       │       ├── artwork.jpg
│       │       │       └── audio.mp3 (future)
│       │       └── exports/
│       └── temp/
└── system/
    ├── personas/
    ├── styles/
    └── templates/
```

#### File Management
- **Naming Convention**: UUID-based filenames for uniqueness
- **Metadata Storage**: JSON files alongside content files
- **Cleanup Strategy**: Automatic cleanup of temporary files
- **Backup System**: Regular backups of user data

### 6. Security Architecture

#### Authentication & Authorization
- **JWT Tokens**: Stateless authentication
- **Password Security**: bcrypt hashing with salt
- **Session Management**: Secure token storage and refresh
- **API Security**: Rate limiting and input validation

#### Data Protection
- **Input Validation**: Pydantic schemas for all inputs
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **XSS Protection**: Content sanitization and CSP headers
- **File Upload Security**: Type validation and size limits

#### API Security
```python
# Security middleware
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

### 7. Performance Optimization

#### Backend Optimizations
- **Async/Await**: Non-blocking I/O operations
- **Connection Pooling**: Database connection management
- **Caching**: Redis for frequently accessed data
- **Background Tasks**: Celery for long-running operations
- **File Streaming**: Efficient large file handling

#### Frontend Optimizations
- **Code Splitting**: Route-based and component-based splitting
- **Lazy Loading**: Dynamic imports for non-critical components
- **Image Optimization**: WebP format with fallbacks
- **Bundle Optimization**: Tree shaking and minification
- **Caching Strategy**: Service worker for offline capability

#### Database Optimizations
- **Indexing**: Strategic indexes on frequently queried columns
- **Query Optimization**: Efficient SQLAlchemy queries
- **Pagination**: Limit-offset for large datasets
- **Connection Pooling**: Reuse database connections

### 8. Deployment Architecture

#### Development Environment
```
┌─────────────────────────────────────┐
│              Docker Compose         │
├─────────────────────────────────────┤
│  Frontend (Vite Dev Server)         │
│  Backend (FastAPI)                  │
│  Database (SQLite)                  │
│  Redis (Cache & Queue)              │
│  Celery Worker                      │
└─────────────────────────────────────┘
```

#### Production Environment
```
┌─────────────────────────────────────┐
│              Load Balancer          │
├─────────────────────────────────────┤
│  Frontend (Nginx + Static Files)    │
├─────────────────────────────────────┤
│  Backend (Gunicorn + FastAPI)       │
├─────────────────────────────────────┤
│  Database (PostgreSQL)              │
├─────────────────────────────────────┤
│  Cache (Redis)                      │
├─────────────────────────────────────┤
│  Queue (Redis + Celery)             │
└─────────────────────────────────────┘
```

#### Container Configuration
```dockerfile
# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 9. Monitoring & Observability

#### Application Monitoring
- **Logging**: Structured logging with correlation IDs
- **Metrics**: Performance and business metrics
- **Health Checks**: Application and dependency health
- **Error Tracking**: Centralized error reporting

#### Performance Monitoring
- **Response Times**: API endpoint performance
- **Database Performance**: Query execution times
- **Memory Usage**: Application memory consumption
- **Background Tasks**: Queue processing metrics

### 10. Development Workflow

#### Code Organization
- **Feature Branches**: Git flow for feature development
- **Code Review**: Pull request review process
- **Testing**: Automated testing in CI/CD pipeline
- **Documentation**: API documentation and code comments

#### Quality Assurance
- **Type Safety**: TypeScript and Python type hints
- **Linting**: ESLint and Pylint for code quality
- **Testing**: Unit, integration, and E2E tests
- **Security Scanning**: Dependency vulnerability scanning

## Integration with CLI Tool

### CLI Wrapper Service
The web application integrates with the existing CLI tool through a dedicated service layer:

```python
class SongGeneratorService:
    def __init__(self):
        self.cli_path = Path(__file__).parent.parent.parent / "song_master.py"
    
    async def generate_song(
        self, 
        user_input: str, 
        song_name: Optional[str] = None,
        persona: Optional[str] = None,
        use_local: bool = False,
        progress_callback: Optional[Callable] = None
    ) -> SongResult:
        # Convert web parameters to CLI arguments
        # Execute CLI tool as subprocess
        # Stream output for progress updates
        # Parse results and return structured data
```

### Progress Tracking Integration
- **Subprocess Monitoring**: Real-time output capture from CLI
- **Stage Detection**: Parse CLI output to identify generation stages
- **Progress Calculation**: Map CLI stages to web progress percentages
- **Error Handling**: Capture and categorize CLI errors

## Scalability Considerations

### Horizontal Scaling
- **Stateless Design**: No server-side session storage
- **Database Scaling**: Read replicas for query distribution
- **Background Processing**: Distributed task queue
- **File Storage**: Cloud storage for large files

### Performance Scaling
- **Caching Layers**: Multiple levels of caching
- **Database Optimization**: Query optimization and indexing
- **CDN Integration**: Static asset delivery optimization
- **Load Balancing**: Traffic distribution across instances

This architecture provides a solid foundation for building a scalable, maintainable, and user-friendly web interface for the Song Master CLI tool.