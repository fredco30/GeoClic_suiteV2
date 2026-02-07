"""
═══════════════════════════════════════════════════════════════════════════════
GeoClic Services API Router
API dédiée aux équipes terrain des services municipaux
═══════════════════════════════════════════════════════════════════════════════
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional, List
import bcrypt
import json

from database import get_db
from config import settings
from schemas.services import (
    # Auth
    ServiceLoginRequest,
    ServiceAgentResponse,
    ServiceToken,
    PasswordChangeRequest,
    AgentRole,
    # Demandes
    ServiceDemandeListItem,
    ServiceDemandeDetail,
    ServiceDemandeStatutUpdate,
    ServiceDemandeAgentUpdate,
    # Messages
    MessageCreate,
    MessageResponse,
    UnreadCountItem,
    SenderType,
    # Agents
    AgentCreate,
    AgentUpdate,
    AgentResetPassword,
    AgentListItem,
    # Stats
    ServiceStats,
    ServiceStatsAgent,
)

router = APIRouter()

# OAuth2 scheme spécifique pour services
oauth2_services = OAuth2PasswordBearer(tokenUrl="/api/services/auth/login")


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES AUTHENTIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash un mot de passe."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_service_token(agent_data: dict, expires_delta: timedelta = None) -> str:
    """Crée un token JWT pour agent service."""
    to_encode = {
        "sub": str(agent_data["id"]),
        "type": "service",  # Distingue des tokens classiques
        "service_id": str(agent_data["service_id"]),
        "role": agent_data["role"],
        "exp": datetime.utcnow() + (expires_delta or timedelta(hours=12)),
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


async def get_current_agent(
    token: str = Depends(oauth2_services),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Récupère l'agent service courant depuis le token.
    Supporte les tokens du système unifié (geoclic_users) et legacy (demandes_services_agents).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Token du système unifié (geoclic_users)
    if token_type != "service":
        result = await db.execute(
            text("""
                SELECT
                    u.id,
                    u.email,
                    u.nom,
                    u.prenom,
                    COALESCE(u.prenom || ' ' || u.nom, u.email) AS nom_complet,
                    u.actif,
                    u.is_super_admin,
                    u.role_terrain,
                    u.role_demandes,
                    u.service_id,
                    s.nom AS service_nom,
                    s.code AS service_code,
                    s.couleur AS service_couleur,
                    s.project_id
                FROM geoclic_users u
                LEFT JOIN demandes_services s ON u.service_id = s.id
                WHERE u.id = CAST(:id AS uuid) AND u.actif = TRUE
            """),
            {"id": user_id},
        )
        user = result.mappings().first()
        if user is None:
            raise credentials_exception

        # Vérifier l'accès à terrain (super_admin ou role_terrain != 'aucun')
        if not user["is_super_admin"] and user["role_terrain"] == "aucun":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès à GéoClic Services",
            )

        # Convertir en format compatible avec l'ancien système
        # role = "responsable" si super_admin OU role_demandes = 'admin' (responsable de service)
        is_responsable = user["is_super_admin"] or user.get("role_demandes") == "admin"
        return {
            "id": str(user["id"]),
            "service_id": str(user["service_id"]) if user["service_id"] else None,
            "email": user["email"],
            "nom": user["nom"],
            "prenom": user["prenom"],
            "nom_complet": user["nom_complet"],
            "telephone": None,
            "role": "responsable" if is_responsable else "agent",
            "peut_assigner": is_responsable or user["role_terrain"] == "agent",
            "actif": user["actif"],
            "last_login": None,
            "created_at": None,
            "service_nom": user["service_nom"],
            "service_code": user["service_code"],
            "service_couleur": user["service_couleur"],
            "project_id": user["project_id"],
            "is_super_admin": user["is_super_admin"],
        }

    # Token legacy (demandes_services_agents)
    result = await db.execute(
        text("""
            SELECT
                a.id,
                a.service_id,
                a.email,
                a.nom,
                a.prenom,
                COALESCE(a.nom || ' ' || a.prenom, a.email) AS nom_complet,
                a.telephone,
                a.role,
                a.peut_assigner,
                a.actif,
                a.last_login,
                a.created_at,
                s.nom AS service_nom,
                s.code AS service_code,
                s.couleur AS service_couleur,
                s.project_id
            FROM demandes_services_agents a
            JOIN demandes_services s ON a.service_id = s.id
            WHERE a.id = :id AND a.actif = TRUE
        """),
        {"id": user_id},
    )
    agent = result.mappings().first()
    if agent is None:
        raise credentials_exception
    return dict(agent)


def require_responsable(current_agent: dict = Depends(get_current_agent)) -> dict:
    """Vérifie que l'agent est responsable."""
    if current_agent["role"] != "responsable":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action réservée aux responsables de service",
        )
    return current_agent


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/auth/login", response_model=ServiceToken)
async def login(
    credentials: ServiceLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Connexion d'un agent service."""
    # Rechercher l'agent par email
    result = await db.execute(
        text("""
            SELECT
                a.id,
                a.service_id,
                a.email,
                a.password_hash,
                a.nom,
                a.prenom,
                COALESCE(a.nom || ' ' || a.prenom, a.email) AS nom_complet,
                a.telephone,
                a.role,
                a.peut_assigner,
                a.actif,
                a.last_login,
                a.created_at,
                s.nom AS service_nom,
                s.code AS service_code,
                s.couleur AS service_couleur,
                s.project_id
            FROM demandes_services_agents a
            JOIN demandes_services s ON a.service_id = s.id
            WHERE a.email = :email
        """),
        {"email": credentials.email},
    )
    agent = result.mappings().first()

    # Vérifications
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    if not agent["actif"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte désactivé. Contactez votre responsable.",
        )

    if not agent["password_hash"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte non configuré. Contactez votre responsable.",
        )

    if not verify_password(credentials.password, agent["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    # Mettre à jour last_login
    await db.execute(
        text("UPDATE demandes_services_agents SET last_login = CURRENT_TIMESTAMP WHERE id = :id"),
        {"id": str(agent["id"])},
    )
    await db.commit()

    # Générer le token
    access_token = create_service_token(dict(agent))

    return ServiceToken(
        access_token=access_token,
        expires_in=12 * 3600,  # 12 heures
        agent=ServiceAgentResponse(
            id=str(agent["id"]),
            service_id=str(agent["service_id"]),
            email=agent["email"],
            nom=agent["nom"],
            prenom=agent["prenom"],
            nom_complet=agent["nom_complet"],
            telephone=agent["telephone"],
            role=agent["role"],
            peut_assigner=agent["peut_assigner"],
            actif=agent["actif"],
            last_login=datetime.utcnow(),
            created_at=agent["created_at"],
            service_nom=agent["service_nom"],
            service_code=agent["service_code"],
            service_couleur=agent["service_couleur"],
            project_id=str(agent["project_id"]),
        ),
    )


@router.post("/auth/logout")
async def logout(current_agent: dict = Depends(get_current_agent)):
    """Déconnexion (côté client, invalidation token)."""
    # En JWT stateless, la déconnexion se fait côté client
    # On pourrait implémenter une blacklist de tokens si nécessaire
    return {"message": "Déconnexion réussie"}


@router.get("/auth/me", response_model=ServiceAgentResponse)
async def get_me(current_agent: dict = Depends(get_current_agent)):
    """Récupère les informations de l'agent connecté."""
    return ServiceAgentResponse(
        id=str(current_agent["id"]),
        service_id=str(current_agent["service_id"]) if current_agent.get("service_id") else None,
        email=current_agent["email"],
        nom=current_agent["nom"],
        prenom=current_agent["prenom"],
        nom_complet=current_agent["nom_complet"],
        telephone=current_agent.get("telephone"),
        role=current_agent["role"],
        peut_assigner=current_agent.get("peut_assigner", False),
        actif=current_agent["actif"],
        last_login=current_agent.get("last_login"),
        created_at=current_agent.get("created_at"),
        service_nom=current_agent.get("service_nom"),
        service_code=current_agent.get("service_code"),
        service_couleur=current_agent.get("service_couleur", "#3b82f6"),
        project_id=str(current_agent["project_id"]) if current_agent.get("project_id") else None,
        is_super_admin=current_agent.get("is_super_admin", False),
    )


@router.put("/auth/password")
async def change_password(
    data: PasswordChangeRequest,
    current_agent: dict = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Changer son mot de passe."""
    # Récupérer le hash actuel
    result = await db.execute(
        text("SELECT password_hash FROM demandes_services_agents WHERE id = :id"),
        {"id": str(current_agent["id"])},
    )
    agent = result.mappings().first()

    if not verify_password(data.current_password, agent["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect",
        )

    # Mettre à jour
    new_hash = get_password_hash(data.new_password)
    await db.execute(
        text("UPDATE demandes_services_agents SET password_hash = :hash WHERE id = :id"),
        {"hash": new_hash, "id": str(current_agent["id"])},
    )
    await db.commit()

    return {"message": "Mot de passe modifié avec succès"}


# ═══════════════════════════════════════════════════════════════════════════════
# DEMANDES (FILTRÉES PAR SERVICE)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/demandes", response_model=List[ServiceDemandeListItem])
async def list_demandes(
    current_agent: dict = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
    statut: Optional[str] = Query(None, description="Filtrer par statut"),
    priorite: Optional[str] = Query(None, description="Filtrer par priorité"),
    agent_service_id: Optional[str] = Query(None, description="Filtrer par agent terrain"),
    my_demandes: bool = Query(False, description="Ne voir que mes demandes assignées (pour Terrain PWA)"),
    search: Optional[str] = Query(None, description="Recherche texte"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Liste des demandes assignées au service (super_admin voit tout)."""
    current_agent_id = str(current_agent["id"])
    is_super_admin = current_agent.get("is_super_admin", False)
    service_id = current_agent.get("service_id")

    # Construction de la requête
    where_clauses = []
    params = {"limit": limit, "offset": offset}

    # Super admin voit tout, sinon filtrer par service
    if not is_super_admin and service_id:
        where_clauses.append("d.service_assigne_id = CAST(:service_id AS uuid)")
        params["service_id"] = str(service_id)
    elif not is_super_admin:
        # Agent sans service_id et pas super_admin = aucune demande
        where_clauses.append("1 = 0")

    # Si my_demandes=true, filtrer par agent connecté (utilisé par Terrain PWA)
    # Note: Le current_agent_id peut être un geoclic_users.id (auth unifiée)
    # mais d.agent_service_id référence demandes_services_agents.id
    # On doit donc chercher l'ID correspondant par email
    if my_demandes:
        # Chercher l'ID demandes_services_agents correspondant à l'email de l'agent
        agent_email = current_agent.get("email")
        agent_lookup = await db.execute(
            text("SELECT id FROM demandes_services_agents WHERE email = :email AND actif = TRUE"),
            {"email": agent_email},
        )
        agent_row = agent_lookup.first()
        if agent_row:
            where_clauses.append("d.agent_service_id = CAST(:my_agent_id AS uuid)")
            params["my_agent_id"] = str(agent_row.id)
        else:
            # Aucun agent correspondant trouvé, ne retourner aucune demande
            where_clauses.append("1 = 0")

    if statut:
        where_clauses.append("d.statut = :statut")
        params["statut"] = statut

    if priorite:
        where_clauses.append("d.priorite = :priorite")
        params["priorite"] = priorite

    if agent_service_id:
        if agent_service_id == "non_assigne":
            where_clauses.append("d.agent_service_id IS NULL")
        else:
            where_clauses.append("d.agent_service_id = :agent_service_id")
            params["agent_service_id"] = agent_service_id

    if search:
        where_clauses.append("""
            (d.description ILIKE :search
             OR d.adresse_approximative ILIKE :search
             OR d.numero_suivi ILIKE :search)
        """)
        params["search"] = f"%{search}%"

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    result = await db.execute(
        text(f"""
            SELECT
                d.id,
                d.numero_suivi AS numero,
                d.description,
                d.statut,
                d.priorite,
                d.created_at,
                d.updated_at,
                d.categorie_id,
                c.nom AS categorie_nom,
                c.icone AS categorie_icone,
                COALESCE('#' || LPAD(UPPER(TO_HEX(c.couleur::bigint & x'FFFFFF'::bigint)), 6, '0'), '#3B82F6') AS categorie_couleur,
                d.adresse_approximative AS adresse,
                p.name AS quartier_nom,
                ST_Y(d.geom) AS latitude,
                ST_X(d.geom) AS longitude,
                d.agent_service_id,
                COALESCE(ag.nom || ' ' || ag.prenom, ag.email) AS agent_service_nom,
                COALESCE(jsonb_array_length(d.photos), 0) > 0 AS has_photos,
                COALESCE(jsonb_array_length(d.photos), 0) AS photo_count,
                COALESCE(unread.cnt, 0) AS unread_messages
            FROM demandes_citoyens d
            LEFT JOIN demandes_categories c ON d.categorie_id = c.id
            LEFT JOIN perimetres p ON d.quartier_id = p.id
            LEFT JOIN demandes_services_agents ag ON d.agent_service_id = ag.id
            LEFT JOIN (
                SELECT demande_id, COUNT(*) AS cnt
                FROM demandes_messages
                WHERE lu_par_service = FALSE AND sender_type = 'demandes'
                GROUP BY demande_id
            ) unread ON unread.demande_id = d.id
            WHERE {where_sql}
            ORDER BY
                CASE d.priorite WHEN 'urgente' THEN 0 WHEN 'haute' THEN 1 WHEN 'normale' THEN 2 ELSE 3 END,
                d.created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )
    demandes = result.mappings().all()

    return [
        ServiceDemandeListItem(
            id=str(d["id"]),
            numero=d["numero"],
            description=d["description"],
            statut=d["statut"],
            priorite=d["priorite"] or "normale",
            created_at=d["created_at"],
            updated_at=d["updated_at"],
            categorie_id=str(d["categorie_id"]) if d["categorie_id"] else None,
            categorie_nom=d["categorie_nom"],
            categorie_icone=d["categorie_icone"],
            categorie_couleur=d["categorie_couleur"],
            adresse=d["adresse"],
            quartier_nom=d["quartier_nom"],
            latitude=d["latitude"],
            longitude=d["longitude"],
            agent_service_id=str(d["agent_service_id"]) if d["agent_service_id"] else None,
            agent_service_nom=d["agent_service_nom"],
            has_photos=d["has_photos"],
            photo_count=d["photo_count"],
            unread_messages=d["unread_messages"],
        )
        for d in demandes
    ]


@router.get("/demandes/{demande_id}", response_model=ServiceDemandeDetail)
async def get_demande(
    demande_id: str,
    current_agent: dict = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Détail d'une demande (super_admin peut voir toutes)."""
    is_super_admin = current_agent.get("is_super_admin", False)
    service_id = current_agent.get("service_id")

    # Super admin peut voir toutes les demandes
    if is_super_admin:
        where_clause = "d.id = :demande_id"
        params = {"demande_id": demande_id}
    elif service_id:
        where_clause = "d.id = :demande_id AND d.service_assigne_id = CAST(:service_id AS uuid)"
        params = {"demande_id": demande_id, "service_id": str(service_id)}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas de service assigné",
        )

    result = await db.execute(
        text(f"""
            SELECT
                d.id,
                d.numero_suivi AS numero,
                d.description,
                d.statut,
                d.priorite,
                d.created_at,
                d.updated_at,
                d.categorie_id,
                c.nom AS categorie_nom,
                c.icone AS categorie_icone,
                COALESCE('#' || LPAD(UPPER(TO_HEX(c.couleur::bigint & x'FFFFFF'::bigint)), 6, '0'), '#3B82F6') AS categorie_couleur,
                d.adresse_approximative AS adresse,
                p.name AS quartier_nom,
                ST_Y(d.geom) AS latitude,
                ST_X(d.geom) AS longitude,
                d.agent_service_id,
                COALESCE(ag.nom || ' ' || ag.prenom, ag.email) AS agent_service_nom,
                d.photos,
                d.photos_intervention,
                d.declarant_nom,
                LEFT(d.declarant_nom, 1) AS declarant_initial_nom,
                CASE
                    WHEN d.declarant_email IS NOT NULL
                    THEN LEFT(d.declarant_email, 1) || '***@' || SPLIT_PART(d.declarant_email, '@', 2)
                    ELSE NULL
                END AS declarant_email_masque,
                d.date_prise_en_charge,
                d.date_planification,
                d.date_resolution
            FROM demandes_citoyens d
            LEFT JOIN demandes_categories c ON d.categorie_id = c.id
            LEFT JOIN perimetres p ON d.quartier_id = p.id
            LEFT JOIN demandes_services_agents ag ON d.agent_service_id = ag.id
            WHERE {where_clause}
        """),
        params,
    )
    d = result.mappings().first()

    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée ou non assignée à votre service",
        )

    # Compter les messages non lus
    unread_result = await db.execute(
        text("""
            SELECT COUNT(*) AS cnt
            FROM demandes_messages
            WHERE demande_id = :demande_id
              AND lu_par_service = FALSE
              AND sender_type = 'demandes'
        """),
        {"demande_id": demande_id},
    )
    unread_count = unread_result.scalar() or 0

    # Séparer photos et documents par extension
    IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
    all_files = d["photos"] or []
    photos_list = [f for f in all_files if any(f.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)]
    documents_list = [f for f in all_files if isinstance(f, str) and not any(f.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)]

    return ServiceDemandeDetail(
        id=str(d["id"]),
        numero=d["numero"],
        description=d["description"],
        statut=d["statut"],
        priorite=d["priorite"] or "normale",
        created_at=d["created_at"],
        updated_at=d["updated_at"],
        categorie_id=str(d["categorie_id"]) if d["categorie_id"] else None,
        categorie_nom=d["categorie_nom"],
        categorie_icone=d["categorie_icone"],
        categorie_couleur=d["categorie_couleur"],
        adresse=d["adresse"],
        quartier_nom=d["quartier_nom"],
        latitude=d["latitude"],
        longitude=d["longitude"],
        agent_service_id=str(d["agent_service_id"]) if d["agent_service_id"] else None,
        agent_service_nom=d["agent_service_nom"],
        has_photos=bool(d["photos"]),
        photo_count=len(photos_list),
        unread_messages=unread_count,
        declarant_prenom=d["declarant_nom"],
        declarant_initial_nom=d["declarant_initial_nom"],
        declarant_email_masque=d["declarant_email_masque"],
        date_prise_en_charge=d["date_prise_en_charge"],
        date_planification=d["date_planification"],
        date_resolution=d["date_resolution"],
        commentaire_interne=None,
        photos=photos_list,
        documents=documents_list,
        photos_intervention=d["photos_intervention"] if isinstance(d["photos_intervention"], list) else (json.loads(d["photos_intervention"]) if d["photos_intervention"] else []),
    )


@router.put("/demandes/{demande_id}/statut")
async def update_demande_statut(
    demande_id: str,
    data: ServiceDemandeStatutUpdate,
    current_agent: dict = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Changer le statut d'une demande (super_admin peut modifier toutes)."""
    is_super_admin = current_agent.get("is_super_admin", False)
    service_id = current_agent.get("service_id")

    # Vérifier que la demande appartient au service (ou super_admin)
    if is_super_admin:
        query = "SELECT id, statut FROM demandes_citoyens WHERE id = CAST(:id AS uuid)"
        params = {"id": demande_id}
    elif service_id:
        query = "SELECT id, statut FROM demandes_citoyens WHERE id = CAST(:id AS uuid) AND service_assigne_id = CAST(:service_id AS uuid)"
        params = {"id": demande_id, "service_id": str(service_id)}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas de service assigné",
        )

    result = await db.execute(text(query), params)
    demande = result.mappings().first()

    if not demande:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée ou non assignée à votre service",
        )

    # Mettre à jour le statut
    update_fields = ["statut = :statut", "updated_at = CURRENT_TIMESTAMP"]
    params = {"id": demande_id, "statut": data.statut}

    # Date de prise en charge si passage à en_cours
    if data.statut == "en_cours" and demande["statut"] not in ("en_cours", "planifie", "traite"):
        update_fields.append("date_prise_en_charge = CURRENT_TIMESTAMP")

    # Date de résolution si passage à traite
    if data.statut == "traite":
        update_fields.append("date_resolution = CURRENT_TIMESTAMP")

    # Date de planification si passage à planifie
    if data.statut == "planifie":
        if data.date_planification:
            update_fields.append("date_planification = :date_planification")
            params["date_planification"] = data.date_planification
        # Aussi enregistrer la date de prise en charge si pas déjà fait
        if demande["statut"] not in ("en_cours", "planifie", "traite"):
            update_fields.append("date_prise_en_charge = CURRENT_TIMESTAMP")

    # Commentaire interne
    if data.commentaire:
        update_fields.append("commentaire_interne = COALESCE(commentaire_interne || E'\\n', '') || :commentaire")
        params["commentaire"] = f"[{datetime.now().strftime('%d/%m/%Y %H:%M')} - {current_agent['nom_complet']}] {data.commentaire}"

    # Sécurité : whitelist des colonnes autorisées pour l'UPDATE
    ALLOWED_DEMANDE_COLS = {
        "statut", "updated_at", "agent_service_id", "date_prise_en_charge",
        "date_resolution", "date_planification", "commentaire_interne",
    }
    for u in update_fields:
        col_name = u.split("=")[0].strip()
        if col_name not in ALLOWED_DEMANDE_COLS:
            raise HTTPException(status_code=400, detail=f"Colonne non autorisée: {col_name}")

    await db.execute(
        text(f"UPDATE demandes_citoyens SET {', '.join(update_fields)} WHERE id = CAST(:id AS uuid)"),
        params,
    )
    await db.commit()

    return {"message": "Statut mis à jour", "statut": data.statut}


@router.put("/demandes/{demande_id}/agent")
async def update_demande_agent(
    demande_id: str,
    data: ServiceDemandeAgentUpdate,
    current_agent: dict = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Assigner un agent terrain à une demande (super_admin, responsable ou agent avec peut_assigner)."""
    is_super_admin = current_agent.get("is_super_admin", False)
    service_id = current_agent.get("service_id")

    # Vérifier les permissions (super_admin peut toujours assigner)
    if not is_super_admin:
        role = current_agent.get("role")
        peut_assigner = current_agent.get("peut_assigner", False)
        if role != "responsable" and not peut_assigner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas la permission d'assigner des demandes",
            )

    # Vérifier que la demande existe (et appartient au service si pas super_admin)
    if is_super_admin:
        query = "SELECT id FROM demandes_citoyens WHERE id = CAST(:id AS uuid)"
        params = {"id": demande_id}
    elif service_id:
        query = "SELECT id FROM demandes_citoyens WHERE id = CAST(:id AS uuid) AND service_assigne_id = CAST(:service_id AS uuid)"
        params = {"id": demande_id, "service_id": str(service_id)}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas de service assigné",
        )

    result = await db.execute(text(query), params)
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée ou non assignée à votre service",
        )

    # Si on assigne un agent, vérifier qu'il existe (super_admin peut assigner n'importe qui)
    if data.agent_service_id:
        if is_super_admin:
            agent_query = "SELECT id FROM demandes_services_agents WHERE id = CAST(:id AS uuid) AND actif = TRUE"
            agent_params = {"id": data.agent_service_id}
        else:
            agent_query = "SELECT id FROM demandes_services_agents WHERE id = CAST(:id AS uuid) AND service_id = CAST(:service_id AS uuid) AND actif = TRUE"
            agent_params = {"id": data.agent_service_id, "service_id": str(service_id)}

        result = await db.execute(text(agent_query), agent_params)
        if not result.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent non trouvé dans votre service",
            )

    # Mettre à jour
    await db.execute(
        text("""
            UPDATE demandes_citoyens
            SET agent_service_id = CAST(:agent_id AS uuid), updated_at = CURRENT_TIMESTAMP
            WHERE id = CAST(:id AS uuid)
        """),
        {"id": demande_id, "agent_id": data.agent_service_id},
    )
    await db.commit()

    # Envoyer une notification push à l'agent assigné
    if data.agent_service_id:
        try:
            from routers.push import send_push_to_user
            # Trouver le user_id (geoclic_users) de l'agent assigné
            agent_user = await db.execute(text("""
                SELECT gu.id::text as user_id
                FROM geoclic_users gu
                JOIN demandes_services_agents dsa ON dsa.email = gu.email
                WHERE dsa.id = CAST(:agent_id AS uuid)
            """), {"agent_id": data.agent_service_id})
            agent_row = agent_user.mappings().first()
            if agent_row:
                # Récupérer le numéro de la demande pour le message
                dem_result = await db.execute(text(
                    "SELECT numero_suivi FROM demandes_citoyens WHERE id = CAST(:id AS uuid)"
                ), {"id": demande_id})
                dem = dem_result.mappings().first()
                num = dem["numero_suivi"] if dem else demande_id[:8]
                await send_push_to_user(
                    agent_row["user_id"],
                    "Nouvelle demande assignée",
                    f"La demande {num} vous a été assignée",
                    f"/terrain/demandes/{demande_id}",
                    db
                )
        except Exception as e:
            logger.warning(f"Push notification échouée (non bloquant): {e}")

    return {"message": "Agent assigné" if data.agent_service_id else "Agent retiré"}


# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGES (TCHAT)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/demandes/{demande_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    demande_id: str,
    current_agent: dict = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    canal: str = Query("backoffice", description="Canal: backoffice ou terrain"),
):
    """Liste des messages d'une demande par canal (super_admin voit tout)."""
    is_super_admin = current_agent.get("is_super_admin", False)
    service_id = current_agent.get("service_id")

    # Vérifier que la demande existe (et appartient au service si pas super_admin)
    if is_super_admin:
        query = "SELECT id FROM demandes_citoyens WHERE id = :id"
        params = {"id": demande_id}
    elif service_id:
        query = "SELECT id FROM demandes_citoyens WHERE id = :id AND service_assigne_id = CAST(:service_id AS uuid)"
        params = {"id": demande_id, "service_id": str(service_id)}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas de service assigné",
        )

    result = await db.execute(text(query), params)
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée ou non assignée à votre service",
        )

    # Récupérer les messages du canal spécifié
    result = await db.execute(
        text("""
            SELECT id, demande_id, sender_type, sender_id, sender_nom, message,
                   lu_par_service, lu_par_demandes, created_at
            FROM demandes_messages
            WHERE demande_id = :demande_id AND COALESCE(canal, 'backoffice') = :canal
            ORDER BY created_at ASC
            LIMIT :limit
        """),
        {"demande_id": demande_id, "limit": limit, "canal": canal},
    )
    messages = result.mappings().all()

    return [
        MessageResponse(
            id=str(m["id"]),
            demande_id=str(m["demande_id"]),
            sender_type=m["sender_type"],
            sender_id=str(m["sender_id"]) if m["sender_id"] else None,
            sender_nom=m["sender_nom"],
            message=m["message"],
            lu_par_service=m["lu_par_service"],
            lu_par_demandes=m["lu_par_demandes"],
            created_at=m["created_at"],
        )
        for m in messages
    ]


@router.post("/demandes/{demande_id}/messages", response_model=MessageResponse)
async def create_message(
    demande_id: str,
    data: MessageCreate,
    current_agent: dict = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
    canal: str = Query("backoffice", description="Canal: backoffice ou terrain"),
    source: str = Query("service", description="Source: service (desktop) ou terrain (PWA)"),
):
    """Envoyer un message sur un canal spécifique (super_admin peut écrire partout)."""
    is_super_admin = current_agent.get("is_super_admin", False)
    service_id = current_agent.get("service_id")

    # Vérifier que la demande existe (et appartient au service si pas super_admin)
    if is_super_admin:
        query = "SELECT id FROM demandes_citoyens WHERE id = :id"
        params = {"id": demande_id}
    elif service_id:
        query = "SELECT id FROM demandes_citoyens WHERE id = :id AND service_assigne_id = CAST(:service_id AS uuid)"
        params = {"id": demande_id, "service_id": str(service_id)}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas de service assigné",
        )

    result = await db.execute(text(query), params)
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée ou non assignée à votre service",
        )

    # Déterminer le sender_type (service = desktop, terrain = PWA mobile)
    sender_type = source if source in ['service', 'terrain'] else 'service'

    # Créer le message avec le canal et sender_type spécifiés
    result = await db.execute(
        text("""
            INSERT INTO demandes_messages (demande_id, sender_type, sender_id, sender_nom, message, lu_par_service, canal)
            VALUES (:demande_id, :sender_type, :sender_id, :sender_nom, :message, TRUE, :canal)
            RETURNING id, demande_id, sender_type, sender_id, sender_nom, message,
                      lu_par_service, lu_par_demandes, created_at
        """),
        {
            "demande_id": demande_id,
            "sender_type": sender_type,
            "sender_id": str(current_agent["id"]),
            "sender_nom": current_agent["nom_complet"],
            "message": data.message,
            "canal": canal,
        },
    )
    await db.commit()
    m = result.mappings().first()

    return MessageResponse(
        id=str(m["id"]),
        demande_id=str(m["demande_id"]),
        sender_type=m["sender_type"],
        sender_id=str(m["sender_id"]) if m["sender_id"] else None,
        sender_nom=m["sender_nom"],
        message=m["message"],
        lu_par_service=m["lu_par_service"],
        lu_par_demandes=m["lu_par_demandes"],
        created_at=m["created_at"],
    )


