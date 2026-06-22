from backend.app.schemas.albums import AlbumArtGenerateRequest, AlbumCreate, AlbumRead, AlbumUpdate
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
from backend.app.schemas.settings import GenerationDefaults, ModelOption, SettingsResponse
from backend.app.schemas.songs import (
    DemoTrackStatus,
    GenerationLog,
    SongCreate,
    SongDetail,
    SongFileRead,
    SongLiveFeedbackDemoTrackRequest,
    SongRegenerateArtRequest,
    SongLyricsUpdate,
    SongRegenerateLyricsRequest,
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
    "AlbumArtGenerateRequest",
    "AlbumRead",
    "AlbumUpdate",
    "AuthMessageResponse",
    "AuthTokenResponse",
    "AuthUserRead",
    "BackupRestoreResult",
    "ChangePasswordRequest",
    "GenerationDefaults",
    "ModelOption",
    "LoginRequest",
    "SettingsResponse",
    "SignUpRequest",
    "DemoTrackStatus",
    "GenerationLog",
    "SongCreate",
    "SongDetail",
    "SongFileRead",
    "SongLiveFeedbackDemoTrackRequest",
    "SongRegenerateArtRequest",
    "SongLyricsUpdate",
    "SongRegenerateLyricsRequest",
    "SongRead",
    "SongStatus",
    "SongUpdate",
    "SongProposalGenerate",
    "SongProposalGenerateResponse",
    "SongProposalRead",
]
