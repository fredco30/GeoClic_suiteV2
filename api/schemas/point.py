"""
Schémas Pydantic pour les Points géographiques.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class SyncStatus(str, Enum):
    """Statuts de synchronisation."""
    draft = "draft"
    pending = "pending"
    validated = "validated"
    rejected = "rejected"
    published = "published"
    syncing = "syncing"
    error = "error"


class GeometryType(str, Enum):
    """Types de géométrie."""
    point = "POINT"
    line = "LINESTRING"
    polygon = "POLYGON"


class PhotoMetadataSchema(BaseModel):
    """Métadonnées d'une photo."""
    id: str
    url: str
    thumbnail_url: Optional[str] = None
    filename: str
    size_bytes: Optional[int] = None
    taken_at: Optional[datetime] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    gps_accuracy: Optional[float] = None
    device_model: Optional[str] = None
    comment: Optional[str] = None


class CoordinateSchema(BaseModel):
    """Coordonnée GPS."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class PointBase(BaseModel):
    """Schéma de base pour un point."""
    name: str = Field(..., min_length=1, max_length=255)
    lexique_code: Optional[str] = None
    type: str = Field(..., min_length=1, max_length=100)
    subtype: Optional[str] = None
    geom_type: GeometryType = GeometryType.point
    coordinates: List[CoordinateSchema]
    gps_precision: Optional[float] = None
    gps_source: Optional[str] = None
    altitude: Optional[float] = None
    condition_state: Optional[str] = "Neuf"
    point_status: Optional[str] = "Projet"
    comment: Optional[str] = None

    # Attributs techniques
    materiau: Optional[str] = None
    hauteur: Optional[float] = None
    largeur: Optional[float] = None
    date_installation: Optional[datetime] = None
    duree_vie_annees: Optional[int] = None
    marque_modele: Optional[str] = None

    # Maintenance
    date_derniere_intervention: Optional[datetime] = None
    date_prochaine_intervention: Optional[datetime] = None
    priorite: Optional[str] = None
    cout_remplacement: Optional[float] = None

    # Propriétés dynamiques
    custom_properties: Optional[dict] = None

    # Affichage
    color_value: Optional[int] = None
    icon_name: Optional[str] = None


class PointCreate(PointBase):
    """Schéma pour créer un point."""
    project_id: Optional[str] = None
    photos: Optional[List[PhotoMetadataSchema]] = []


class PointUpdate(BaseModel):
    """Schéma pour mettre à jour un point."""
    name: Optional[str] = None
    lexique_code: Optional[str] = None
    type: Optional[str] = None
    subtype: Optional[str] = None
    coordinates: Optional[List[CoordinateSchema]] = None
    condition_state: Optional[str] = None
    point_status: Optional[str] = None
    sync_status: Optional[SyncStatus] = None
    rejection_comment: Optional[str] = None
    comment: Optional[str] = None
    materiau: Optional[str] = None
    hauteur: Optional[float] = None
    largeur: Optional[float] = None
    priorite: Optional[str] = None
    custom_properties: Optional[dict] = None
    photos: Optional[List[PhotoMetadataSchema]] = None


class PointResponse(PointBase):
    """Schéma de réponse pour un point."""
    id: str
    project_id: Optional[str] = None
    sync_status: SyncStatus = SyncStatus.draft
    rejection_comment: Optional[str] = None
    zone_name: Optional[str] = None
    photos: List[PhotoMetadataSchema] = []
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PointListResponse(BaseModel):
    """Réponse paginée pour liste de points."""
    total: int
    page: int
    page_size: int
    items: List[PointResponse]