@router.put("/demandes/{demande_id}/messages/read")
async def mark_messages_read(
    demande_id: str,
    current_agent: dict = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
    canal: str = Query("backoffice", description="Canal: backoffice ou terrain"),
):
    """Marquer les messages comme lus par le service (par canal)."""
    is_super_admin = current_agent.get("is_super_admin", False)
    service_id = current_agent.get("service_id")

    # Vérifier que la demande existe (et appartient au service si pas super_admin)
    if is_super_admin:
        query = "SELECT id FROM demandes_citoyens WHERE id = :id"
        params = {"id": demande_id}
    elif service_id:
        query = "SELECT id FROM demandes_citoyens WHERE id = :id AND service_assigne_id = CAST(:service_id AS uuid)"
        params = {"id": demande_id, "service_id": str(service_id)}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas de service assigné",
        )

    result = await db.execute(text(query), params)
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée ou non assignée à votre service",
        )

    # Marquer comme lus (pour le canal spécifié)
    # Pour backoffice: messages venant de 'demandes'
    # Pour terrain: messages venant de 'terrain'
    sender_filter = 'demandes' if canal == 'backoffice' else 'terrain'
    result = await db.execute(
        text("""
            UPDATE demandes_messages
            SET lu_par_service = TRUE
            WHERE demande_id = :demande_id
              AND lu_par_service = FALSE
              AND sender_type = :sender_filter
              AND COALESCE(canal, 'backoffice') = :canal
        """),
        {"demande_id": demande_id, "sender_filter": sender_filter, "canal": canal},
    )
    await db.commit()

    return {"marked_read": result.rowcount}


