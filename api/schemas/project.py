"""
Schémas Pydantic pour les Projets.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


class ProjectBase(BaseModel):
    """Schéma de base pour un projet."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = "En cours"
    is_active: bool = True
    collectivite_name: Optional[str] = None
    collectivite_address: Optional[str] = None
    responsable_name: Optional[str] = None
    responsable_email: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    metadata: Optional[dict] = None


class ProjectCreate(ProjectBase):
    """Schéma pour créer un projet."""
    pass


class ProjectUpdate(BaseModel):
    """Schéma pour mettre à jour un projet."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    collectivite_name: Optional[str] = None
    responsable_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectResponse(ProjectBase):
    """Schéma de réponse pour un projet."""
    id: str
    is_system: bool = False
    point_count: Optional[int] = 0
    min_lat: Optional[float] = None
    max_lat: Optional[float] = None
    min_lng: Optional[float] = None
    max_lng: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
