"""
Schémas Pydantic pour les photos.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PhotoMetadata(BaseModel):
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
    gps_altitude: Optional[float] = None
    orientation: Optional[int] = None
    device_model: Optional[str] = None
    comment: Optional[str] = None


class PhotoUploadResponse(BaseModel):
    """Réponse après upload d'une photo."""
    success: bool
    photo: Optional[PhotoMetadata] = None
    error: Optional[str] = None
