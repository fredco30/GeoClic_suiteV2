"""
Router d'authentification unifiée - GéoClic Suite
Gère l'authentification et la gestion des utilisateurs pour toutes les applications.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from jose import JWTError, jwt

from database import get_db
from config import settings

router = APIRouter(tags=["Authentification"])

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class UserBase(BaseModel):
    email: EmailStr
    nom: str
    prenom: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role_data: str = "aucun"
    role_demandes: str = "aucun"
    role_sig: str = "aucun"
    role_terrain: str = "aucun"
    service_id: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    password: Optional[str] = None
    actif: Optional[bool] = None
    role_data: Optional[str] = None
    role_demandes: Optional[str] = None
    role_sig: Optional[str] = None
    role_terrain: Optional[str] = None
    service_id: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    nom: str
    prenom: str
    actif: bool
    is_super_admin: bool
    role_data: str
    role_demandes: str
    role_sig: str
    role_terrain: str
    service_id: Optional[str] = None
    service_nom: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class SuperAdminUpdate(BaseModel):
    """Pour changer le super admin depuis l'interface."""
    email: EmailStr
    password: str = Field(..., min_length=6)
    nom: str
    prenom: str


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe contre son hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Génère un hash bcrypt pour un mot de passe."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un token JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Récupère l'utilisateur courant depuis le token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(text("""
        SELECT u.id, u.email, u.nom, u.prenom, u.actif,
               u.is_super_admin, u.role_data, u.role_demandes, u.role_sig, u.role_terrain,
               u.service_id, s.nom AS service_nom
        FROM geoclic_users u
        LEFT JOIN demandes_services s ON u.service_id = s.id
        WHERE u.id = CAST(:id AS uuid) AND u.actif = TRUE
    """), {"id": user_id})

    user = result.fetchone()
    if user is None:
        raise credentials_exception

    return {
        "id": str(user.id),
        "email": user.email,
        "nom": user.nom,
        "prenom": user.prenom,
        "is_super_admin": user.is_super_admin,
        "role_data": user.role_data,
        "role_demandes": user.role_demandes,
        "role_sig": user.role_sig,
        "role_terrain": user.role_terrain,
        "service_id": str(user.service_id) if user.service_id else None,
        "service_nom": user.service_nom,
    }


async def get_current_user_optional(
    token: str = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db)
) -> Optional[dict]:
    """Récupère l'utilisateur courant si un token est fourni, sinon None."""
    if token is None:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None


def require_role(allowed_roles: List[str], role_field: str):
    """Crée une dépendance pour vérifier les rôles."""
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("is_super_admin"):
            return current_user

        user_role = current_user.get(role_field, "aucun")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé. Rôle requis: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


# Dépendances de rôle pré-configurées
def get_require_data_admin():
    return require_role(["admin"], "role_data")

def get_require_demandes_access():
    return require_role(["agent", "admin"], "role_demandes")

def get_require_demandes_admin():
    return require_role(["admin"], "role_demandes")

def get_require_sig_access():
    return require_role(["lecture", "edition"], "role_sig")

def get_require_sig_edition():
    return require_role(["edition"], "role_sig")

def get_require_terrain_access():
    return require_role(["agent"], "role_terrain")


# ═══════════════════════════════════════════════════════════════════════════════
# RATE LIMITING - Protection anti brute-force
# ═══════════════════════════════════════════════════════════════════════════════

from collections import defaultdict
import threading

# Stockage en mémoire des tentatives échouées: email -> [timestamps]
_failed_attempts: dict[str, list[datetime]] = defaultdict(list)
_failed_lock = threading.Lock()

# Configuration
RATE_LIMIT_MAX_ATTEMPTS = 5    # Max tentatives échouées
RATE_LIMIT_WINDOW_SECONDS = 60  # Fenêtre de 1 minute


def _check_rate_limit(email: str) -> bool:
    """Vérifie si l'email n'a pas dépassé le nombre de tentatives autorisées."""
    now = datetime.utcnow()
    cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW_SECONDS)
    with _failed_lock:
        # Nettoyer les anciennes tentatives
        _failed_attempts[email] = [ts for ts in _failed_attempts[email] if ts > cutoff]
        return len(_failed_attempts[email]) < RATE_LIMIT_MAX_ATTEMPTS


def _record_failed_attempt(email: str):
    """Enregistre une tentative échouée."""
    with _failed_lock:
        _failed_attempts[email].append(datetime.utcnow())