@router.get("/demandes/unread-count", response_model=List[UnreadCountItem])
async def get_unread_count(
    current_agent: dict = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Compteur de messages non lus par demande (super_admin voit tout)."""
    is_super_admin = current_agent.get("is_super_admin", False)
    service_id = current_agent.get("service_id")

    # Super admin voit tous les messages non lus
    if is_super_admin:
        query = """
            SELECT m.demande_id, COUNT(*) AS unread_count
            FROM demandes_messages m
            JOIN demandes_citoyens d ON d.id = m.demande_id
            WHERE m.lu_par_service = FALSE
              AND m.sender_type = 'demandes'
            GROUP BY m.demande_id
        """
        params = {}
    elif service_id:
        query = """
            SELECT m.demande_id, COUNT(*) AS unread_count
            FROM demandes_messages m
            JOIN demandes_citoyens d ON d.id = m.demande_id
            WHERE d.service_assigne_id = CAST(:service_id AS uuid)
              AND m.lu_par_service = FALSE
              AND m.sender_type = 'demandes'
            GROUP BY m.demande_id
        """
        params = {"service_id": str(service_id)}
    else:
        # Agent sans service_id et pas super_admin = rien
        return []

    result = await db.execute(text(query), params)
    counts = result.mappings().all()

    return [
        UnreadCountItem(demande_id=str(c["demande_id"]), unread_count=c["unread_count"])
        for c in counts
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# GESTION AGENTS (RESPONSABLE UNIQUEMENT)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/agents", response_model=List[AgentListItem])
async def list_agents(
    current_agent: dict = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
    include_inactive: bool = Query(False, description="Inclure les agents inactifs"),
):
    """Liste des agents du service (super_admin voit tous les agents)."""
    is_super_admin = current_agent.get("is_super_admin", False)
    service_id = current_agent.get("service_id")

    # Super admin voit tous les agents
    if is_super_admin:
        where_clause = "1=1"
        params = {}
    elif service_id:
        where_clause = "a.service_id = CAST(:service_id AS uuid)"
        params = {"service_id": str(service_id)}
    else:
        return []

    if not include_inactive:
        where_clause += " AND a.actif = TRUE"

    result = await db.execute(
        text(f"""
            SELECT
                a.id,
                a.email,
                a.nom,
                a.prenom,
                COALESCE(a.nom || ' ' || a.prenom, a.email) AS nom_complet,
                a.telephone,
                a.role,
                a.peut_assigner,
                a.actif,
                a.last_login,
                a.created_at,
                COUNT(d.id) FILTER (WHERE d.statut NOT IN ('traite', 'cloture', 'rejete')) AS demandes_assignees,
                COUNT(d.id) FILTER (WHERE d.statut = 'traite') AS demandes_traitees
            FROM demandes_services_agents a
            LEFT JOIN demandes_citoyens d ON d.agent_service_id = a.id
            WHERE {where_clause}
            GROUP BY a.id
            ORDER BY a.role DESC, a.nom, a.prenom
        """),
        params,
    )
    agents = result.mappings().all()

    return [
        AgentListItem(
            id=str(a["id"]),
            email=a["email"],
            nom=a["nom"],
            prenom=a["prenom"],
            nom_complet=a["nom_complet"],
            telephone=a["telephone"],
            role=a["role"],
            peut_assigner=a["peut_assigner"],
            actif=a["actif"],
            last_login=a["last_login"],
            created_at=a["created_at"],
            demandes_assignees=a["demandes_assignees"],
            demandes_traitees=a["demandes_traitees"],
        )
        for a in agents
    ]


@router.post("/agents", response_model=AgentListItem, status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreate,
    current_agent: dict = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
    service_id: Optional[str] = Query(None, description="Service ID (requis pour super_admin)"),
):
    """Créer un agent (crée aussi dans geoclic_users pour l'accès unifié)."""
    is_super_admin = current_agent.get("is_super_admin", False)
    agent_service_id = current_agent.get("service_id")

    # Déterminer le service_id à utiliser
    if is_super_admin:
        if not service_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Super admin doit spécifier un service_id",
            )
        target_service_id = service_id
    elif agent_service_id:
        target_service_id = str(agent_service_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas de service assigné",
        )

    # Vérifier les permissions (super_admin ou responsable du service)
    if not is_super_admin and current_agent.get("role") != "responsable":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action réservée aux responsables de service",
        )

    # Vérifier que l'email n'existe pas déjà (dans les deux tables)
    result = await db.execute(
        text("SELECT id FROM demandes_services_agents WHERE email = :email"),
        {"email": data.email},
    )
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé",
        )

    result = await db.execute(
        text("SELECT id FROM geoclic_users WHERE email = :email"),
        {"email": data.email},
    )
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé dans le système",
        )

    # Créer l'agent dans demandes_services_agents
    password_hash = get_password_hash(data.password)
    result = await db.execute(
        text("""
            INSERT INTO demandes_services_agents
                (service_id, email, password_hash, nom, prenom, telephone, role, peut_assigner, recoit_notifications)
            VALUES
                (CAST(:service_id AS uuid), :email, :password_hash, :nom, :prenom, :telephone, :role, :peut_assigner, :recoit_notifications)
            RETURNING id, email, nom, prenom, telephone, role, peut_assigner, actif, last_login, created_at
        """),
        {
            "service_id": target_service_id,
            "email": data.email,
            "password_hash": password_hash,
            "nom": data.nom,
            "prenom": data.prenom,
            "telephone": data.telephone,
            "role": data.role.value,
            "peut_assigner": data.peut_assigner,
            "recoit_notifications": data.recoit_notifications,
        },
    )
    a = result.mappings().first()

    # Créer aussi dans geoclic_users pour l'authentification unifiée
    role_demandes = "admin" if data.role.value == "responsable" else "agent"
    await db.execute(
        text("""
            INSERT INTO geoclic_users (
                email, password_hash, nom, prenom, actif,
                is_super_admin, role_data, role_demandes, role_sig, role_terrain,
                service_id
            )
            VALUES (
                :email, :password_hash, :nom, :prenom, TRUE,
                FALSE, 'aucun', :role_demandes, 'aucun', 'agent',
                CAST(:service_id AS uuid)
            )
        """),
        {
            "email": data.email,
            "password_hash": password_hash,
            "nom": data.nom,
            "prenom": data.prenom,
            "role_demandes": role_demandes,
            "service_id": target_service_id,
        },
    )

    await db.commit()

    return AgentListItem(
        id=str(a["id"]),
        email=a["email"],
        nom=a["nom"],
        prenom=a["prenom"],
        nom_complet=f"{a['nom']} {a['prenom']}",
        telephone=a["telephone"],
        role=a["role"],
        peut_assigner=a["peut_assigner"],
        actif=a["actif"],
        last_login=a["last_login"],
        created_at=a["created_at"],
        demandes_assignees=0,
        demandes_traitees=0,
    )


