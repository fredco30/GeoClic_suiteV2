"""
Schémas Pydantic pour l'API GéoClic V12 Pro.
"""

from .point import (
    PointBase,
    PointCreate,
    PointUpdate,
    PointResponse,
    PointListResponse,
    SyncStatus,
    GeometryType,
)
from .lexique import (
    LexiqueBase,
    LexiqueCreate,
    LexiqueResponse,
    LexiqueTreeResponse,
)
from .project import (
    ProjectBase,
    ProjectCreate,
    ProjectResponse,
)
from .auth import (
    UserCreate,
    UserResponse,
    Token,
    TokenData,
)
from .sync import (
    SyncRequest,
    SyncResponse,
)
from .photo import (
    PhotoMetadata,
    PhotoUploadResponse,
)