def _clear_failed_attempts(email: str):
    """Efface les tentatives échouées après une connexion réussie."""
    with _failed_lock:
        _failed_attempts.pop(email, None)


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS AUTHENTIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Authentification utilisateur.
    Retourne un token JWT et les informations utilisateur.
    Rate-limité à 5 tentatives échouées par minute par email.
    """
    email = form_data.username

    # Vérifier le rate limit
    if not _check_rate_limit(email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives de connexion. Réessayez dans une minute.",
        )

    result = await db.execute(text("""
        SELECT u.id, u.email, u.password_hash, u.nom, u.prenom, u.actif,
               u.is_super_admin, u.role_data, u.role_demandes, u.role_sig, u.role_terrain,
               u.service_id, s.nom AS service_nom, u.created_at
        FROM geoclic_users u
        LEFT JOIN demandes_services s ON u.service_id = s.id
        WHERE u.email = :email
    """), {"email": email})

    user = result.fetchone()

    if not user:
        _record_failed_attempt(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    if not user.actif:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte désactivé",
        )

    if not verify_password(form_data.password, user.password_hash):
        _record_failed_attempt(email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    # Connexion réussie - effacer les tentatives échouées
    _clear_failed_attempts(email)

    # Mettre à jour last_login
    await db.execute(text("""
        UPDATE geoclic_users SET last_login = CURRENT_TIMESTAMP WHERE id = :id
    """), {"id": str(user.id)})
    await db.commit()

    # Créer le token
    access_token = create_access_token(data={
        "sub": str(user.id),
        "email": user.email,
        "is_super_admin": user.is_super_admin,
        "role_data": user.role_data,
        "role_demandes": user.role_demandes,
        "role_sig": user.role_sig,
        "role_terrain": user.role_terrain,
    })

    return Token(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            nom=user.nom,
            prenom=user.prenom,
            actif=user.actif,
            is_super_admin=user.is_super_admin,
            role_data=user.role_data,
            role_demandes=user.role_demandes,
            role_sig=user.role_sig,
            role_terrain=user.role_terrain,
            service_id=str(user.service_id) if user.service_id else None,
            service_nom=user.service_nom,
            created_at=user.created_at,
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retourne les informations de l'utilisateur connecté."""
    result = await db.execute(text("""
        SELECT u.id, u.email, u.nom, u.prenom, u.actif,
               u.is_super_admin, u.role_data, u.role_demandes, u.role_sig, u.role_terrain,
               u.service_id, s.nom AS service_nom, u.last_login, u.created_at
        FROM geoclic_users u
        LEFT JOIN demandes_services s ON u.service_id = s.id
        WHERE u.id = CAST(:id AS uuid)
    """), {"id": current_user["id"]})

    user = result.fetchone()

    return UserResponse(
        id=str(user.id),
        email=user.email,
        nom=user.nom,
        prenom=user.prenom,
        actif=user.actif,
        is_super_admin=user.is_super_admin,
        role_data=user.role_data,
        role_demandes=user.role_demandes,
        role_sig=user.role_sig,
        role_terrain=user.role_terrain,
        service_id=str(user.service_id) if user.service_id else None,
        service_nom=user.service_nom,
        last_login=user.last_login,
        created_at=user.created_at,
    )


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change le mot de passe de l'utilisateur connecté."""
    # Vérifier l'ancien mot de passe
    result = await db.execute(text("""
        SELECT password_hash FROM geoclic_users WHERE id = CAST(:id AS uuid)
    """), {"id": current_user["id"]})
    user = result.fetchone()

    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect"
        )

    # Mettre à jour
    new_hash = get_password_hash(data.new_password)
    await db.execute(text("""
        UPDATE geoclic_users SET password_hash = :hash WHERE id = CAST(:id AS uuid)
    """), {"hash": new_hash, "id": current_user["id"]})
    await db.commit()

    return {"message": "Mot de passe modifié avec succès"}


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS GESTION UTILISATEURS (Admin only)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Liste tous les utilisateurs (admin data ou super admin uniquement)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")

    result = await db.execute(text("""
        SELECT u.id, u.email, u.nom, u.prenom, u.actif,
               u.is_super_admin, u.role_data, u.role_demandes, u.role_sig, u.role_terrain,
               u.service_id, s.nom AS service_nom, u.last_login, u.created_at
        FROM geoclic_users u
        LEFT JOIN demandes_services s ON u.service_id = s.id
        ORDER BY u.is_super_admin DESC, u.nom, u.prenom
    """))

    users = []
    for row in result.fetchall():
        users.append(UserResponse(
            id=str(row.id),
            email=row.email,
            nom=row.nom,
            prenom=row.prenom,
            actif=row.actif,
            is_super_admin=row.is_super_admin,
            role_data=row.role_data,
            role_demandes=row.role_demandes,
            role_sig=row.role_sig,
            role_terrain=row.role_terrain,
            service_id=str(row.service_id) if row.service_id else None,
            service_nom=row.service_nom,
            last_login=row.last_login,
            created_at=row.created_at,
        ))

    return users


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Crée un nouvel utilisateur (admin data ou super admin uniquement)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")

    # Vérifier si l'email existe déjà
    result = await db.execute(text("""
        SELECT id FROM geoclic_users WHERE email = :email
    """), {"email": user_data.email})

    if result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà"
        )

    # Créer l'utilisateur
    password_hash = get_password_hash(user_data.password)

    result = await db.execute(text("""
        INSERT INTO geoclic_users (
            email, password_hash, nom, prenom,
            role_data, role_demandes, role_sig, role_terrain, service_id
        )
        VALUES (
            :email, :password_hash, :nom, :prenom,
            :role_data, :role_demandes, :role_sig, :role_terrain,
            CAST(:service_id AS uuid)
        )
        RETURNING id, email, nom, prenom, actif, is_super_admin,
                  role_data, role_demandes, role_sig, role_terrain, service_id, created_at
    """), {
        "email": user_data.email,
        "password_hash": password_hash,
        "nom": user_data.nom,
        "prenom": user_data.prenom,
        "role_data": user_data.role_data,
        "role_demandes": user_data.role_demandes,
        "role_sig": user_data.role_sig,
        "role_terrain": user_data.role_terrain,
        "service_id": user_data.service_id,
    })
    await db.commit()

    row = result.fetchone()

    return UserResponse(
        id=str(row.id),
        email=row.email,
        nom=row.nom,
        prenom=row.prenom,
        actif=row.actif,
        is_super_admin=row.is_super_admin,
        role_data=row.role_data,
        role_demandes=row.role_demandes,
        role_sig=row.role_sig,
        role_terrain=row.role_terrain,
        service_id=str(row.service_id) if row.service_id else None,
        created_at=row.created_at,
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Récupère un utilisateur par son ID."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")

    result = await db.execute(text("""
        SELECT u.id, u.email, u.nom, u.prenom, u.actif,
               u.is_super_admin, u.role_data, u.role_demandes, u.role_sig, u.role_terrain,
               u.service_id, s.nom AS service_nom, u.last_login, u.created_at
        FROM geoclic_users u
        LEFT JOIN demandes_services s ON u.service_id = s.id
        WHERE u.id = CAST(:id AS uuid)
    """), {"id": user_id})

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    return UserResponse(
        id=str(row.id),
        email=row.email,
        nom=row.nom,
        prenom=row.prenom,
        actif=row.actif,
        is_super_admin=row.is_super_admin,
        role_data=row.role_data,
        role_demandes=row.role_demandes,
        role_sig=row.role_sig,
        role_terrain=row.role_terrain,
        service_id=str(row.service_id) if row.service_id else None,
        service_nom=row.service_nom,
        last_login=row.last_login,
        created_at=row.created_at,
    )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Met à jour un utilisateur."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")

    # Vérifier que l'utilisateur existe
    result = await db.execute(text("""
        SELECT id, is_super_admin FROM geoclic_users WHERE id = CAST(:id AS uuid)
    """), {"id": user_id})
    existing = result.fetchone()

    if not existing:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Empêcher la modification du super admin par un non-super admin
    if existing.is_super_admin and not current_user.get("is_super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul un super admin peut modifier un autre super admin"
        )

    # Construire la requête de mise à jour
    updates = []
    params = {"id": user_id}

    if user_data.email is not None:
        updates.append("email = :email")
        params["email"] = user_data.email
    if user_data.nom is not None:
        updates.append("nom = :nom")
        params["nom"] = user_data.nom
    if user_data.prenom is not None:
        updates.append("prenom = :prenom")
        params["prenom"] = user_data.prenom
    if user_data.password is not None:
        updates.append("password_hash = :password_hash")
        params["password_hash"] = get_password_hash(user_data.password)
    if user_data.actif is not None:
        updates.append("actif = :actif")
        params["actif"] = user_data.actif
    if user_data.role_data is not None:
        updates.append("role_data = :role_data")
        params["role_data"] = user_data.role_data
    if user_data.role_demandes is not None:
        updates.append("role_demandes = :role_demandes")
        params["role_demandes"] = user_data.role_demandes
    if user_data.role_sig is not None:
        updates.append("role_sig = :role_sig")
        params["role_sig"] = user_data.role_sig
    if user_data.role_terrain is not None:
        updates.append("role_terrain = :role_terrain")
        params["role_terrain"] = user_data.role_terrain
    if user_data.service_id is not None:
        if user_data.service_id == "":
            updates.append("service_id = NULL")
        else:
            updates.append("service_id = CAST(:service_id AS uuid)")
            params["service_id"] = user_data.service_id

    if not updates:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")

    query = f"""
        UPDATE geoclic_users SET {', '.join(updates)}
        WHERE id = CAST(:id AS uuid)
        RETURNING id, email, nom, prenom, actif, is_super_admin,
                  role_data, role_demandes, role_sig, role_terrain, service_id, created_at
    """

    result = await db.execute(text(query), params)
    await db.commit()

    row = result.fetchone()

    # Récupérer le nom du service
    service_nom = None
    if row.service_id:
        srv_result = await db.execute(text("""
            SELECT nom FROM demandes_services WHERE id = :id
        """), {"id": str(row.service_id)})
        srv = srv_result.fetchone()
        if srv:
            service_nom = srv.nom

    return UserResponse(
        id=str(row.id),
        email=row.email,
        nom=row.nom,
        prenom=row.prenom,
        actif=row.actif,
        is_super_admin=row.is_super_admin,
        role_data=row.role_data,
        role_demandes=row.role_demandes,
        role_sig=row.role_sig,
        role_terrain=row.role_terrain,
        service_id=str(row.service_id) if row.service_id else None,
        service_nom=service_nom,
        created_at=row.created_at,
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Supprime un utilisateur."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")

    # Vérifier que l'utilisateur existe et n'est pas super admin
    result = await db.execute(text("""
        SELECT id, is_super_admin FROM geoclic_users WHERE id = CAST(:id AS uuid)
    """), {"id": user_id})
    existing = result.fetchone()

    if not existing:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    if existing.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de supprimer un super admin"
        )

    # Empêcher de se supprimer soi-même
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas supprimer votre propre compte"
        )

    await db.execute(text("""
        DELETE FROM geoclic_users WHERE id = CAST(:id AS uuid)
    """), {"id": user_id})
    await db.commit()

    return {"message": "Utilisateur supprimé"}


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT SUPER ADMIN (changement depuis l'interface)
# ═══════════════════════════════════════════════════════════════════════════════

@router.put("/super-admin", response_model=UserResponse)
async def update_super_admin(
    data: SuperAdminUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Met à jour ou remplace le super admin.
    Seul le super admin actuel peut faire cette opération.
    """
    if not current_user.get("is_super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul le super admin peut effectuer cette opération"
        )

    password_hash = get_password_hash(data.password)

    # Utiliser la fonction SQL qui gère le remplacement
    result = await db.execute(text("""
        SELECT create_super_admin(:email, :password_hash, :nom, :prenom) AS new_id
    """), {
        "email": data.email,
        "password_hash": password_hash,
        "nom": data.nom,
        "prenom": data.prenom,
    })
    await db.commit()

    row = result.fetchone()
    new_id = str(row.new_id)

    # Récupérer les infos complètes
    result = await db.execute(text("""
        SELECT u.id, u.email, u.nom, u.prenom, u.actif,
               u.is_super_admin, u.role_data, u.role_demandes, u.role_sig, u.role_terrain,
               u.service_id, u.created_at
        FROM geoclic_users u
        WHERE u.id = CAST(:id AS uuid)
    """), {"id": new_id})

    user = result.fetchone()

    return UserResponse(
        id=str(user.id),
        email=user.email,
        nom=user.nom,
        prenom=user.prenom,
        actif=user.actif,
        is_super_admin=user.is_super_admin,
        role_data=user.role_data,
        role_demandes=user.role_demandes,
        role_sig=user.role_sig,
        role_terrain=user.role_terrain,
        service_id=str(user.service_id) if user.service_id else None,
        created_at=user.created_at,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/services")
async def list_services_for_dropdown(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Liste les services pour le dropdown (assignation agents terrain)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")

    result = await db.execute(text("""
        SELECT id, nom FROM demandes_services WHERE actif = TRUE ORDER BY nom
    """))

    return [{"id": str(row.id), "nom": row.nom} for row in result.fetchall()]


@router.post("/hash-password")
async def hash_password_util(
    password: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Génère un hash bcrypt pour un mot de passe.
    Utile pour créer le super admin en SQL.
    """
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Accès refusé")

    return {"hash": get_password_hash(password)}
