"""
Schémas Pydantic pour l'authentification.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """Rôles utilisateur."""
    admin = "admin"
    moderator = "moderator"
    contributor = "contributor"
    viewer = "viewer"


class UserPermissions(BaseModel):
    """Permissions utilisateur pour projets et catégories."""
    projets: List[str] = []  # IDs des projets accessibles
    categories: List[str] = []  # Codes des catégories accessibles


class UserBase(BaseModel):
    """Schéma de base pour un utilisateur."""
    email: str = Field(..., min_length=5)  # Utilise str au lieu de EmailStr pour accepter .local
    name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Schéma pour créer un utilisateur."""
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.contributor


class UserUpdate(BaseModel):
    """Schéma pour mettre à jour un utilisateur."""
    name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schéma de réponse pour un utilisateur."""
    id: str
    role: UserRole
    is_active: bool
    permissions: Optional[UserPermissions] = None
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token JWT."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    """Données extraites du token."""
    user_id: str
    email: str
    role: UserRole


class LoginRequest(BaseModel):
    """Requête de connexion."""
    email: str
    password: str
