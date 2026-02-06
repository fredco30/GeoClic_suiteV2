"""
Router pour la gestion des utilisateurs.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel, Field
import bcrypt

from database import get_db
from routers.auth import get_current_user
from schemas.auth import UserRole

router = APIRouter()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


class UserCreateAdmin(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    nom: str = Field(..., min_length=1)
    prenom: str = ""
    role: UserRole = UserRole.contributor


class UserUpdateAdmin(BaseModel):
    nom: Optional[str] = Field(None, alias="name")
    prenom: Optional[str] = None
    role: Optional[UserRole] = None
    actif: Optional[bool] = Field(None, alias="is_active")


class UserPermissions(BaseModel):
    projets: List[str] = []
    categories: List[str] = []


class UserResponse(BaseModel):
    id: str
    email: str
    nom: str
    prenom: str
    role: str
    actif: bool
    permissions: Optional[UserPermissions] = None
    created_at: str
    last_login: Optional[str] = None


@router.get("", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Liste tous les utilisateurs (admin seulement)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    result = await db.execute(
        text("""
            SELECT id, email, name, role, is_active,
                   permissions, created_at, last_login
            FROM users
            ORDER BY created_at DESC
        """)
    )
    rows = result.mappings().all()

    return [
        UserResponse(
            id=str(row["id"]),
            email=row["email"],
            nom=row["name"] or "",
            prenom="",  # À ajouter dans la table si nécessaire
            role=row["role"],
            actif=row["is_active"],
            permissions=UserPermissions(**row["permissions"]) if row["permissions"] else None,
            created_at=row["created_at"].isoformat() if row["created_at"] else "",
            last_login=row["last_login"].isoformat() if row["last_login"] else None,
        )
        for row in rows
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère un utilisateur par son ID."""
    is_admin = current_user.get("is_super_admin") or current_user.get("role_data") == "admin"
    if not is_admin and str(current_user["id"]) != user_id:
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    result = await db.execute(
        text("""
            SELECT id, email, name, role, is_active,
                   permissions, created_at, last_login
            FROM users WHERE id = :id
        """),
        {"id": user_id},
    )
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    return UserResponse(
        id=str(row["id"]),
        email=row["email"],
        nom=row["name"] or "",
        prenom="",
        role=row["role"],
        actif=row["is_active"],
        permissions=UserPermissions(**row["permissions"]) if row["permissions"] else None,
        created_at=row["created_at"].isoformat() if row["created_at"] else "",
        last_login=row["last_login"].isoformat() if row["last_login"] else None,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateAdmin,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Crée un nouvel utilisateur (admin seulement)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    # Vérifier si l'email existe
    existing = await db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": user_data.email},
    )
    if existing.first():
        raise HTTPException(status_code=400, detail="Cet email existe déjà")

    password_hash = hash_password(user_data.password)

    # Combiner prénom et nom pour le champ name
    full_name = f"{user_data.prenom} {user_data.nom}".strip()

    result = await db.execute(
        text("""
            INSERT INTO users (email, password_hash, name, role, is_active)
            VALUES (:email, :password_hash, :name, :role, TRUE)
            RETURNING id, email, name, role, is_active, created_at
        """),
        {
            "email": user_data.email,
            "password_hash": password_hash,
            "name": full_name,
            "role": user_data.role.value,
        },
    )
    await db.commit()
    row = result.mappings().first()

    return UserResponse(
        id=str(row["id"]),
        email=row["email"],
        nom=row["name"] or "",
        prenom="",
        role=row["role"],
        actif=row["is_active"],
        permissions=None,
        created_at=row["created_at"].isoformat() if row["created_at"] else "",
        last_login=None,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    updates: UserUpdateAdmin,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Met à jour un utilisateur (admin seulement)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    update_data = updates.model_dump(exclude_unset=True, by_alias=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune modification")

    # Mapper les champs
    field_mapping = {
        "name": "name",
        "is_active": "is_active",
        "role": "role",
    }

    set_clauses = []
    params = {"id": user_id}
    for key, value in update_data.items():
        db_field = field_mapping.get(key, key)
        if key == "role" and value:
            value = value.value
        set_clauses.append(f"{db_field} = :{key}")
        params[key] = value

    if not set_clauses:
        raise HTTPException(status_code=400, detail="Aucune modification")

    result = await db.execute(
        text(f"""
            UPDATE users SET {', '.join(set_clauses)}
            WHERE id = :id
            RETURNING id, email, name, role, is_active, permissions, created_at, last_login
        """),
        params,
    )
    await db.commit()
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    return UserResponse(
        id=str(row["id"]),
        email=row["email"],
        nom=row["name"] or "",
        prenom="",
        role=row["role"],
        actif=row["is_active"],
        permissions=UserPermissions(**row["permissions"]) if row["permissions"] else None,
        created_at=row["created_at"].isoformat() if row["created_at"] else "",
        last_login=row["last_login"].isoformat() if row["last_login"] else None,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Supprime un utilisateur (admin seulement)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    # Ne pas se supprimer soi-même
    if str(current_user["id"]) == user_id:
        raise HTTPException(status_code=400, detail="Impossible de vous supprimer vous-même")

    result = await db.execute(
        text("DELETE FROM users WHERE id = :id RETURNING id"),
        {"id": user_id},
    )
    await db.commit()

    if not result.first():
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")


@router.put("/{user_id}/permissions", response_model=UserResponse)
async def update_user_permissions(
    user_id: str,
    permissions: UserPermissions,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Met à jour les permissions d'un utilisateur (admin seulement)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    import json
    permissions_json = json.dumps(permissions.model_dump())

    result = await db.execute(
        text("""
            UPDATE users SET permissions = CAST(:permissions AS jsonb)
            WHERE id = :id
            RETURNING id, email, name, role, is_active, permissions, created_at, last_login
        """),
        {"id": user_id, "permissions": permissions_json},
    )
    await db.commit()
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    return UserResponse(
        id=str(row["id"]),
        email=row["email"],
        nom=row["name"] or "",
        prenom="",
        role=row["role"],
        actif=row["is_active"],
        permissions=UserPermissions(**row["permissions"]) if row["permissions"] else None,
        created_at=row["created_at"].isoformat() if row["created_at"] else "",
        last_login=row["last_login"].isoformat() if row["last_login"] else None,
    )