@router.put("/agents/{agent_id}", response_model=AgentListItem)
async def update_agent(
    agent_id: str,
    data: AgentUpdate,
    current_agent: dict = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Modifier un agent (synchronise aussi avec geoclic_users)."""
    is_super_admin = current_agent.get("is_super_admin", False)
    agent_service_id = current_agent.get("service_id")

    # Vérifier les permissions
    if not is_super_admin and current_agent.get("role") != "responsable":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action réservée aux responsables de service",
        )

    # Vérifier que l'agent existe (et appartient au service si pas super_admin)
    if is_super_admin:
        result = await db.execute(
            text("SELECT id, email FROM demandes_services_agents WHERE id = CAST(:id AS uuid)"),
            {"id": agent_id},
        )
    elif agent_service_id:
        result = await db.execute(
            text("SELECT id, email FROM demandes_services_agents WHERE id = CAST(:id AS uuid) AND service_id = CAST(:service_id AS uuid)"),
            {"id": agent_id, "service_id": str(agent_service_id)},
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas de service assigné",
        )

    agent_row = result.first()
    if not agent_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent non trouvé dans votre service",
        )

    agent_email = agent_row.email

    # Construire la mise à jour pour demandes_services_agents
    update_fields = []
    params = {"id": agent_id}

    # Construire la mise à jour pour geoclic_users
    update_fields_users = []
    params_users = {"email": agent_email}

    if data.nom is not None:
        update_fields.append("nom = :nom")
        update_fields_users.append("nom = :nom")
        params["nom"] = data.nom
        params_users["nom"] = data.nom

    if data.prenom is not None:
        update_fields.append("prenom = :prenom")
        update_fields_users.append("prenom = :prenom")
        params["prenom"] = data.prenom
        params_users["prenom"] = data.prenom

    if data.telephone is not None:
        update_fields.append("telephone = :telephone")
        params["telephone"] = data.telephone

    if data.role is not None:
        update_fields.append("role = :role")
        params["role"] = data.role.value
        # Synchroniser le rôle vers geoclic_users
        role_demandes = "admin" if data.role.value == "responsable" else "agent"
        update_fields_users.append("role_demandes = :role_demandes")
        params_users["role_demandes"] = role_demandes

    if data.peut_assigner is not None:
        update_fields.append("peut_assigner = :peut_assigner")
        params["peut_assigner"] = data.peut_assigner

    if data.recoit_notifications is not None:
        update_fields.append("recoit_notifications = :recoit_notifications")
        params["recoit_notifications"] = data.recoit_notifications

    if data.actif is not None:
        update_fields.append("actif = :actif")
        update_fields_users.append("actif = :actif")
        params["actif"] = data.actif
        params_users["actif"] = data.actif

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucune modification fournie",
        )

    # Sécurité : whitelist des colonnes autorisées pour l'UPDATE agents
    ALLOWED_AGENT_COLS = {
        "nom", "prenom", "email", "telephone", "role",
        "peut_assigner", "recoit_notifications", "actif",
    }
    for u in update_fields:
        col_name = u.split("=")[0].strip()
        if col_name not in ALLOWED_AGENT_COLS:
            raise HTTPException(status_code=400, detail=f"Colonne non autorisée: {col_name}")

    ALLOWED_USER_COLS = {"nom", "prenom", "email", "actif", "role_demandes"}
    for u in update_fields_users:
        col_name = u.split("=")[0].strip()
        if col_name not in ALLOWED_USER_COLS:
            raise HTTPException(status_code=400, detail=f"Colonne non autorisée: {col_name}")

    # Mettre à jour demandes_services_agents
    await db.execute(
        text(f"UPDATE demandes_services_agents SET {', '.join(update_fields)} WHERE id = CAST(:id AS uuid)"),
        params,
    )

    # Synchroniser vers geoclic_users si des champs pertinents ont changé
    if update_fields_users:
        await db.execute(
            text(f"UPDATE geoclic_users SET {', '.join(update_fields_users)} WHERE email = :email"),
            params_users,
        )

    await db.commit()

    # Récupérer l'agent mis à jour
    result = await db.execute(
        text("""
            SELECT
                a.id, a.email, a.nom, a.prenom,
                COALESCE(a.nom || ' ' || a.prenom, a.email) AS nom_complet,
                a.telephone, a.role, a.peut_assigner, a.actif, a.last_login, a.created_at,
                COUNT(d.id) FILTER (WHERE d.statut NOT IN ('traite', 'cloture', 'rejete')) AS demandes_assignees,
                COUNT(d.id) FILTER (WHERE d.statut = 'traite') AS demandes_traitees
            FROM demandes_services_agents a
            LEFT JOIN demandes_citoyens d ON d.agent_service_id = a.id
            WHERE a.id = :id
            GROUP BY a.id
        """),
        {"id": agent_id},
    )
    a = result.mappings().first()

    return AgentListItem(
        id=str(a["id"]),
        email=a["email"],
        nom=a["nom"],
        prenom=a["prenom"],
        nom_complet=a["nom_complet"],
        telephone=a["telephone"],
        role=a["role"],
        peut_assigner=a["peut_assigner"],
        actif=a["actif"],
        last_login=a["last_login"],
        created_at=a["created_at"],
        demandes_assignees=a["demandes_assignees"],
        demandes_traitees=a["demandes_traitees"],
    )


@router.post("/agents/{agent_id}/reset-password")
async def reset_agent_password(
    agent_id: str,
    data: AgentResetPassword,
    current_agent: dict = Depends(require_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Réinitialiser le mot de passe d'un agent (responsable uniquement)."""
    service_id = str(current_agent["service_id"])

    # Vérifier que l'agent appartient au service
    result = await db.execute(
        text("SELECT id FROM demandes_services_agents WHERE id = :id AND service_id = :service_id"),
        {"id": agent_id, "service_id": service_id},
    )
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent non trouvé dans votre service",
        )

    # Mettre à jour le mot de passe
    password_hash = get_password_hash(data.new_password)
    await db.execute(
        text("UPDATE demandes_services_agents SET password_hash = :hash WHERE id = :id"),
        {"hash": password_hash, "id": agent_id},
    )
    await db.commit()

    return {"message": "Mot de passe réinitialisé"}


