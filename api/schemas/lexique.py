"""
Schémas Pydantic pour le Lexique (menus en cascade).
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class LexiqueBase(BaseModel):
    """Schéma de base pour une entrée Lexique."""
    code: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=255)
    parent_code: Optional[str] = None
    project_id: Optional[str] = None
    level: int = 0
    display_order: int = 0
    triggers_form: bool = False
    form_type_ref: Optional[str] = None
    icon_name: Optional[str] = None
    color_value: Optional[int] = None
    is_active: bool = True
    metadata: Optional[dict] = None


class LexiqueCreate(LexiqueBase):
    """Schéma pour créer une entrée Lexique."""
    project_id: str = Field(..., description="ID du projet auquel appartient cette entrée")


class LexiqueUpdate(BaseModel):
    """Schéma pour mettre à jour une entrée Lexique."""
    label: Optional[str] = None
    parent_code: Optional[str] = None
    display_order: Optional[int] = None
    triggers_form: Optional[bool] = None
    form_type_ref: Optional[str] = None
    icon_name: Optional[str] = None
    color_value: Optional[int] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


class LexiqueResponse(LexiqueBase):
    """Schéma de réponse pour une entrée Lexique."""
    id: int
    created_at: datetime
    full_path: Optional[str] = None  # Chemin complet "A > B > C"

    class Config:
        from_attributes = True


class LexiqueChildResponse(BaseModel):
    """Réponse pour un enfant dans l'arbre."""
    code: str
    label: str
    level: int
    triggers_form: bool
    icon_name: Optional[str] = None
    color_value: Optional[int] = None
    has_children: bool = False


class LexiqueTreeResponse(BaseModel):
    """Réponse pour l'arbre Lexique complet."""
    roots: List[LexiqueResponse]
    total_entries: int
    max_depth: int
