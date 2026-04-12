from backend.app.schemas.albums import AlbumCreate, AlbumRead
from backend.app.schemas.auth import (
    AuthMessageResponse,
    AuthTokenResponse,
    AuthUserRead,
    ChangePasswordRequest,
    LoginRequest,
    SignUpRequest,
)
from backend.app.schemas.backups import BackupRestoreResult
from backend.app.schemas.personas import Persona, PersonaCreate, PersonaUpdate
from backend.app.schemas.settings import GenerationDefaults, SettingsResponse
from backend.app.schemas.songs import (
    DemoTrackStatus,
    GenerationLog,
    SongCreate,
    SongDetail,
    SongFileRead,
    SongLyricsUpdate,
    SongRead,
    SongStatus,
    SongUpdate,
)
from backend.app.schemas.song_proposals import (
    SongProposalGenerate,
    SongProposalGenerateResponse,
    SongProposalRead,
)

__all__ = [
    "Persona",
    "PersonaCreate",
    "PersonaUpdate",
    "AlbumCreate",
    "AlbumRead",
    "AuthMessageResponse",
    "AuthTokenResponse",
    "AuthUserRead",
    "BackupRestoreResult",
    "ChangePasswordRequest",
    "GenerationDefaults",
    "LoginRequest",
    "SettingsResponse",
    "SignUpRequest",
    "DemoTrackStatus",
    "GenerationLog",
    "SongCreate",
    "SongDetail",
    "SongFileRead",
    "SongLyricsUpdate",
    "SongRead",
    "SongStatus",
    "SongUpdate",
    "SongProposalGenerate",
    "SongProposalGenerateResponse",
    "SongProposalRead",
]
