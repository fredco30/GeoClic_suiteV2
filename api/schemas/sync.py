"""
Schémas Pydantic pour la synchronisation.
"""

from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

from .point import PointCreate, PointResponse, PointUpdate


class SyncRequest(BaseModel):
    """Requête de synchronisation depuis Mobile."""
    device_id: str
    last_sync_at: Optional[datetime] = None
    points_to_upload: List[PointCreate] = []
    points_to_update: List[dict] = []  # {id: str, ...changes}
    points_to_delete: List[str] = []
    # Options pour la sync
    include_lexique: bool = False
    include_projects: bool = False
    include_champs: bool = False
    lexique_version: Optional[str] = None  # Hash MD5 du lexique local
    project_id: Optional[str] = None  # Filtrer lexique/champs par projet


class LexiqueEntrySync(BaseModel):
    """Entrée lexique pour synchronisation."""
    code: str
    label: str
    parent_code: Optional[str] = None
    level: int = 0
    icon_name: Optional[str] = None
    color_value: Optional[Any] = None  # int en DB, converti en string hex pour le mobile
    display_order: int = 0
    is_active: bool = True
    project_id: Optional[str] = None  # ID du projet pour isolation


class ChampDynamiqueSync(BaseModel):
    """Champ dynamique pour synchronisation."""
    id: str
    lexique_code: str
    nom: str
    type: str
    obligatoire: bool = False
    ordre: int = 0
    options: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    formule: Optional[str] = None
    actif: bool = True
    project_id: Optional[str] = None  # ID du projet pour isolation
    # Champs conditionnels
    condition_field: Optional[str] = None
    condition_operator: Optional[str] = None
    condition_value: Optional[str] = None


class ProjectSync(BaseModel):
    """Projet pour synchronisation."""
    id: str
    name: str
    description: Optional[str] = None
    collectivite: Optional[str] = None
    collectivite_name: Optional[str] = None
    status: Optional[str] = None
    is_active: bool = True


class SyncResponse(BaseModel):
    """Réponse de synchronisation."""
    success: bool
    sync_id: int
    server_time: datetime
    points_uploaded: int = 0
    points_updated: int = 0
    points_deleted: int = 0
    points_to_download: List[PointResponse] = []
    # Données pour offline
    lexique_updated: bool = False
    lexique_version: Optional[str] = None
    lexique_entries: List[LexiqueEntrySync] = []
    champs_dynamiques: List[ChampDynamiqueSync] = []
    projects: List[ProjectSync] = []
    errors: List[str] = []


class SyncStatusResponse(BaseModel):
    """Statut de synchronisation."""
    last_sync_at: Optional[datetime] = None
    pending_uploads: int = 0
    pending_downloads: int = 0
    server_version: str = "1.0.0"
    lexique_version: Optional[str] = None
    lexique_count: int = 0
    projects_count: int = 0


class OfflinePackageResponse(BaseModel):
    """Package complet pour mode offline."""
    server_time: datetime
    lexique_version: str
    lexique_entries: List[LexiqueEntrySync]
    champs_dynamiques: List[ChampDynamiqueSync]
    projects: List[ProjectSync]
    user_permissions: Dict[str, Any]