@router.delete("/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    current_agent: dict = Depends(require_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Désactiver un agent (responsable uniquement). Ne supprime pas, désactive."""
    service_id = str(current_agent["service_id"])

    # Vérifier que l'agent appartient au service
    result = await db.execute(
        text("SELECT id FROM demandes_services_agents WHERE id = :id AND service_id = :service_id"),
        {"id": agent_id, "service_id": service_id},
    )
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent non trouvé dans votre service",
        )

    # On ne peut pas se désactiver soi-même
    if agent_id == str(current_agent["id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas vous désactiver vous-même",
        )

    # Désactiver l'agent (soft delete)
    await db.execute(
        text("UPDATE demandes_services_agents SET actif = FALSE WHERE id = :id"),
        {"id": agent_id},
    )

    # Retirer ses demandes assignées
    await db.execute(
        text("UPDATE demandes_citoyens SET agent_service_id = NULL WHERE agent_service_id = :id"),
        {"id": agent_id},
    )
    await db.commit()

    return {"message": "Agent désactivé"}


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTIQUES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/stats", response_model=ServiceStats)
async def get_stats(
    current_agent: dict = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Statistiques du service (super_admin voit tout)."""
    is_super_admin = current_agent.get("is_super_admin", False)
    service_id = current_agent.get("service_id")

    # Super admin voit toutes les stats
    if is_super_admin:
        where_clause = "1=1"
        params = {}
    elif service_id:
        where_clause = "service_assigne_id = CAST(:service_id AS uuid)"
        params = {"service_id": str(service_id)}
    else:
        # Pas de service = stats vides
        return ServiceStats(
            total_demandes=0, en_attente=0, en_cours=0, traitees=0,
            traitees_jour=0, traitees_semaine=0, traitees_mois=0,
            urgentes=0, en_retard=0, delai_moyen_heures=None
        )

    # Stats globales
    result = await db.execute(
        text(f"""
            SELECT
                COUNT(*) AS total_demandes,
                COUNT(*) FILTER (WHERE statut IN ('nouveau', 'en_moderation', 'envoye', 'accepte')) AS en_attente,
                COUNT(*) FILTER (WHERE statut IN ('en_cours', 'planifie')) AS en_cours,
                COUNT(*) FILTER (WHERE statut = 'traite') AS traitees,
                COUNT(*) FILTER (WHERE statut = 'traite' AND date_resolution >= CURRENT_DATE) AS traitees_jour,
                COUNT(*) FILTER (WHERE statut = 'traite' AND date_resolution >= CURRENT_DATE - INTERVAL '7 days') AS traitees_semaine,
                COUNT(*) FILTER (WHERE statut = 'traite' AND date_resolution >= CURRENT_DATE - INTERVAL '30 days') AS traitees_mois,
                COUNT(*) FILTER (WHERE priorite = 'urgente' AND statut NOT IN ('traite', 'cloture', 'rejete')) AS urgentes,
                COUNT(*) FILTER (WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
                                 AND statut NOT IN ('traite', 'cloture', 'rejete')
                                 AND date_prise_en_charge IS NULL) AS en_retard,
                AVG(EXTRACT(EPOCH FROM (date_resolution - created_at))/3600)
                    FILTER (WHERE date_resolution IS NOT NULL) AS delai_moyen_heures
            FROM demandes_citoyens
            WHERE {where_clause}
        """),
        params,
    )
    stats = result.mappings().first()

    return ServiceStats(
        total_demandes=stats["total_demandes"] or 0,
        en_attente=stats["en_attente"] or 0,
        en_cours=stats["en_cours"] or 0,
        traitees=stats["traitees"] or 0,
        traitees_jour=stats["traitees_jour"] or 0,
        traitees_semaine=stats["traitees_semaine"] or 0,
        traitees_mois=stats["traitees_mois"] or 0,
        urgentes=stats["urgentes"] or 0,
        en_retard=stats["en_retard"] or 0,
        delai_moyen_heures=round(stats["delai_moyen_heures"], 1) if stats["delai_moyen_heures"] else None,
    )


@router.get("/stats/agents", response_model=List[ServiceStatsAgent])
async def get_stats_agents(
    current_agent: dict = Depends(require_responsable),
    db: AsyncSession = Depends(get_db),
):
    """Statistiques par agent (responsable uniquement)."""
    service_id = str(current_agent["service_id"])

    result = await db.execute(
        text("""
            SELECT
                a.id AS agent_id,
                COALESCE(a.nom || ' ' || a.prenom, a.email) AS agent_nom,
                COUNT(d.id) FILTER (WHERE d.statut NOT IN ('traite', 'cloture', 'rejete')) AS assignees,
                COUNT(d.id) FILTER (WHERE d.statut IN ('en_cours', 'planifie')) AS en_cours,
                COUNT(d.id) FILTER (WHERE d.statut = 'traite') AS traitees,
                AVG(EXTRACT(EPOCH FROM (d.date_resolution - d.created_at))/3600)
                    FILTER (WHERE d.date_resolution IS NOT NULL) AS delai_moyen_heures
            FROM demandes_services_agents a
            LEFT JOIN demandes_citoyens d ON d.agent_service_id = a.id
            WHERE a.service_id = :service_id AND a.actif = TRUE
            GROUP BY a.id
            ORDER BY traitees DESC
        """),
        {"service_id": service_id},
    )
    stats = result.mappings().all()

    return [
        ServiceStatsAgent(
            agent_id=str(s["agent_id"]),
            agent_nom=s["agent_nom"],
            assignees=s["assignees"] or 0,
            en_cours=s["en_cours"] or 0,
            traitees=s["traitees"] or 0,
            delai_moyen_heures=round(s["delai_moyen_heures"], 1) if s["delai_moyen_heures"] else None,
        )
        for s in stats
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# PHOTOS D'INTERVENTION
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/demandes/{demande_id}/photos")
async def upload_intervention_photo(
    demande_id: str,
    file: UploadFile = File(...),
    current_agent: dict = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Upload une photo d'intervention pour une demande."""
    import os
    import uuid
    from PIL import Image
    from io import BytesIO

    service_id = str(current_agent["service_id"])

    # Vérifier que la demande appartient au service
    result = await db.execute(
        text("SELECT id, photos_intervention FROM demandes_citoyens WHERE id = CAST(:id AS uuid) AND service_assigne_id = CAST(:service_id AS uuid)"),
        {"id": demande_id, "service_id": service_id},
    )
    demande = result.mappings().first()
    if not demande:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée ou non assignée à votre service",
        )

    # Valider le fichier - content-type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier doit être une image",
        )

    # Valider l'extension
    from pathlib import PurePosixPath
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    original_ext = PurePosixPath(file.filename).suffix.lower() if file.filename else ".jpg"
    if original_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extension non autorisée: {original_ext}",
        )

    # Lire et compresser l'image
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'image ne doit pas dépasser 10 Mo",
        )

    try:
        # PIL.Image.open valide que c'est une vraie image
        img = Image.open(BytesIO(content))

        # Convertir en RGB si nécessaire
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Redimensionner si trop grand
        max_size = (1280, 960)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Sauvegarder en JPEG
        output = BytesIO()
        img.save(output, format="JPEG", quality=85, optimize=True)
        compressed_content = output.getvalue()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier n'est pas une image valide",
        )

    # Générer un nom de fichier unique
    from datetime import datetime
    now = datetime.utcnow()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    filename = f"{uuid.uuid4()}.jpg"

    # Créer le répertoire (utiliser le volume Docker monté)
    storage_path = "/app/photos/interventions"
    dir_path = os.path.join(storage_path, year, month)
    os.makedirs(dir_path, exist_ok=True)

    # Sauvegarder le fichier
    file_path = os.path.join(dir_path, filename)
    with open(file_path, "wb") as f:
        f.write(compressed_content)

    # URL relative pour stockage en DB (via le router services)
    photo_url = f"/api/services/photos/interventions/{year}/{month}/{filename}"

    # Ajouter l'URL à photos_intervention
    current_photos = demande["photos_intervention"] or []
    if isinstance(current_photos, str):
        current_photos = json.loads(current_photos)
    current_photos.append(photo_url)

    await db.execute(
        text("UPDATE demandes_citoyens SET photos_intervention = :photos WHERE id = CAST(:id AS uuid)"),
        {"id": demande_id, "photos": json.dumps(current_photos)},
    )
    await db.commit()

    return {
        "success": True,
        "url": photo_url,
        "total_photos": len(current_photos),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT POUR SERVIR LES PHOTOS D'INTERVENTION
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/photos/interventions/{year}/{month}/{filename}")
async def get_intervention_photo(year: str, month: str, filename: str):
    """Sert une photo d'intervention."""
    import os
    from pathlib import Path

    # Protection path traversal
    if not filename or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")
    if not year.isdigit() or not month.isdigit():
        raise HTTPException(status_code=400, detail="Paramètres invalides")

    # Vérifier que c'est bien une image
    if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format de fichier non autorisé"
        )

    # Construire le chemin du fichier
    base_path = Path("/app/photos/interventions")
    file_path = base_path / year / month / filename

    # Vérifier que le chemin résolu reste dans le dossier autorisé
    if not file_path.resolve().is_relative_to(base_path.resolve()):
        raise HTTPException(status_code=400, detail="Chemin invalide")

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo non trouvée"
        )

    return FileResponse(
        str(file_path),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"}
    )
