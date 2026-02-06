"""
Router pour les demandes citoyennes.
GéoClic Suite V14 - Phase 3 Portail Citoyen

Endpoints:
- /api/demandes/categories - Gestion des catégories
- /api/demandes - CRUD demandes (agents)
- /api/demandes/public - API publique citoyens
- /api/demandes/templates - Templates de réponses
- /api/demandes/quartiers - Gestion des quartiers
- /api/demandes/stats - Statistiques
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime, date, timedelta
from pathlib import Path
from PIL import Image
import json
import hashlib
import httpx
import uuid
import io

from database import get_db
from routers.auth import get_current_user, get_current_user_optional
from services.email_service import get_email_service_for_project
from services.notifications import (
    notify_citizen_demande_created,
    notify_citizen_status_changed,
    notify_service_new_demande,
    notify_agent_new_message,
    schedule_intervention_reminder,
)
from config import settings
from schemas.demandes import (
    # Catégories
    CategorieCreate, CategorieUpdate, CategorieResponse, CategorieArbre,
    # Demandes
    DemandeCreatePublic, DemandeCreateBackoffice, DemandeUpdateBackoffice, DemandeUpdateAgent, DemandeResponse,
    DemandeResponsePublic, DemandeListResponse, DemandeStatut, DemandePriorite,
    # Historique
    HistoriqueCreate, HistoriqueResponse, HistoriqueAction,
    # Templates
    TemplateCreate, TemplateUpdate, TemplateResponse,
    # Quartiers
    QuartierCreate, QuartierResponse, QuartierWithGeometry, Coordonnees,
    # Stats
    StatsResponse, StatsGlobales, StatsParCategorie, StatsParQuartier, StatsParPeriode,
    DashboardStats, StatsParService, DemandePrioritaire,
    ComparaisonPeriode, DistributionStatuts,
    # Email
    EmailConfigCreate, EmailConfigResponse,
    # IRIS
    IRISImportRequest, IRISImportResponse,
    # Doublons
    DoublonCheck, DoublonPotentiel, DoublonCheckResponse, DoublonMarquer,
    # Services
    ServiceCreate, ServiceUpdate, ServiceResponse, ServiceStatsResponse,
    ServiceAgentCreate, ServiceAgentUpdate, ServiceAgentResponse, ServiceAgentResetPassword,
    # Messages tchat
    MessageCreate, MessageResponse, MessageSenderType,
)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def hash_ip(ip: str) -> str:
    """Hash une adresse IP pour l'anti-abus."""
    return hashlib.sha256(ip.encode()).hexdigest()


def coords_to_wkt_point(lat: float, lng: float) -> str:
    """Convertit des coordonnées en WKT Point."""
    return f"POINT({lng} {lat})"


def polygon_coords_to_wkt(coords: List[Coordonnees]) -> str:
    """Convertit une liste de coordonnées en WKT Polygon."""
    points = ", ".join([f"{c.longitude} {c.latitude}" for c in coords])
    # Fermer le polygone
    if coords[0].latitude != coords[-1].latitude or coords[0].longitude != coords[-1].longitude:
        points += f", {coords[0].longitude} {coords[0].latitude}"
    return f"POLYGON(({points}))"


# ═══════════════════════════════════════════════════════════════════════════════
# TÂCHES EMAIL EN ARRIÈRE-PLAN
# ═══════════════════════════════════════════════════════════════════════════════

async def send_demande_creation_email(
    db_url: str,
    project_id: str,
    demande_data: dict,
):
    """Envoie un email de confirmation de création (tâche background)."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    try:
        engine = create_async_engine(db_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            # Utiliser le nouveau système de notifications
            await notify_citizen_demande_created(db, demande_data)
    except Exception as e:
        print(f"Erreur envoi email création: {e}")


async def send_demande_status_email(
    db_url: str,
    project_id: str,
    demande_data: dict,
    nouveau_statut: str,
    commentaire: Optional[str] = None,
):
    """Envoie un email de changement de statut (tâche background)."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    try:
        engine = create_async_engine(db_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as db:
            # Utiliser le nouveau système de notifications
            await notify_citizen_status_changed(db, demande_data, nouveau_statut, commentaire)
    except Exception as e:
        print(f"Erreur envoi email statut: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# CATÉGORIES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/categories", response_model=List[CategorieResponse])
async def list_categories(
    project_id: Optional[str] = Query(None, description="UUID du projet (optionnel)"),
    actif_only: bool = Query(True, description="Uniquement les catégories actives"),
    db: AsyncSession = Depends(get_db),
):
    """Liste les catégories de demandes pour un projet ou toutes si non spécifié."""
    params = {}
    conditions = []

    if project_id:
        conditions.append("project_id = :project_id")
        params["project_id"] = project_id

    if actif_only:
        conditions.append("actif = TRUE")

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT id, project_id, parent_id, nom, description, icone, couleur,
               actif, ordre_affichage, moderation_requise, service_defaut_id,
               delai_traitement_jours, photo_obligatoire, photo_max_count,
               champs_config, created_at, updated_at
        FROM demandes_categories
        {where_clause}
        ORDER BY ordre_affichage, nom
    """

    result = await db.execute(text(query), params)
    rows = result.fetchall()

    categories = []
    for row in rows:
        categories.append(CategorieResponse(
            id=str(row.id),
            project_id=str(row.project_id),
            parent_id=str(row.parent_id) if row.parent_id else None,
            nom=row.nom,
            description=row.description,
            icone=row.icone,
            couleur=row.couleur,
            actif=row.actif,
            ordre_affichage=row.ordre_affichage,
            moderation_requise=row.moderation_requise,
            service_defaut_id=str(row.service_defaut_id) if row.service_defaut_id else None,
            delai_traitement_jours=row.delai_traitement_jours,
            photo_obligatoire=row.photo_obligatoire,
            photo_max_count=row.photo_max_count,
            champs_config=row.champs_config or [],
            created_at=row.created_at,
            updated_at=row.updated_at,
        ))

    return categories


@router.get("/categories/tree", response_model=List[CategorieArbre])
async def get_categories_tree(
    project_id: str = Query(..., description="UUID du projet"),
    db: AsyncSession = Depends(get_db),
):
    """Récupère les catégories en arborescence."""
    categories = await list_categories(project_id, True, db)

    # Construire l'arbre
    categories_map = {c.id: CategorieArbre(**c.model_dump(), children=[]) for c in categories}
    root_categories = []

    for cat in categories_map.values():
        if cat.parent_id and cat.parent_id in categories_map:
            categories_map[cat.parent_id].children.append(cat)
        else:
            root_categories.append(cat)

    return root_categories


@router.post("/categories", response_model=CategorieResponse)
async def create_category(
    project_id: str,
    category: CategorieCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Crée une nouvelle catégorie de demandes."""
    try:
        result = await db.execute(text("""
            INSERT INTO demandes_categories (
                project_id, parent_id, nom, description, icone, couleur,
                actif, ordre_affichage, moderation_requise, service_defaut_id,
                delai_traitement_jours, photo_obligatoire, photo_max_count, champs_config
            )
            VALUES (
                :project_id, :parent_id, :nom, :description, :icone, :couleur,
                :actif, :ordre_affichage, :moderation_requise, :service_defaut_id,
                :delai_traitement_jours, :photo_obligatoire, :photo_max_count, CAST(:champs_config AS jsonb)
            )
            RETURNING id, project_id, parent_id, nom, description, icone, couleur,
                      actif, ordre_affichage, moderation_requise, service_defaut_id,
                      delai_traitement_jours, photo_obligatoire, photo_max_count,
                      champs_config, created_at, updated_at
        """), {
            "project_id": project_id,
            "parent_id": category.parent_id,
            "nom": category.nom,
            "description": category.description,
            "icone": category.icone,
            "couleur": category.couleur,
            "actif": category.actif,
            "ordre_affichage": category.ordre_affichage,
            "moderation_requise": category.moderation_requise,
            "service_defaut_id": category.service_defaut_id,
            "delai_traitement_jours": category.delai_traitement_jours,
            "photo_obligatoire": category.photo_obligatoire,
            "photo_max_count": category.photo_max_count,
            "champs_config": json.dumps([c.model_dump() for c in category.champs_config]),
        })

        await db.commit()
        row = result.fetchone()

        return CategorieResponse(
            id=str(row.id),
            project_id=str(row.project_id),
            parent_id=str(row.parent_id) if row.parent_id else None,
            nom=row.nom,
            description=row.description,
            icone=row.icone,
            couleur=row.couleur,
            actif=row.actif,
            ordre_affichage=row.ordre_affichage,
            moderation_requise=row.moderation_requise,
            service_defaut_id=str(row.service_defaut_id) if row.service_defaut_id else None,
            delai_traitement_jours=row.delai_traitement_jours,
            photo_obligatoire=row.photo_obligatoire,
            photo_max_count=row.photo_max_count,
            champs_config=row.champs_config or [],
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur création catégorie: {str(e)}",
        )


@router.put("/categories/{category_id}", response_model=CategorieResponse)
async def update_category(
    category_id: str,
    category: CategorieUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Met à jour une catégorie."""
    updates = []
    params = {"id": category_id}

    for field, value in category.model_dump(exclude_unset=True).items():
        if field == "champs_config" and value is not None:
            updates.append(f"{field} = CAST(:{field} AS jsonb)")
            params[field] = json.dumps([c.model_dump() if hasattr(c, 'model_dump') else c for c in value])
        else:
            updates.append(f"{field} = :{field}")
            params[field] = value

    if not updates:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

    updates.append("updated_at = CURRENT_TIMESTAMP")

    query = f"""
        UPDATE demandes_categories
        SET {', '.join(updates)}
        WHERE id = :id
        RETURNING id, project_id, parent_id, nom, description, icone, couleur,
                  actif, ordre_affichage, moderation_requise, service_defaut_id,
                  delai_traitement_jours, photo_obligatoire, photo_max_count,
                  champs_config, created_at, updated_at
    """

    try:
        result = await db.execute(text(query), params)
        await db.commit()
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Catégorie non trouvée")

        return CategorieResponse(
            id=str(row.id),
            project_id=str(row.project_id),
            parent_id=str(row.parent_id) if row.parent_id else None,
            nom=row.nom,
            description=row.description,
            icone=row.icone,
            couleur=row.couleur,
            actif=row.actif,
            ordre_affichage=row.ordre_affichage,
            moderation_requise=row.moderation_requise,
            service_defaut_id=str(row.service_defaut_id) if row.service_defaut_id else None,
            delai_traitement_jours=row.delai_traitement_jours,
            photo_obligatoire=row.photo_obligatoire,
            photo_max_count=row.photo_max_count,
            champs_config=row.champs_config or [],
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Supprime une catégorie (si pas de demandes liées)."""
    # Vérifier s'il y a des demandes
    check = await db.execute(text("""
        SELECT COUNT(*) FROM demandes_citoyens WHERE categorie_id = :id
    """), {"id": category_id})
    count = check.scalar()

    if count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de supprimer: {count} demandes liées. Désactivez plutôt.",
        )

    result = await db.execute(text("""
        DELETE FROM demandes_categories WHERE id = :id RETURNING id
    """), {"id": category_id})

    await db.commit()

    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Catégorie non trouvée")

    return {"success": True, "deleted_id": category_id}


# ═══════════════════════════════════════════════════════════════════════════════
# DEMANDES - API PUBLIQUE (Citoyens)
# ═══════════════════════════════════════════════════════════════════════════════

def get_demandes_storage_path() -> Path:
    """Génère le chemin de stockage pour les photos de demandes citoyennes."""
    now = datetime.now()
    path = Path(settings.photo_storage_path) / "demandes" / str(now.year) / f"{now.month:02d}"
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        print(f"Permission denied creating photo directory {path}: {e}")
        # Fallback: essayer le répertoire de base s'il existe déjà
        base_path = Path(settings.photo_storage_path) / "demandes"
        if base_path.exists():
            path = base_path
        else:
            raise
    return path


def resize_image(image_data: bytes, max_width: int = 720, max_height: int = 576) -> bytes:
    """Redimensionne une image en conservant les proportions."""
    img = Image.open(io.BytesIO(image_data))

    # Convertir en RGB si nécessaire (pour les PNG avec transparence)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Calculer les nouvelles dimensions en conservant les proportions
    width, height = img.size
    if width > max_width or height > max_height:
        ratio = min(max_width / width, max_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Sauvegarder en JPEG
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85, optimize=True)
    return buffer.getvalue()


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@router.post("/public/photos/upload")
async def upload_photo_public(
    file: UploadFile = File(...),
):
    """
    Upload une photo pour une demande citoyenne.
    API publique sans authentification.
    Les photos sont redimensionnées à 720x576 max.
    """
    try:
        # Vérifier le type de fichier (header)
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Le fichier doit être une image")

        # Vérifier l'extension
        from pathlib import PurePosixPath
        original_ext = PurePosixPath(file.filename).suffix.lower() if file.filename else ".jpg"
        if original_ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Extension non autorisée: {original_ext}. Extensions acceptées: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
            )

        # Lire le contenu
        content = await file.read()
        file_size = len(content)

        # Vérifier la taille (max 10 Mo avant compression)
        max_size = 10 * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=400,
                detail="Image trop volumineuse (max 10 Mo)",
            )

        try:
            # Redimensionner l'image (valide aussi que c'est une vraie image via PIL)
            resized_content = resize_image(content, max_width=720, max_height=576)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Le fichier n'est pas une image valide")

        # Générer les chemins
        photo_id = str(uuid.uuid4())
        now = datetime.now()
        storage_path = get_demandes_storage_path()
        filename = f"{photo_id}.jpg"

        file_path = storage_path / filename

        # Sauvegarder l'image redimensionnée
        with open(file_path, "wb") as f:
            f.write(resized_content)

        # Construire l'URL
        photo_url = f"/api/photos/demandes/{now.year}/{now.month:02d}/{filename}"

        return {
            "success": True,
            "url": photo_url,
            "id": photo_id,
            "size_bytes": len(resized_content),
        }

    except HTTPException:
        raise
    except PermissionError as e:
        print(f"Permission error in upload_photo_public: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur de permissions du serveur. Contactez l'administrateur."
        )
    except Exception as e:
        print(f"Error in upload_photo_public: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'upload")


ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".odt", ".xls", ".xlsx", ".txt", ".csv"}


@router.post("/upload/fichier")
async def upload_fichier(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload un fichier (photo ou document) pour une demande backoffice.
    Endpoint authentifié. Accepte images et documents (PDF, DOC, etc.).
    """
    from pathlib import PurePosixPath
    original_ext = PurePosixPath(file.filename).suffix.lower() if file.filename else ""
    original_name = file.filename or "fichier"

    is_image = original_ext in ALLOWED_IMAGE_EXTENSIONS
    is_document = original_ext in ALLOWED_DOCUMENT_EXTENSIONS

    if not is_image and not is_document:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non autorisé: {original_ext}. "
                   f"Images: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}. "
                   f"Documents: {', '.join(ALLOWED_DOCUMENT_EXTENSIONS)}"
        )

    content = await file.read()
    file_size = len(content)

    max_size = 20 * 1024 * 1024  # 20 Mo pour les documents
    if file_size > max_size:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 20 Mo)")

    file_id = str(uuid.uuid4())
    now = datetime.now()
    storage_path = get_demandes_storage_path()

    if is_image:
        try:
            resized_content = resize_image(content)
        except Exception:
            raise HTTPException(status_code=400, detail="Le fichier n'est pas une image valide")
        filename = f"{file_id}.jpg"
        file_path = storage_path / filename
        with open(file_path, "wb") as f:
            f.write(resized_content)
        file_url = f"/api/photos/demandes/{now.year}/{now.month:02d}/{filename}"
        return {
            "success": True,
            "url": file_url,
            "type": "image",
            "original_name": original_name,
            "size_bytes": len(resized_content),
        }
    else:
        # Document: sauvegarder tel quel avec nom sécurisé
        safe_ext = original_ext
        filename = f"{file_id}{safe_ext}"
        file_path = storage_path / filename
        with open(file_path, "wb") as f:
            f.write(content)
        file_url = f"/api/photos/demandes/{now.year}/{now.month:02d}/{filename}"
        return {
            "success": True,
            "url": file_url,
            "type": "document",
            "original_name": original_name,
            "size_bytes": file_size,
        }


@router.post("/backoffice/creer", response_model=DemandeResponse)
async def create_demande_backoffice(
    project_id: str,
    demande: DemandeCreateBackoffice,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Crée une demande depuis le backoffice (signalement reçu par mail, téléphone, etc.).
    Endpoint authentifié réservé aux agents.
    """
    # Vérifier que l'utilisateur a le droit
    if not current_user.get("is_super_admin") and current_user.get("role_demandes") == "aucun":
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    # Vérifier que la catégorie existe et est active
    cat_result = await db.execute(text("""
        SELECT id, moderation_requise, project_id
        FROM demandes_categories
        WHERE id = :id AND actif = TRUE
    """), {"id": demande.categorie_id})
    categorie = cat_result.fetchone()

    if not categorie:
        raise HTTPException(status_code=400, detail="Catégorie invalide ou inactive")

    # Pas de modération pour les demandes backoffice (déjà vérifiées par l'agent)
    statut_initial = "nouveau"

    # Construire la géométrie
    geom_wkt = None
    if demande.coordonnees:
        geom_wkt = coords_to_wkt_point(
            demande.coordonnees.latitude,
            demande.coordonnees.longitude
        )

    # Combiner photos et documents dans le champ photos (JSONB)
    all_files = list(demande.photos) + list(demande.documents)

    priorite = demande.priorite.value if demande.priorite else "normale"

    try:
        result = await db.execute(text("""
            INSERT INTO demandes_citoyens (
                project_id, categorie_id,
                declarant_email, declarant_telephone, declarant_nom,
                description, photos,
                geom, adresse_approximative,
                statut, source, priorite
            )
            VALUES (
                :project_id, :categorie_id,
                :email, :telephone, :nom,
                :description, CAST(:photos AS jsonb),
                ST_GeomFromText(:geom, 4326), :adresse,
                :statut, :source, :priorite
            )
            RETURNING id, numero_suivi, statut, priorite, created_at, updated_at
        """), {
            "project_id": project_id,
            "categorie_id": demande.categorie_id,
            "email": demande.declarant_email or "",
            "telephone": demande.declarant_telephone,
            "nom": demande.declarant_nom,
            "description": demande.description,
            "photos": json.dumps(all_files),
            "geom": geom_wkt,
            "adresse": demande.adresse_approximative,
            "statut": statut_initial,
            "source": demande.source.value,
            "priorite": priorite,
        })

        await db.commit()
        row = result.fetchone()

        # Créer l'entrée historique avec l'agent
        agent_name = f"{current_user.get('prenom', '')} {current_user.get('nom', '')}".strip() or current_user.get('email', 'Agent')
        commentaire_hist = f"Demande créée par {agent_name} (source: {demande.source.value})"
        if demande.note_interne:
            commentaire_hist += f"\nNote: {demande.note_interne}"

        await db.execute(text("""
            INSERT INTO demandes_historique (demande_id, agent_id, action, nouveau_statut, commentaire)
            VALUES (:demande_id, CAST(:agent_id AS uuid), 'creation', :statut, :commentaire)
        """), {
            "demande_id": row.id,
            "agent_id": str(current_user["id"]),
            "statut": statut_initial,
            "commentaire": commentaire_hist,
        })
        await db.commit()

        # Envoyer email de confirmation si email du déclarant fourni
        if demande.declarant_email:
            cat_name_result = await db.execute(text("""
                SELECT nom FROM demandes_categories WHERE id = :id
            """), {"id": demande.categorie_id})
            cat_name = cat_name_result.scalar()

            demande_data = {
                "numero_suivi": row.numero_suivi,
                "description": demande.description,
                "declarant_email": demande.declarant_email,
                "declarant_nom": demande.declarant_nom,
                "declarant_langue": "fr",
                "categorie_nom": cat_name,
            }
            background_tasks.add_task(
                send_demande_creation_email,
                settings.database_url,
                project_id,
                demande_data,
            )

        # Retourner la demande complète
        demande_result = await db.execute(text("""
            SELECT d.*, c.nom as categorie_nom, c.icone as categorie_icone, c.couleur as categorie_couleur,
                   cp.nom as categorie_parent_nom,
                   s.nom as service_assigne_nom, s.couleur as service_assigne_couleur,
                   ST_Y(d.geom) as latitude, ST_X(d.geom) as longitude
            FROM demandes_citoyens d
            LEFT JOIN demandes_categories c ON d.categorie_id = c.id
            LEFT JOIN demandes_categories cp ON c.parent_id = cp.id
            LEFT JOIN demandes_services s ON d.service_assigne_id = s.id
            WHERE d.id = :id
        """), {"id": row.id})
        demande_row = demande_result.fetchone()

        photos_list = json.loads(demande_row.photos) if demande_row.photos else []
        # Séparer photos et documents
        photo_urls = [f for f in photos_list if any(f.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
        doc_urls = [f for f in photos_list if not any(f.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'))]

        return DemandeResponse(
            id=str(demande_row.id),
            project_id=str(demande_row.project_id),
            numero_suivi=demande_row.numero_suivi,
            categorie_id=str(demande_row.categorie_id),
            categorie_nom=demande_row.categorie_nom,
            categorie_icone=demande_row.categorie_icone,
            categorie_couleur=demande_row.categorie_couleur,
            categorie_parent_nom=demande_row.categorie_parent_nom,
            declarant_email=demande_row.declarant_email or "",
            declarant_telephone=demande_row.declarant_telephone,
            declarant_nom=demande_row.declarant_nom,
            description=demande_row.description,
            photos=photo_urls,
            documents=doc_urls,
            latitude=demande_row.latitude,
            longitude=demande_row.longitude,
            adresse_approximative=demande_row.adresse_approximative,
            statut=DemandeStatut(demande_row.statut),
            priorite=DemandePriorite(demande_row.priorite),
            source=demande_row.source or "backoffice",
            created_at=demande_row.created_at,
            updated_at=demande_row.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import logging
        logging.getLogger(__name__).error(f"Erreur création demande backoffice: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur création demande: {str(e)}")


@router.put("/backoffice/{demande_id}")
async def update_demande_backoffice(
    demande_id: str,
    update: DemandeUpdateBackoffice,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Modifie une demande depuis le backoffice.
    Permet de modifier tous les champs éditables.
    """
    if not current_user.get("is_super_admin") and current_user.get("role_demandes") == "aucun":
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    # Vérifier que la demande existe
    check = await db.execute(text("""
        SELECT id FROM demandes_citoyens WHERE id = CAST(:id AS uuid)
    """), {"id": demande_id})
    if not check.fetchone():
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    # Construire dynamiquement les champs à mettre à jour
    ALLOWED_COLS = {
        "categorie_id", "declarant_email", "declarant_telephone", "declarant_nom",
        "description", "adresse_approximative", "source", "priorite",
    }
    updates = {}
    set_clauses = []

    data = update.dict(exclude_none=True)

    for col in ALLOWED_COLS:
        if col in data:
            val = data[col]
            if hasattr(val, 'value'):
                val = val.value
            updates[col] = val
            set_clauses.append(f"{col} = :{col}")

    # Gestion photos + documents -> champ photos JSONB
    if update.photos is not None or update.documents is not None:
        photos = update.photos if update.photos is not None else []
        documents = update.documents if update.documents is not None else []
        all_files = list(photos) + list(documents)
        updates["photos"] = json.dumps(all_files)
        set_clauses.append("photos = CAST(:photos AS jsonb)")

    # Gestion coordonnées -> geom
    if update.coordonnees is not None:
        wkt = coords_to_wkt_point(update.coordonnees.latitude, update.coordonnees.longitude)
        updates["geom_wkt"] = wkt
        set_clauses.append("geom = ST_GeomFromText(:geom_wkt, 4326)")

    if not set_clauses:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")

    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    updates["demande_id"] = demande_id

    query = f"UPDATE demandes_citoyens SET {', '.join(set_clauses)} WHERE id = CAST(:demande_id AS uuid)"

    try:
        await db.execute(text(query), updates)

        # Historique
        agent_name = f"{current_user.get('prenom', '')} {current_user.get('nom', '')}".strip() or current_user.get('email', 'Agent')
        champs_modifies = [c for c in data.keys() if c not in ('coordonnees',)] + (["localisation"] if update.coordonnees else [])
        commentaire = f"Demande modifiée par {agent_name} (champs: {', '.join(champs_modifies)})"

        await db.execute(text("""
            INSERT INTO demandes_historique (demande_id, agent_id, action, commentaire)
            VALUES (CAST(:demande_id AS uuid), CAST(:agent_id AS uuid), 'modification', :commentaire)
        """), {
            "demande_id": demande_id,
            "agent_id": str(current_user["id"]),
            "commentaire": commentaire,
        })
        await db.commit()

        # Retourner la demande mise à jour
        result = await db.execute(text("""
            SELECT d.*, c.nom as categorie_nom, c.icone as categorie_icone, c.couleur as categorie_couleur,
                   cp.nom as categorie_parent_nom,
                   s.nom as service_assigne_nom, s.couleur as service_assigne_couleur,
                   ST_Y(d.geom) as latitude, ST_X(d.geom) as longitude
            FROM demandes_citoyens d
            LEFT JOIN demandes_categories c ON d.categorie_id = c.id
            LEFT JOIN demandes_categories cp ON c.parent_id = cp.id
            LEFT JOIN demandes_services s ON d.service_assigne_id = s.id
            WHERE d.id = CAST(:id AS uuid)
        """), {"id": demande_id})
        row = result.fetchone()

        photos_list = json.loads(row.photos) if row.photos and isinstance(row.photos, str) else (row.photos or [])
        photo_urls = [f for f in photos_list if any(f.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
        doc_urls = [f for f in photos_list if isinstance(f, str) and not any(f.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'))]

        return {
            "success": True,
            "id": str(row.id),
            "numero_suivi": row.numero_suivi,
            "photos": photo_urls,
            "documents": doc_urls,
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import logging
        logging.getLogger(__name__).error(f"Erreur modification demande backoffice: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur modification: {str(e)}")


@router.post("/public/demandes", response_model=DemandeResponsePublic)
async def create_demande_public(
    project_id: str,
    demande: DemandeCreatePublic,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    # Note: pas d'auth requise pour les citoyens
):
    """
    Crée une nouvelle demande citoyenne.
    API publique sans authentification (mais avec CAPTCHA).
    """
    # TODO: Vérifier le CAPTCHA
    # if demande.captcha_token:
    #     verify_captcha(demande.captcha_token)

    # Vérifier le rate limit (optionnel - skip si la fonction n'existe pas)
    try:
        result = await db.execute(text("""
            SELECT check_rate_limit(:email, 'email', 5)
        """), {"email": demande.declarant_email})
        allowed = result.scalar()

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Limite quotidienne de demandes atteinte. Réessayez demain.",
            )
    except Exception as e:
        # Si la fonction check_rate_limit n'existe pas, on continue sans rate limiting
        print(f"Rate limit check skipped: {e}")

    # Vérifier que la catégorie existe et est active
    cat_result = await db.execute(text("""
        SELECT id, moderation_requise, project_id
        FROM demandes_categories
        WHERE id = :id AND actif = TRUE
    """), {"id": demande.categorie_id})
    categorie = cat_result.fetchone()

    if not categorie:
        raise HTTPException(status_code=400, detail="Catégorie invalide ou inactive")

    # Déterminer le statut initial
    statut_initial = "en_moderation" if categorie.moderation_requise else "nouveau"

    # Construire la géométrie
    geom_wkt = None
    if demande.coordonnees:
        geom_wkt = coords_to_wkt_point(
            demande.coordonnees.latitude,
            demande.coordonnees.longitude
        )

    try:
        result = await db.execute(text("""
            INSERT INTO demandes_citoyens (
                project_id, categorie_id,
                declarant_email, declarant_telephone, declarant_nom, declarant_langue,
                description, champs_supplementaires, photos,
                geom, adresse_approximative, equipement_id,
                statut, source
            )
            VALUES (
                :project_id, :categorie_id,
                :email, :telephone, :nom, :langue,
                :description, CAST(:champs AS jsonb), CAST(:photos AS jsonb),
                ST_GeomFromText(:geom, 4326), :adresse, :equipement_id,
                :statut, :source
            )
            RETURNING id, numero_suivi, statut, created_at, updated_at
        """), {
            "project_id": project_id,
            "categorie_id": demande.categorie_id,
            "email": demande.declarant_email,
            "telephone": demande.declarant_telephone,
            "nom": demande.declarant_nom,
            "langue": demande.declarant_langue,
            "description": demande.description,
            "champs": json.dumps(demande.champs_supplementaires),
            "photos": json.dumps(demande.photos),
            "geom": geom_wkt,
            "adresse": demande.adresse_approximative,
            "equipement_id": demande.equipement_id,
            "statut": statut_initial,
            "source": demande.source.value,
        })

        await db.commit()
        row = result.fetchone()

        # Créer l'entrée historique
        await db.execute(text("""
            INSERT INTO demandes_historique (demande_id, action, nouveau_statut, commentaire)
            VALUES (:demande_id, 'creation', :statut, 'Demande créée via le portail citoyen')
        """), {"demande_id": row.id, "statut": statut_initial})
        await db.commit()

        # Récupérer le nom de la catégorie pour la réponse
        cat_name_result = await db.execute(text("""
            SELECT nom FROM demandes_categories WHERE id = :id
        """), {"id": demande.categorie_id})
        cat_name = cat_name_result.scalar()

        # Envoyer email de confirmation en arrière-plan
        from config import settings
        demande_data = {
            "numero_suivi": row.numero_suivi,
            "description": demande.description,
            "declarant_email": demande.declarant_email,
            "declarant_nom": demande.declarant_nom,
            "declarant_langue": demande.declarant_langue,
            "categorie_nom": cat_name,
        }
        background_tasks.add_task(
            send_demande_creation_email,
            settings.database_url,
            project_id,
            demande_data,
        )

        return DemandeResponsePublic(
            numero_suivi=row.numero_suivi,
            statut=DemandeStatut(row.statut),
            categorie_nom=cat_name,
            description=demande.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur création demande: {str(e)}")


@router.get("/public/demandes/{numero_suivi}", response_model=DemandeResponsePublic)
async def get_demande_public(
    numero_suivi: str,
    email: str = Query(..., description="Email du déclarant pour vérification"),
    db: AsyncSession = Depends(get_db),
):
    """
    Consulte une demande par son numéro de suivi.
    Nécessite l'email du déclarant pour vérification.
    """
    result = await db.execute(text("""
        SELECT d.numero_suivi, d.statut, d.description,
               d.created_at, d.updated_at, d.date_planification, d.date_resolution,
               c.nom AS categorie_nom
        FROM demandes_citoyens d
        LEFT JOIN demandes_categories c ON d.categorie_id = c.id
        WHERE d.numero_suivi = :numero AND d.declarant_email = :email
    """), {"numero": numero_suivi, "email": email})

    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Demande non trouvée ou email incorrect",
        )

    return DemandeResponsePublic(
        numero_suivi=row.numero_suivi,
        statut=DemandeStatut(row.statut),
        categorie_nom=row.categorie_nom,
        description=row.description,
        created_at=row.created_at,
        updated_at=row.updated_at,
        date_planification=row.date_planification,
        date_resolution=row.date_resolution,
    )


@router.get("/public/demandes/{numero_suivi}/historique", response_model=List[HistoriqueResponse])
async def get_demande_historique_public(
    numero_suivi: str,
    email: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Consulte l'historique d'une demande (messages publics uniquement)."""
    # Vérifier l'accès
    check = await db.execute(text("""
        SELECT id FROM demandes_citoyens
        WHERE numero_suivi = :numero AND declarant_email = :email
    """), {"numero": numero_suivi, "email": email})

    demande = check.fetchone()
    if not demande:
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    result = await db.execute(text("""
        SELECT id, demande_id, agent_nom, action, ancien_statut, nouveau_statut,
               commentaire, email_envoye, created_at
        FROM demandes_historique
        WHERE demande_id = :demande_id AND commentaire_interne = FALSE
        ORDER BY created_at ASC
    """), {"demande_id": demande.id})

    return [
        HistoriqueResponse(
            id=str(row.id),
            demande_id=str(row.demande_id),
            agent_nom=row.agent_nom,
            action=HistoriqueAction(row.action),
            ancien_statut=row.ancien_statut,
            nouveau_statut=row.nouveau_statut,
            commentaire=row.commentaire,
            commentaire_interne=False,
            email_envoye=row.email_envoye,
            created_at=row.created_at,
        )
        for row in result.fetchall()
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# CARTE PUBLIQUE - Affichage des demandes sur la carte du portail citoyen
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/public/carte/demandes")
async def get_demandes_carte_public(
    db: AsyncSession = Depends(get_db),
):
    """
    Récupère les demandes pour affichage sur la carte publique du portail citoyen.
    Retourne un GeoJSON avec les demandes des 90 derniers jours (position, catégorie, statut).
    Aucune authentification requise - données anonymisées.
    """
    # Récupérer les demandes des 90 derniers jours avec coordonnées valides
    result = await db.execute(text("""
        SELECT
            d.id,
            d.numero_suivi,
            d.statut,
            d.created_at,
            d.photos,
            c.nom AS categorie_nom,
            c.icone AS categorie_icone,
            c.couleur AS categorie_couleur,
            ST_X(d.geom::geometry) AS longitude,
            ST_Y(d.geom::geometry) AS latitude
        FROM demandes_citoyens d
        LEFT JOIN demandes_categories c ON d.categorie_id = c.id
        WHERE d.geom IS NOT NULL
          AND d.created_at >= NOW() - INTERVAL '90 days'
        ORDER BY d.created_at DESC
        LIMIT 500
    """))

    rows = result.fetchall()

    # Construire le GeoJSON
    features = []
    for row in rows:
        # Couleur selon le statut
        statut_colors = {
            "nouveau": "#ef4444",      # Rouge
            "en_moderation": "#f97316",# Orange-Rouge
            "envoye": "#0ea5e9",       # Bleu ciel
            "accepte": "#22c55e",      # Vert
            "en_cours": "#f59e0b",     # Orange
            "planifie": "#3b82f6",     # Bleu
            "traite": "#22c55e",       # Vert
            "rejete": "#6b7280",       # Gris
            "cloture": "#10b981",      # Vert émeraude
        }

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row.longitude, row.latitude]
            },
            "properties": {
                "id": str(row.id),
                "numero_suivi": row.numero_suivi,
                "statut": row.statut,
                "statut_color": statut_colors.get(row.statut, "#6b7280"),
                "categorie_nom": row.categorie_nom or "Non catégorisé",
                "categorie_icone": row.categorie_icone or "📍",
                "categorie_couleur": row.categorie_couleur or "#6b7280",
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "photos": row.photos if row.photos else [],
            }
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features
    }


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTIQUES (AVANT les routes avec paramètres dynamiques!)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/statistiques", response_model=StatsResponse)
async def get_stats(
    project_id: Optional[str] = Query(None),
    periode: Optional[str] = Query(None, description="Période: jour, semaine, mois, annee"),
    date_debut: Optional[date] = Query(default=None),
    date_fin: Optional[date] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère les statistiques des demandes."""
    # Calcul des dates selon la période
    if periode == "jour":
        date_debut = date.today()
        date_fin = date.today()
    elif periode == "semaine":
        date_debut = date.today() - timedelta(days=7)
        date_fin = date.today()
    elif periode == "mois":
        date_debut = date.today() - timedelta(days=30)
        date_fin = date.today()
    elif periode == "annee":
        date_debut = date.today() - timedelta(days=365)
        date_fin = date.today()
    else:
        if not date_debut:
            date_debut = date.today() - timedelta(days=30)
        if not date_fin:
            date_fin = date.today()

    params = {
        "date_debut": date_debut,
        "date_fin": date_fin,
    }

    # Construire la condition project_id
    project_filter = ""
    if project_id:
        project_filter = "AND project_id = :project_id"
        params["project_id"] = project_id

    # Stats globales
    global_result = await db.execute(text(f"""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE statut = 'nouveau') AS nouvelles,
            COUNT(*) FILTER (WHERE statut IN ('en_cours', 'planifie', 'accepte', 'envoye')) AS en_cours,
            COUNT(*) FILTER (WHERE statut = 'traite') AS traitees,
            COUNT(*) FILTER (WHERE statut = 'rejete') AS rejetees,
            AVG(EXTRACT(EPOCH FROM (date_resolution - created_at))/3600)
                FILTER (WHERE date_resolution IS NOT NULL) AS temps_moyen
        FROM demandes_citoyens
        WHERE created_at >= CAST(:date_debut AS timestamp)
          AND created_at < (CAST(:date_fin AS timestamp) + INTERVAL '1 day')
          {project_filter}
    """), params)

    global_row = global_result.fetchone()

    globales = StatsGlobales(
        total=global_row.total or 0,
        nouvelles=global_row.nouvelles or 0,
        en_cours=global_row.en_cours or 0,
        traitees=global_row.traitees or 0,
        rejetees=global_row.rejetees or 0,
        temps_moyen_traitement_heures=float(global_row.temps_moyen) if global_row.temps_moyen else None,
    )

    # Stats par catégorie - seulement si project_id fourni
    par_categorie = []
    par_quartier = []
    evolution = []

    if project_id:
        cat_result = await db.execute(text("""
            SELECT
                c.id AS categorie_id,
                c.nom AS categorie_nom,
                COUNT(d.id) AS total,
                COUNT(d.id) FILTER (WHERE d.statut = 'nouveau') AS nouvelles,
                COUNT(d.id) FILTER (WHERE d.statut IN ('en_cours', 'planifie')) AS en_cours,
                COUNT(d.id) FILTER (WHERE d.statut = 'traite') AS traitees,
                AVG(EXTRACT(EPOCH FROM (d.date_resolution - d.created_at))/3600)
                    FILTER (WHERE d.date_resolution IS NOT NULL) AS temps_moyen
            FROM demandes_categories c
            LEFT JOIN demandes_citoyens d ON d.categorie_id = c.id
                AND d.created_at >= CAST(:date_debut AS timestamp)
                AND d.created_at < (CAST(:date_fin AS timestamp) + INTERVAL '1 day')
            WHERE c.project_id = :project_id AND c.actif = TRUE
            GROUP BY c.id, c.nom
            ORDER BY total DESC
        """), params)

        par_categorie = [
            StatsParCategorie(
                categorie_id=str(row.categorie_id),
                categorie_nom=row.categorie_nom,
                total=row.total or 0,
                nouvelles=row.nouvelles or 0,
                en_cours=row.en_cours or 0,
                traitees=row.traitees or 0,
                temps_moyen_heures=float(row.temps_moyen) if row.temps_moyen else None,
            )
            for row in cat_result.fetchall()
        ]

        # Stats par quartier
        quartier_result = await db.execute(text("""
            SELECT
                p.id AS quartier_id,
                p.name AS quartier_nom,
                COUNT(d.id) AS total,
                COUNT(d.id) FILTER (WHERE d.statut = 'nouveau') AS nouvelles,
                COUNT(d.id) FILTER (WHERE d.statut IN ('en_cours', 'planifie')) AS en_cours,
                COUNT(d.id) FILTER (WHERE d.statut = 'traite') AS traitees,
                AVG(EXTRACT(EPOCH FROM (d.date_resolution - d.created_at))/3600)
                    FILTER (WHERE d.date_resolution IS NOT NULL) AS temps_moyen
            FROM perimetres p
            LEFT JOIN demandes_citoyens d ON d.quartier_id = p.id
                AND d.created_at >= CAST(:date_debut AS timestamp)
                AND d.created_at < (CAST(:date_fin AS timestamp) + INTERVAL '1 day')
            WHERE p.project_id = :project_id AND p.perimetre_type = 'quartier'
            GROUP BY p.id, p.name
            ORDER BY total DESC
        """), params)

        par_quartier = [
            StatsParQuartier(
                quartier_id=str(row.quartier_id),
                quartier_nom=row.quartier_nom,
                total=row.total or 0,
                nouvelles=row.nouvelles or 0,
                en_cours=row.en_cours or 0,
                traitees=row.traitees or 0,
                temps_moyen_heures=float(row.temps_moyen) if row.temps_moyen else None,
            )
            for row in quartier_result.fetchall()
        ]

        # Évolution quotidienne
        evolution_result = await db.execute(text("""
            SELECT
                DATE(created_at) AS date_stat,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE statut = 'nouveau') AS nouvelles,
                COUNT(*) FILTER (WHERE statut = 'traite') AS traitees
            FROM demandes_citoyens
            WHERE project_id = :project_id
              AND created_at >= CAST(:date_debut AS timestamp)
              AND created_at < (CAST(:date_fin AS timestamp) + INTERVAL '1 day')
            GROUP BY DATE(created_at)
            ORDER BY date_stat
        """), params)

        evolution = [
            StatsParPeriode(
                date=row.date_stat,
                total=row.total or 0,
                nouvelles=row.nouvelles or 0,
                traitees=row.traitees or 0,
            )
            for row in evolution_result.fetchall()
        ]

    return StatsResponse(
        globales=globales,
        par_categorie=par_categorie,
        par_quartier=par_quartier,
        evolution=evolution,
        periode_debut=date_debut,
        periode_fin=date_fin,
    )


@router.get("/statistiques/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère les statistiques pour le tableau de bord."""
    # Récupérer le délai de retard depuis les paramètres (même que rappel email)
    delai_retard_jours = 2  # Valeur par défaut

    # Vérifier si la table demandes_settings existe avant de la requêter
    table_check = await db.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = 'demandes_settings'
        )
    """))
    if table_check.scalar():
        settings_result = await db.execute(text("""
            SELECT value FROM demandes_settings WHERE key = 'reminder_hours_before'
        """))
        settings_row = settings_result.fetchone()
        if settings_row:
            delai_retard_heures = int(settings_row.value)
            delai_retard_jours = delai_retard_heures // 24 or 2

    # KPIs globaux
    kpi_result = await db.execute(text("""
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE statut IN ('nouveau', 'en_moderation')) AS nouvelles,
            COUNT(*) FILTER (WHERE priorite = 'urgente' AND statut NOT IN ('traite', 'cloture', 'rejete')) AS urgentes,
            COUNT(*) FILTER (WHERE statut = 'envoye') AS envoyees,
            COUNT(*) FILTER (WHERE statut = 'traite' AND date_resolution >= DATE_TRUNC('month', CURRENT_DATE)) AS traitees_mois,
            AVG(EXTRACT(EPOCH FROM (COALESCE(date_resolution, CURRENT_TIMESTAMP) - created_at))/86400)
                FILTER (WHERE date_resolution IS NOT NULL) AS delai_moyen
        FROM demandes_citoyens
    """))
    kpi = kpi_result.fetchone()

    # Stats par catégorie
    cat_result = await db.execute(text("""
        SELECT
            c.id AS categorie_id,
            c.nom AS categorie_nom,
            COUNT(d.id) AS total
        FROM demandes_categories c
        LEFT JOIN demandes_citoyens d ON d.categorie_id = c.id
        WHERE c.actif = TRUE
        GROUP BY c.id, c.nom
        HAVING COUNT(d.id) > 0
        ORDER BY total DESC
        LIMIT 10
    """))
    par_categorie = [
        StatsParCategorie(
            categorie_id=str(row.categorie_id),
            categorie_nom=row.categorie_nom,
            total=row.total or 0,
        )
        for row in cat_result.fetchall()
    ]

    # Stats par service
    service_result = await db.execute(text("""
        SELECT
            s.id AS service_id,
            s.nom AS service_nom,
            s.couleur AS service_couleur,
            COUNT(d.id) AS total,
            AVG(EXTRACT(EPOCH FROM (COALESCE(d.date_resolution, CURRENT_TIMESTAMP) - d.created_at))/86400)
                FILTER (WHERE d.date_resolution IS NOT NULL) AS temps_moyen
        FROM demandes_services s
        LEFT JOIN demandes_citoyens d ON d.service_assigne_id = s.id
        WHERE s.actif = TRUE
        GROUP BY s.id, s.nom, s.couleur
        ORDER BY total DESC
    """))
    par_service = [
        StatsParService(
            service_id=str(row.service_id),
            service_nom=row.service_nom,
            service_couleur=row.service_couleur,
            total=row.total or 0,
            temps_moyen_jours=round(float(row.temps_moyen), 1) if row.temps_moyen else None,
        )
        for row in service_result.fetchall()
    ]

    # Évolution 30 derniers jours
    evolution_result = await db.execute(text("""
        SELECT
            DATE(created_at) AS date_stat,
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE statut = 'nouveau') AS nouvelles,
            COUNT(*) FILTER (WHERE statut = 'traite') AS traitees
        FROM demandes_citoyens
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(created_at)
        ORDER BY date_stat
    """))
    evolution_30j = [
        StatsParPeriode(
            date=row.date_stat,
            total=row.total or 0,
            nouvelles=row.nouvelles or 0,
            traitees=row.traitees or 0,
        )
        for row in evolution_result.fetchall()
    ]

    # Demandes prioritaires (urgentes + en retard)
    prioritaires_result = await db.execute(text("""
        SELECT
            d.id,
            d.numero_suivi,
            c.nom AS categorie_nom,
            s.nom AS service_nom,
            d.description,
            d.priorite,
            d.statut,
            d.created_at,
            EXTRACT(DAY FROM (CURRENT_TIMESTAMP - d.created_at))::int AS jours_attente,
            (d.priorite = 'urgente') AS est_urgente,
            (EXTRACT(DAY FROM (CURRENT_TIMESTAMP - d.created_at)) >= :delai_retard) AS est_en_retard,
            FALSE AS rappel_envoye
        FROM demandes_citoyens d
        LEFT JOIN demandes_categories c ON d.categorie_id = c.id
        LEFT JOIN demandes_services s ON d.service_assigne_id = s.id
        WHERE d.statut NOT IN ('traite', 'cloture', 'rejete')
          AND (
              d.priorite = 'urgente'
              OR EXTRACT(DAY FROM (CURRENT_TIMESTAMP - d.created_at)) >= :delai_retard
          )
        ORDER BY
            CASE d.priorite WHEN 'urgente' THEN 0 WHEN 'haute' THEN 1 WHEN 'normale' THEN 2 ELSE 3 END,
            d.created_at ASC
        LIMIT 20
    """), {"delai_retard": delai_retard_jours})

    prioritaires = [
        DemandePrioritaire(
            id=str(row.id),
            numero_suivi=row.numero_suivi,
            categorie_nom=row.categorie_nom,
            service_nom=row.service_nom,
            description=row.description[:60] + "..." if len(row.description) > 60 else row.description,
            priorite=row.priorite,
            statut=row.statut,
            created_at=row.created_at,
            jours_attente=row.jours_attente or 0,
            est_urgente=row.est_urgente,
            est_en_retard=row.est_en_retard,
            rappel_envoye=row.rappel_envoye,
        )
        for row in prioritaires_result.fetchall()
    ]

    # === Métriques dirigeant ===

    # Taux de résolution et distribution des statuts
    dist_result = await db.execute(text("""
        SELECT
            COUNT(*) FILTER (WHERE statut = 'nouveau') AS nouveau,
            COUNT(*) FILTER (WHERE statut = 'en_moderation') AS en_moderation,
            COUNT(*) FILTER (WHERE statut = 'envoye') AS envoye,
            COUNT(*) FILTER (WHERE statut = 'accepte') AS accepte,
            COUNT(*) FILTER (WHERE statut = 'en_cours') AS en_cours,
            COUNT(*) FILTER (WHERE statut = 'planifie') AS planifie,
            COUNT(*) FILTER (WHERE statut = 'traite') AS traite,
            COUNT(*) FILTER (WHERE statut = 'cloture') AS cloture,
            COUNT(*) FILTER (WHERE statut = 'rejete') AS rejete
        FROM demandes_citoyens
    """))
    dist = dist_result.fetchone()

    total_count = kpi.total or 0
    traite_count = (dist.traite or 0) + (dist.cloture or 0)
    taux_resolution = round(traite_count * 100.0 / total_count, 1) if total_count > 0 else None

    distribution_statuts = DistributionStatuts(
        nouveau=dist.nouveau or 0,
        en_moderation=dist.en_moderation or 0,
        envoye=dist.envoye or 0,
        accepte=dist.accepte or 0,
        en_cours=dist.en_cours or 0,
        planifie=dist.planifie or 0,
        traite=dist.traite or 0,
        cloture=dist.cloture or 0,
        rejete=dist.rejete or 0,
    )

    # Comparaison avec le mois précédent
    comp_result = await db.execute(text("""
        SELECT
            COUNT(*) FILTER (WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)) AS volume_ce_mois,
            COUNT(*) FILTER (WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                AND created_at < DATE_TRUNC('month', CURRENT_DATE)) AS volume_mois_prec,
            COUNT(*) FILTER (WHERE statut IN ('traite', 'cloture')
                AND date_resolution >= DATE_TRUNC('month', CURRENT_DATE)) AS traitees_ce_mois,
            COUNT(*) FILTER (WHERE statut IN ('traite', 'cloture')
                AND date_resolution >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                AND date_resolution < DATE_TRUNC('month', CURRENT_DATE)) AS traitees_mois_prec,
            AVG(EXTRACT(EPOCH FROM (date_resolution - created_at))/86400)
                FILTER (WHERE date_resolution IS NOT NULL
                    AND date_resolution >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month'
                    AND date_resolution < DATE_TRUNC('month', CURRENT_DATE)) AS delai_moyen_mois_prec
        FROM demandes_citoyens
    """))
    comp = comp_result.fetchone()

    vol_ce_mois = comp.volume_ce_mois or 0
    vol_mois_prec = comp.volume_mois_prec or 0
    comp_volume = ComparaisonPeriode(
        ce_mois=vol_ce_mois,
        mois_precedent=vol_mois_prec,
        variation_pct=round((vol_ce_mois - vol_mois_prec) * 100.0 / vol_mois_prec, 1) if vol_mois_prec > 0 else None,
    )

    trait_ce_mois = comp.traitees_ce_mois or 0
    trait_mois_prec = comp.traitees_mois_prec or 0
    comp_traitees = ComparaisonPeriode(
        ce_mois=trait_ce_mois,
        mois_precedent=trait_mois_prec,
        variation_pct=round((trait_ce_mois - trait_mois_prec) * 100.0 / trait_mois_prec, 1) if trait_mois_prec > 0 else None,
    )

    delai_moyen_mois_prec = round(float(comp.delai_moyen_mois_prec), 1) if comp.delai_moyen_mois_prec else None

    # Évolution sur 12 mois (agrégation mensuelle)
    evolution_12m_result = await db.execute(text("""
        SELECT
            DATE_TRUNC('month', created_at)::date AS date_stat,
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE statut = 'nouveau') AS nouvelles,
            COUNT(*) FILTER (WHERE statut IN ('traite', 'cloture')) AS traitees
        FROM demandes_citoyens
        WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '11 months'
        GROUP BY DATE_TRUNC('month', created_at)
        ORDER BY date_stat
    """))
    evolution_12m = [
        StatsParPeriode(
            date=row.date_stat,
            total=row.total or 0,
            nouvelles=row.nouvelles or 0,
            traitees=row.traitees or 0,
        )
        for row in evolution_12m_result.fetchall()
    ]

    return DashboardStats(
        total=kpi.total or 0,
        nouvelles=kpi.nouvelles or 0,
        urgentes=kpi.urgentes or 0,
        traitees_mois=kpi.traitees_mois or 0,
        delai_moyen_jours=round(float(kpi.delai_moyen), 1) if kpi.delai_moyen else None,
        # Métriques dirigeant
        taux_resolution_pct=taux_resolution,
        en_cours=(dist.en_cours or 0) + (dist.planifie or 0),
        rejetees=dist.rejete or 0,
        delai_moyen_mois_precedent=delai_moyen_mois_prec,
        comparaison_volume=comp_volume,
        comparaison_traitees=comp_traitees,
        distribution_statuts=distribution_statuts,
        # Graphiques
        par_categorie=par_categorie,
        par_service=par_service,
        evolution_30j=evolution_30j,
        evolution_12m=evolution_12m,
        prioritaires=prioritaires,
        delai_retard_jours=delai_retard_jours,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATES DE RÉPONSES (AVANT les routes avec paramètres dynamiques!)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(
    project_id: Optional[str] = Query(None),
    categorie_id: Optional[str] = None,
    langue: str = Query("fr"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Liste les templates de réponses."""
    conditions = ["actif = TRUE", "langue = :langue"]
    params = {"langue": langue}

    if project_id:
        conditions.append("project_id = :project_id")
        params["project_id"] = project_id

    query = f"""
        SELECT id, project_id, titre, contenu, categorie_id, statut_cible,
               actif, ordre_affichage, langue, created_at, updated_at
        FROM demandes_templates
        WHERE {' AND '.join(conditions)}
    """

    if categorie_id:
        query += " AND (categorie_id = :cat_id OR categorie_id IS NULL)"
        params["cat_id"] = categorie_id

    query += " ORDER BY ordre_affichage, titre"

    result = await db.execute(text(query), params)

    return [
        TemplateResponse(
            id=str(row.id),
            project_id=str(row.project_id),
            titre=row.titre,
            contenu=row.contenu,
            categorie_id=str(row.categorie_id) if row.categorie_id else None,
            statut_cible=DemandeStatut(row.statut_cible) if row.statut_cible else None,
            actif=row.actif,
            ordre_affichage=row.ordre_affichage,
            langue=row.langue,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in result.fetchall()
    ]


@router.post("/templates", response_model=TemplateResponse)
async def create_template(
    project_id: str,
    template: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Crée un nouveau template de réponse."""
    result = await db.execute(text("""
        INSERT INTO demandes_templates (
            project_id, titre, contenu, categorie_id, statut_cible,
            actif, ordre_affichage, langue
        )
        VALUES (
            :project_id, :titre, :contenu, :categorie_id, :statut_cible,
            :actif, :ordre, :langue
        )
        RETURNING id, project_id, titre, contenu, categorie_id, statut_cible,
                  actif, ordre_affichage, langue, created_at, updated_at
    """), {
        "project_id": project_id,
        "titre": template.titre,
        "contenu": template.contenu,
        "categorie_id": template.categorie_id,
        "statut_cible": template.statut_cible.value if template.statut_cible else None,
        "actif": template.actif,
        "ordre": template.ordre_affichage,
        "langue": template.langue,
    })

    await db.commit()
    row = result.fetchone()

    return TemplateResponse(
        id=str(row.id),
        project_id=str(row.project_id),
        titre=row.titre,
        contenu=row.contenu,
        categorie_id=str(row.categorie_id) if row.categorie_id else None,
        statut_cible=DemandeStatut(row.statut_cible) if row.statut_cible else None,
        actif=row.actif,
        ordre_affichage=row.ordre_affichage,
        langue=row.langue,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# DEMANDES - API AGENTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("", response_model=DemandeListResponse)
async def list_demandes(
    project_id: Optional[str] = Query(None, description="UUID du projet (optionnel si mono-projet)"),
    statut: Optional[List[DemandeStatut]] = Query(None, description="Filtrer par statut(s)"),
    categorie_id: Optional[str] = None,
    quartier_id: Optional[str] = None,
    priorite: Optional[DemandePriorite] = None,
    agent_assigne_id: Optional[str] = None,
    date_debut: Optional[date] = None,
    date_fin: Optional[date] = None,
    recherche: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Liste les demandes avec filtres et pagination."""
    conditions = ["1=1"]
    params = {}

    # Filtrer par projet si spécifié
    if project_id:
        conditions.append("d.project_id = :project_id")
        params["project_id"] = project_id

    # Filtrer par statut(s) - peut être une liste
    if statut:
        if len(statut) == 1:
            conditions.append("d.statut = :statut")
            params["statut"] = statut[0].value
        else:
            statut_values = [s.value for s in statut]
            conditions.append(f"d.statut IN ({','.join([':s' + str(i) for i in range(len(statut_values))])})")
            for i, s in enumerate(statut_values):
                params[f"s{i}"] = s

    if categorie_id:
        conditions.append("d.categorie_id = :categorie_id")
        params["categorie_id"] = categorie_id

    if quartier_id:
        conditions.append("d.quartier_id = :quartier_id")
        params["quartier_id"] = quartier_id

    if priorite:
        conditions.append("d.priorite = :priorite")
        params["priorite"] = priorite.value

    if agent_assigne_id:
        conditions.append("d.agent_assigne_id = :agent_id")
        params["agent_id"] = agent_assigne_id

    if date_debut:
        conditions.append("d.created_at >= :date_debut")
        params["date_debut"] = date_debut

    if date_fin:
        conditions.append("d.created_at <= :date_fin")
        params["date_fin"] = date_fin

    if recherche:
        conditions.append("""
            (d.numero_suivi ILIKE :recherche
             OR d.description ILIKE :recherche
             OR d.declarant_email ILIKE :recherche
             OR d.declarant_nom ILIKE :recherche)
        """)
        params["recherche"] = f"%{recherche}%"

    where_clause = " AND ".join(conditions)

    # Compter le total
    count_result = await db.execute(text(f"""
        SELECT COUNT(*) FROM demandes_citoyens d WHERE {where_clause}
    """), params)
    total = count_result.scalar()

    # Récupérer les demandes
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    result = await db.execute(text(f"""
        SELECT d.id, d.project_id, d.numero_suivi, d.categorie_id,
               c.nom AS categorie_nom, c.icone AS categorie_icone, c.couleur AS categorie_couleur,
               cp.nom AS categorie_parent_nom,
               d.declarant_email, d.declarant_telephone, d.declarant_nom, d.declarant_langue,
               d.description, d.champs_supplementaires, d.photos,
               ST_Y(d.geom) AS latitude, ST_X(d.geom) AS longitude,
               d.adresse_approximative, d.quartier_id, p.name AS quartier_nom,
               d.equipement_id, d.statut, d.priorite,
               d.service_assigne_id, sv.nom AS service_assigne_nom, sv.couleur AS service_assigne_couleur,
               d.agent_assigne_id,
               d.agent_service_id, CONCAT(agt.prenom, ' ', agt.nom) AS agent_service_nom,
               d.created_at, d.updated_at, d.date_prise_en_charge,
               d.date_planification, d.date_resolution, d.date_cloture, d.source,
               EXTRACT(EPOCH FROM (COALESCE(d.date_resolution, CURRENT_TIMESTAMP) - d.created_at))/3600 AS heures,
               COALESCE((
                   SELECT COUNT(*)
                   FROM demandes_messages m
                   WHERE m.demande_id = d.id
                     AND m.sender_type = 'service'
                     AND m.lu_par_demandes = FALSE
               ), 0) AS messages_non_lus
        FROM demandes_citoyens d
        LEFT JOIN demandes_categories c ON d.categorie_id = c.id
        LEFT JOIN demandes_categories cp ON c.parent_id = cp.id
        LEFT JOIN perimetres p ON d.quartier_id = p.id
        LEFT JOIN demandes_services sv ON d.service_assigne_id = sv.id
        LEFT JOIN demandes_services_agents agt ON d.agent_service_id = agt.id
        WHERE {where_clause}
        ORDER BY d.created_at DESC
        LIMIT :limit OFFSET :offset
    """), params)

    demandes = []
    for row in result.fetchall():
        demandes.append(DemandeResponse(
            id=str(row.id),
            project_id=str(row.project_id),
            numero_suivi=row.numero_suivi,
            categorie_id=str(row.categorie_id),
            categorie_nom=row.categorie_nom,
            categorie_icone=row.categorie_icone,
            categorie_couleur=row.categorie_couleur,
            categorie_parent_nom=row.categorie_parent_nom,
            declarant_email=row.declarant_email,
            declarant_telephone=row.declarant_telephone,
            declarant_nom=row.declarant_nom,
            declarant_langue=row.declarant_langue,
            description=row.description,
            champs_supplementaires=row.champs_supplementaires or {},
            photos=row.photos or [],
            latitude=row.latitude,
            longitude=row.longitude,
            adresse_approximative=row.adresse_approximative,
            quartier_id=str(row.quartier_id) if row.quartier_id else None,
            quartier_nom=row.quartier_nom,
            equipement_id=str(row.equipement_id) if row.equipement_id else None,
            statut=DemandeStatut(row.statut),
            priorite=DemandePriorite(row.priorite),
            service_assigne_id=str(row.service_assigne_id) if row.service_assigne_id else None,
            service_assigne_nom=row.service_assigne_nom,
            service_assigne_couleur=row.service_assigne_couleur,
            agent_assigne_id=str(row.agent_assigne_id) if row.agent_assigne_id else None,
            agent_service_id=str(row.agent_service_id) if row.agent_service_id else None,
            agent_service_nom=row.agent_service_nom,
            created_at=row.created_at,
            updated_at=row.updated_at,
            date_prise_en_charge=row.date_prise_en_charge,
            date_planification=row.date_planification,
            date_resolution=row.date_resolution,
            date_cloture=row.date_cloture,
            source=row.source,
            heures_depuis_creation=row.heures,
            messages_non_lus=row.messages_non_lus or 0,
        ))

    total_pages = (total + page_size - 1) // page_size

    return DemandeListResponse(
        demandes=demandes,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICES MUNICIPAUX
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/services", response_model=List[ServiceResponse])
async def list_services(
    project_id: str = Query(...),
    actif_only: bool = Query(True),
    include_stats: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Liste tous les services d'un projet."""
    query = """
        SELECT
            s.*,
            COUNT(d.id) AS total_demandes,
            COUNT(d.id) FILTER (WHERE d.statut IN ('nouveau', 'en_moderation', 'envoye', 'accepte', 'en_cours', 'planifie')) AS demandes_en_cours
        FROM demandes_services s
        LEFT JOIN demandes_citoyens d ON d.service_assigne_id = s.id
        WHERE s.project_id = CAST(:project_id AS uuid)
    """
    if actif_only:
        query += " AND s.actif = TRUE"
    query += " GROUP BY s.id ORDER BY s.ordre_affichage, s.nom"

    result = await db.execute(text(query), {"project_id": project_id})
    rows = result.fetchall()

    services = []
    for row in rows:
        service = ServiceResponse(
            id=str(row.id),
            project_id=str(row.project_id),
            nom=row.nom,
            code=row.code,
            description=row.description,
            email=row.email,
            telephone=row.telephone,
            responsable_nom=row.responsable_nom,
            actif=row.actif,
            ordre_affichage=row.ordre_affichage,
            couleur=row.couleur or "#3b82f6",
            icone=row.icone or "business",
            notifier_nouvelle_demande=row.notifier_nouvelle_demande,
            notifier_changement_statut=row.notifier_changement_statut,
            emails_notification=row.emails_notification or [],
            created_at=row.created_at,
            updated_at=row.updated_at,
            total_demandes=row.total_demandes if include_stats else None,
            demandes_en_cours=row.demandes_en_cours if include_stats else None,
        )
        services.append(service)

    return services


@router.post("/services", response_model=ServiceResponse, status_code=201)
async def create_service(
    project_id: str = Query(...),
    service: ServiceCreate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Crée un nouveau service municipal."""
    result = await db.execute(text("""
        INSERT INTO demandes_services (
            project_id, nom, code, description, email, telephone, responsable_nom,
            actif, ordre_affichage, couleur, icone,
            notifier_nouvelle_demande, notifier_changement_statut, emails_notification
        )
        VALUES (
            CAST(:project_id AS uuid), :nom, :code, :description, :email, :telephone, :responsable_nom,
            :actif, :ordre_affichage, :couleur, :icone,
            :notifier_nouvelle_demande, :notifier_changement_statut, CAST(:emails_notification AS jsonb)
        )
        RETURNING *
    """), {
        "project_id": project_id,
        "nom": service.nom,
        "code": service.code,
        "description": service.description,
        "email": service.email,
        "telephone": service.telephone,
        "responsable_nom": service.responsable_nom,
        "actif": service.actif,
        "ordre_affichage": service.ordre_affichage,
        "couleur": service.couleur,
        "icone": service.icone,
        "notifier_nouvelle_demande": service.notifier_nouvelle_demande,
        "notifier_changement_statut": service.notifier_changement_statut,
        "emails_notification": json.dumps(service.emails_notification),
    })

    row = result.fetchone()
    await db.commit()

    return ServiceResponse(
        id=str(row.id),
        project_id=str(row.project_id),
        nom=row.nom,
        code=row.code,
        description=row.description,
        email=row.email,
        telephone=row.telephone,
        responsable_nom=row.responsable_nom,
        actif=row.actif,
        ordre_affichage=row.ordre_affichage,
        couleur=row.couleur or "#3b82f6",
        icone=row.icone or "business",
        notifier_nouvelle_demande=row.notifier_nouvelle_demande,
        notifier_changement_statut=row.notifier_changement_statut,
        emails_notification=row.emails_notification or [],
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/services/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère un service par son ID."""
    result = await db.execute(text("""
        SELECT
            s.*,
            COUNT(d.id) AS total_demandes,
            COUNT(d.id) FILTER (WHERE d.statut IN ('nouveau', 'en_moderation', 'envoye', 'accepte', 'en_cours', 'planifie')) AS demandes_en_cours
        FROM demandes_services s
        LEFT JOIN demandes_citoyens d ON d.service_assigne_id = s.id
        WHERE s.id = CAST(:service_id AS uuid)
        GROUP BY s.id
    """), {"service_id": service_id})

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Service non trouvé")

    return ServiceResponse(
        id=str(row.id),
        project_id=str(row.project_id),
        nom=row.nom,
        code=row.code,
        description=row.description,
        email=row.email,
        telephone=row.telephone,
        responsable_nom=row.responsable_nom,
        actif=row.actif,
        ordre_affichage=row.ordre_affichage,
        couleur=row.couleur or "#3b82f6",
        icone=row.icone or "business",
        notifier_nouvelle_demande=row.notifier_nouvelle_demande,
        notifier_changement_statut=row.notifier_changement_statut,
        emails_notification=row.emails_notification or [],
        created_at=row.created_at,
        updated_at=row.updated_at,
        total_demandes=row.total_demandes,
        demandes_en_cours=row.demandes_en_cours,
    )


@router.put("/services/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: str,
    service: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Met à jour un service."""
    # Construire la requête de mise à jour dynamiquement
    updates = []
    params = {"service_id": service_id}

    if service.nom is not None:
        updates.append("nom = :nom")
        params["nom"] = service.nom
    if service.code is not None:
        updates.append("code = :code")
        params["code"] = service.code
    if service.description is not None:
        updates.append("description = :description")
        params["description"] = service.description
    if service.email is not None:
        updates.append("email = :email")
        params["email"] = service.email
    if service.telephone is not None:
        updates.append("telephone = :telephone")
        params["telephone"] = service.telephone
    if service.responsable_nom is not None:
        updates.append("responsable_nom = :responsable_nom")
        params["responsable_nom"] = service.responsable_nom
    if service.actif is not None:
        updates.append("actif = :actif")
        params["actif"] = service.actif
    if service.ordre_affichage is not None:
        updates.append("ordre_affichage = :ordre_affichage")
        params["ordre_affichage"] = service.ordre_affichage
    if service.couleur is not None:
        updates.append("couleur = :couleur")
        params["couleur"] = service.couleur
    if service.icone is not None:
        updates.append("icone = :icone")
        params["icone"] = service.icone
    if service.notifier_nouvelle_demande is not None:
        updates.append("notifier_nouvelle_demande = :notifier_nouvelle_demande")
        params["notifier_nouvelle_demande"] = service.notifier_nouvelle_demande
    if service.notifier_changement_statut is not None:
        updates.append("notifier_changement_statut = :notifier_changement_statut")
        params["notifier_changement_statut"] = service.notifier_changement_statut
    if service.emails_notification is not None:
        updates.append("emails_notification = CAST(:emails_notification AS jsonb)")
        params["emails_notification"] = json.dumps(service.emails_notification)

    if not updates:
        raise HTTPException(status_code=400, detail="Aucune modification fournie")

    query = f"""
        UPDATE demandes_services
        SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
        WHERE id = CAST(:service_id AS uuid)
        RETURNING *
    """

    result = await db.execute(text(query), params)
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Service non trouvé")

    await db.commit()

    return ServiceResponse(
        id=str(row.id),
        project_id=str(row.project_id),
        nom=row.nom,
        code=row.code,
        description=row.description,
        email=row.email,
        telephone=row.telephone,
        responsable_nom=row.responsable_nom,
        actif=row.actif,
        ordre_affichage=row.ordre_affichage,
        couleur=row.couleur or "#3b82f6",
        icone=row.icone or "business",
        notifier_nouvelle_demande=row.notifier_nouvelle_demande,
        notifier_changement_statut=row.notifier_changement_statut,
        emails_notification=row.emails_notification or [],
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.delete("/services/{service_id}")
async def delete_service(
    service_id: str,
    reassign_to: Optional[str] = Query(None, description="ID du service vers lequel réaffecter les demandes"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Supprime un service. Peut réaffecter les demandes vers un autre service."""
    # Vérifier si des demandes sont assignées
    check = await db.execute(text("""
        SELECT COUNT(*) AS count FROM demandes_citoyens
        WHERE service_assigne_id = CAST(:service_id AS uuid)
          AND statut NOT IN ('cloture', 'rejete', 'traite')
    """), {"service_id": service_id})
    count = check.fetchone().count

    if count > 0 and not reassign_to:
        raise HTTPException(
            status_code=400,
            detail=f"{count} demande(s) active(s) assignée(s) à ce service. Spécifiez reassign_to pour les réaffecter."
        )

    # Réaffecter si nécessaire
    if reassign_to:
        await db.execute(text("""
            UPDATE demandes_citoyens
            SET service_assigne_id = CAST(:new_service_id AS uuid),
                updated_at = CURRENT_TIMESTAMP
            WHERE service_assigne_id = CAST(:service_id AS uuid)
              AND statut NOT IN ('cloture', 'rejete', 'traite')
        """), {"service_id": service_id, "new_service_id": reassign_to})

    # Supprimer le service
    result = await db.execute(text("""
        DELETE FROM demandes_services
        WHERE id = CAST(:service_id AS uuid)
        RETURNING id
    """), {"service_id": service_id})

    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Service non trouvé")

    await db.commit()

    return {"success": True, "message": "Service supprimé", "demandes_reassignees": count if reassign_to else 0}


@router.get("/services/stats/all", response_model=List[ServiceStatsResponse])
async def get_services_stats(
    project_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère les statistiques de tous les services d'un projet."""
    result = await db.execute(text("""
        SELECT * FROM v_stats_par_service
        WHERE project_id = CAST(:project_id AS uuid)
        ORDER BY total_demandes DESC
    """), {"project_id": project_id})

    rows = result.fetchall()

    return [
        ServiceStatsResponse(
            service_id=str(row.service_id),
            service_nom=row.service_nom,
            service_code=row.service_code,
            service_couleur=row.service_couleur or "#3b82f6",
            total_demandes=row.total_demandes or 0,
            nouvelles=row.nouvelles or 0,
            a_traiter=row.a_traiter or 0,
            en_cours=row.en_cours or 0,
            traitees=row.traitees or 0,
            cloturees=row.cloturees or 0,
            temps_moyen_heures=float(row.temps_moyen_heures) if row.temps_moyen_heures else None,
        )
        for row in rows
    ]


@router.post("/services/{service_id}/assign-demande/{demande_id}")
async def assign_demande_to_service(
    service_id: str,
    demande_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Assigne une demande à un service et passe le statut à 'envoye'."""
    result = await db.execute(text("""
        UPDATE demandes_citoyens
        SET service_assigne_id = CAST(:service_id AS uuid),
            statut = CASE
                WHEN statut IN ('nouveau', 'en_moderation') THEN 'envoye'
                ELSE statut
            END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = CAST(:demande_id AS uuid)
        RETURNING id, numero_suivi
    """), {"service_id": service_id, "demande_id": demande_id})

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    # Ajouter à l'historique
    await db.execute(text("""
        INSERT INTO demandes_historique (
            demande_id, agent_id, agent_nom, action, commentaire
        )
        VALUES (
            CAST(:demande_id AS uuid), :agent_id, :agent_nom, 'assignation',
            :commentaire
        )
    """), {
        "demande_id": demande_id,
        "agent_id": current_user.get("id"),
        "agent_nom": current_user.get("name", current_user.get("email")),
        "commentaire": f"Demande assignée au service",
    })

    await db.commit()

    return {
        "success": True,
        "message": f"Demande {row.numero_suivi} assignée au service",
        "demande_id": demande_id,
        "service_id": service_id,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AGENTS DE SERVICE (CRUD pour GeoClic Services)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/services/{service_id}/agents", response_model=List[ServiceAgentResponse])
async def list_service_agents(
    service_id: str,
    include_inactive: bool = Query(False, description="Inclure les agents désactivés"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Liste les agents d'un service."""
    where_clause = "a.service_id = CAST(:service_id AS uuid)"
    if not include_inactive:
        where_clause += " AND a.actif = TRUE"

    result = await db.execute(text(f"""
        SELECT
            a.id,
            a.service_id,
            a.email,
            a.nom,
            a.prenom,
            COALESCE(a.nom || ' ' || a.prenom, a.email, 'Agent') AS nom_complet,
            a.telephone,
            a.role,
            a.peut_assigner,
            a.recoit_notifications,
            a.actif,
            a.last_login,
            a.created_at
        FROM demandes_services_agents a
        WHERE {where_clause}
        ORDER BY a.role DESC, a.nom, a.prenom
    """), {"service_id": service_id})

    agents = result.fetchall()
    return [
        ServiceAgentResponse(
            id=str(a.id),
            service_id=str(a.service_id),
            email=a.email,
            nom=a.nom,
            prenom=a.prenom,
            nom_complet=a.nom_complet,
            telephone=a.telephone,
            role=a.role,
            peut_assigner=a.peut_assigner,
            recoit_notifications=a.recoit_notifications,
            actif=a.actif,
            last_login=a.last_login,
            created_at=a.created_at,
        )
        for a in agents
    ]


@router.post("/services/{service_id}/agents", response_model=ServiceAgentResponse, status_code=201)
async def create_service_agent(
    service_id: str,
    agent_data: ServiceAgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Crée un agent pour un service (crée aussi dans geoclic_users pour l'accès unifié)."""
    import bcrypt

    # Vérifier que le service existe
    result = await db.execute(text("""
        SELECT id FROM demandes_services WHERE id = CAST(:id AS uuid)
    """), {"id": service_id})
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Service non trouvé")

    # Vérifier que l'email n'existe pas déjà (dans les deux tables)
    result = await db.execute(text("""
        SELECT id FROM demandes_services_agents WHERE email = :email
    """), {"email": agent_data.email})
    if result.fetchone():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    result = await db.execute(text("""
        SELECT id FROM geoclic_users WHERE email = :email
    """), {"email": agent_data.email})
    if result.fetchone():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé dans le système")

    # Hasher le mot de passe
    password_hash = bcrypt.hashpw(
        agent_data.password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    # Créer l'agent dans demandes_services_agents (legacy)
    result = await db.execute(text("""
        INSERT INTO demandes_services_agents (
            service_id, email, password_hash, nom, prenom, telephone,
            role, peut_assigner, recoit_notifications
        )
        VALUES (
            CAST(:service_id AS uuid), :email, :password_hash, :nom, :prenom, :telephone,
            :role, :peut_assigner, :recoit_notifications
        )
        RETURNING id, service_id, email, nom, prenom, telephone, role,
                  peut_assigner, recoit_notifications, actif, last_login, created_at
    """), {
        "service_id": service_id,
        "email": agent_data.email,
        "password_hash": password_hash,
        "nom": agent_data.nom,
        "prenom": agent_data.prenom,
        "telephone": agent_data.telephone,
        "role": agent_data.role.value,
        "peut_assigner": agent_data.peut_assigner,
        "recoit_notifications": agent_data.recoit_notifications,
    })
    a = result.fetchone()

    # Créer aussi dans geoclic_users pour l'authentification unifiée
    role_demandes = "admin" if agent_data.role.value == "responsable" else "agent"
    await db.execute(text("""
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
    """), {
        "email": agent_data.email,
        "password_hash": password_hash,
        "nom": agent_data.nom,
        "prenom": agent_data.prenom,
        "role_demandes": role_demandes,
        "service_id": service_id,
    })

    await db.commit()

    return ServiceAgentResponse(
        id=str(a.id),
        service_id=str(a.service_id),
        email=a.email,
        nom=a.nom,
        prenom=a.prenom,
        nom_complet=f"{a.nom} {a.prenom}",
        telephone=a.telephone,
        role=a.role,
        peut_assigner=a.peut_assigner,
        recoit_notifications=a.recoit_notifications,
        actif=a.actif,
        last_login=a.last_login,
        created_at=a.created_at,
    )


@router.put("/services/{service_id}/agents/{agent_id}", response_model=ServiceAgentResponse)
async def update_service_agent(
    service_id: str,
    agent_id: str,
    agent_data: ServiceAgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Modifie un agent de service (synchronise aussi avec geoclic_users)."""
    # Vérifier que l'agent appartient au service et récupérer son email
    result = await db.execute(text("""
        SELECT id, email FROM demandes_services_agents
        WHERE id = CAST(:agent_id AS uuid) AND service_id = CAST(:service_id AS uuid)
    """), {"agent_id": agent_id, "service_id": service_id})
    agent_row = result.fetchone()
    if not agent_row:
        raise HTTPException(status_code=404, detail="Agent non trouvé dans ce service")

    agent_email = agent_row.email

    # Construire la requête de mise à jour pour demandes_services_agents
    update_fields = []
    params = {"agent_id": agent_id}

    # Construire la requête de mise à jour pour geoclic_users
    update_fields_users = []
    params_users = {"email": agent_email}

    if agent_data.nom is not None:
        update_fields.append("nom = :nom")
        update_fields_users.append("nom = :nom")
        params["nom"] = agent_data.nom
        params_users["nom"] = agent_data.nom

    if agent_data.prenom is not None:
        update_fields.append("prenom = :prenom")
        update_fields_users.append("prenom = :prenom")
        params["prenom"] = agent_data.prenom
        params_users["prenom"] = agent_data.prenom

    if agent_data.telephone is not None:
        update_fields.append("telephone = :telephone")
        params["telephone"] = agent_data.telephone

    if agent_data.role is not None:
        update_fields.append("role = :role")
        params["role"] = agent_data.role.value
        # Synchroniser le rôle vers geoclic_users
        role_demandes = "admin" if agent_data.role.value == "responsable" else "agent"
        update_fields_users.append("role_demandes = :role_demandes")
        params_users["role_demandes"] = role_demandes

    if agent_data.peut_assigner is not None:
        update_fields.append("peut_assigner = :peut_assigner")
        params["peut_assigner"] = agent_data.peut_assigner

    if agent_data.recoit_notifications is not None:
        update_fields.append("recoit_notifications = :recoit_notifications")
        params["recoit_notifications"] = agent_data.recoit_notifications

    if agent_data.actif is not None:
        update_fields.append("actif = :actif")
        update_fields_users.append("actif = :actif")
        params["actif"] = agent_data.actif
        params_users["actif"] = agent_data.actif

    if not update_fields:
        raise HTTPException(status_code=400, detail="Aucune modification fournie")

    # Mettre à jour demandes_services_agents
    await db.execute(text(f"""
        UPDATE demandes_services_agents
        SET {', '.join(update_fields)}
        WHERE id = CAST(:agent_id AS uuid)
    """), params)

    # Synchroniser vers geoclic_users si des champs pertinents ont changé
    if update_fields_users:
        await db.execute(text(f"""
            UPDATE geoclic_users
            SET {', '.join(update_fields_users)}
            WHERE email = :email
        """), params_users)

    await db.commit()

    # Récupérer l'agent mis à jour
    result = await db.execute(text("""
        SELECT
            id, service_id, email, nom, prenom,
            COALESCE(nom || ' ' || prenom, email, 'Agent') AS nom_complet,
            telephone, role, peut_assigner,
            recoit_notifications,
            actif, last_login, created_at
        FROM demandes_services_agents
        WHERE id = CAST(:agent_id AS uuid)
    """), {"agent_id": agent_id})
    a = result.fetchone()

    return ServiceAgentResponse(
        id=str(a.id),
        service_id=str(a.service_id),
        email=a.email,
        nom=a.nom,
        prenom=a.prenom,
        nom_complet=a.nom_complet,
        telephone=a.telephone,
        role=a.role,
        peut_assigner=a.peut_assigner,
        recoit_notifications=a.recoit_notifications,
        actif=a.actif,
        last_login=a.last_login,
        created_at=a.created_at,
    )


@router.post("/services/{service_id}/agents/{agent_id}/reset-password")
async def reset_agent_password(
    service_id: str,
    agent_id: str,
    data: ServiceAgentResetPassword,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Réinitialise le mot de passe d'un agent."""
    import bcrypt

    # Vérifier que l'agent appartient au service
    result = await db.execute(text("""
        SELECT id FROM demandes_services_agents
        WHERE id = CAST(:agent_id AS uuid) AND service_id = CAST(:service_id AS uuid)
    """), {"agent_id": agent_id, "service_id": service_id})
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Agent non trouvé dans ce service")

    # Hasher le nouveau mot de passe
    password_hash = bcrypt.hashpw(
        data.new_password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    # Mettre à jour
    await db.execute(text("""
        UPDATE demandes_services_agents
        SET password_hash = :password_hash
        WHERE id = CAST(:agent_id AS uuid)
    """), {"agent_id": agent_id, "password_hash": password_hash})
    await db.commit()

    return {"message": "Mot de passe réinitialisé avec succès"}


@router.delete("/services/{service_id}/agents/{agent_id}")
async def delete_service_agent(
    service_id: str,
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Désactive un agent de service (soft delete)."""
    # Vérifier que l'agent appartient au service
    result = await db.execute(text("""
        SELECT id FROM demandes_services_agents
        WHERE id = CAST(:agent_id AS uuid) AND service_id = CAST(:service_id AS uuid)
    """), {"agent_id": agent_id, "service_id": service_id})
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Agent non trouvé dans ce service")

    # Désactiver (soft delete)
    await db.execute(text("""
        UPDATE demandes_services_agents
        SET actif = FALSE
        WHERE id = CAST(:agent_id AS uuid)
    """), {"agent_id": agent_id})

    # Retirer les demandes assignées à cet agent
    await db.execute(text("""
        UPDATE demandes_citoyens
        SET agent_service_id = NULL
        WHERE agent_service_id = CAST(:agent_id AS uuid)
    """), {"agent_id": agent_id})

    await db.commit()

    return {"message": "Agent désactivé"}


# ═══════════════════════════════════════════════════════════════════════════════
# DÉTAIL DEMANDE (doit être après /services pour ne pas capturer /services)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{demande_id}", response_model=DemandeResponse)
async def get_demande(
    demande_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère une demande par son ID."""
    result = await db.execute(text("""
        SELECT d.id, d.project_id, d.numero_suivi, d.categorie_id,
               c.nom AS categorie_nom, c.icone AS categorie_icone, c.couleur AS categorie_couleur,
               cp.nom AS categorie_parent_nom,
               d.declarant_email, d.declarant_telephone, d.declarant_nom, d.declarant_langue,
               d.description, d.champs_supplementaires, d.photos, d.photos_intervention,
               ST_Y(d.geom) AS latitude, ST_X(d.geom) AS longitude,
               d.adresse_approximative, d.quartier_id, p.name AS quartier_nom,
               d.equipement_id, d.statut, d.priorite,
               d.service_assigne_id, s.nom AS service_assigne_nom, s.couleur AS service_assigne_couleur,
               d.agent_assigne_id,
               d.agent_service_id, CONCAT(agt.prenom, ' ', agt.nom) AS agent_service_nom,
               d.created_at, d.updated_at, d.date_prise_en_charge,
               d.date_planification, d.date_resolution, d.date_cloture, d.source,
               EXTRACT(EPOCH FROM (COALESCE(d.date_resolution, CURRENT_TIMESTAMP) - d.created_at))/3600 AS heures
        FROM demandes_citoyens d
        LEFT JOIN demandes_categories c ON d.categorie_id = c.id
        LEFT JOIN demandes_categories cp ON c.parent_id = cp.id
        LEFT JOIN perimetres p ON d.quartier_id = p.id
        LEFT JOIN demandes_services s ON d.service_assigne_id = s.id
        LEFT JOIN demandes_services_agents agt ON d.agent_service_id = agt.id
        WHERE d.id = CAST(:id AS uuid)
    """), {"id": demande_id})

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    return DemandeResponse(
        id=str(row.id),
        project_id=str(row.project_id),
        numero_suivi=row.numero_suivi,
        categorie_id=str(row.categorie_id),
        categorie_nom=row.categorie_nom,
        categorie_icone=row.categorie_icone,
        categorie_couleur=row.categorie_couleur,
        categorie_parent_nom=row.categorie_parent_nom,
        declarant_email=row.declarant_email,
        declarant_telephone=row.declarant_telephone,
        declarant_nom=row.declarant_nom,
        declarant_langue=row.declarant_langue,
        description=row.description,
        champs_supplementaires=row.champs_supplementaires or {},
        photos=[f for f in (row.photos or []) if any(f.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'))] if isinstance(row.photos, list) else (row.photos or []),
        documents=[f for f in (row.photos or []) if isinstance(f, str) and not any(f.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'))] if isinstance(row.photos, list) else [],
        photos_intervention=row.photos_intervention or [],
        latitude=row.latitude,
        longitude=row.longitude,
        adresse_approximative=row.adresse_approximative,
        quartier_id=str(row.quartier_id) if row.quartier_id else None,
        quartier_nom=row.quartier_nom,
        equipement_id=str(row.equipement_id) if row.equipement_id else None,
        statut=DemandeStatut(row.statut),
        priorite=DemandePriorite(row.priorite),
        service_assigne_id=str(row.service_assigne_id) if row.service_assigne_id else None,
        service_assigne_nom=row.service_assigne_nom,
        service_assigne_couleur=row.service_assigne_couleur,
        agent_assigne_id=str(row.agent_assigne_id) if row.agent_assigne_id else None,
        agent_service_id=str(row.agent_service_id) if row.agent_service_id else None,
        agent_service_nom=row.agent_service_nom,
        created_at=row.created_at,
        updated_at=row.updated_at,
        date_prise_en_charge=row.date_prise_en_charge,
        date_planification=row.date_planification,
        date_resolution=row.date_resolution,
        date_cloture=row.date_cloture,
        source=row.source,
        heures_depuis_creation=row.heures,
    )


@router.put("/{demande_id}", response_model=DemandeResponse)
async def update_demande(
    demande_id: str,
    update: DemandeUpdateAgent,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Met à jour une demande (changement statut, assignation, réponse)."""
    # Récupérer la demande actuelle
    current = await db.execute(text("""
        SELECT statut, declarant_email FROM demandes_citoyens WHERE id = :id
    """), {"id": demande_id})
    current_row = current.fetchone()

    if not current_row:
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    old_statut = current_row.statut

    # Construire la mise à jour
    updates = []
    params = {"id": demande_id}

    if update.statut:
        updates.append("statut = :statut")
        params["statut"] = update.statut.value

        # Dates automatiques selon le statut
        if update.statut == DemandeStatut.en_cours and old_statut == "nouveau":
            updates.append("date_prise_en_charge = CURRENT_TIMESTAMP")
        elif update.statut == DemandeStatut.traite:
            updates.append("date_resolution = CURRENT_TIMESTAMP")
        elif update.statut == DemandeStatut.cloture:
            updates.append("date_cloture = CURRENT_TIMESTAMP")

    if update.priorite:
        updates.append("priorite = :priorite")
        params["priorite"] = update.priorite.value

    if update.service_assigne_id is not None:
        updates.append("service_assigne_id = :service_id")
        params["service_id"] = update.service_assigne_id or None

    if update.agent_assigne_id is not None:
        updates.append("agent_assigne_id = :agent_id")
        params["agent_id"] = update.agent_assigne_id or None

    if update.date_planification:
        updates.append("date_planification = :date_planif")
        params["date_planif"] = update.date_planification

    if not updates and not update.commentaire:
        raise HTTPException(status_code=400, detail="Aucune modification")

    # Exécuter la mise à jour
    if updates:
        # Sécurité : vérifier que les colonnes sont dans la whitelist
        ALLOWED_UPDATE_COLS = {
            "statut", "priorite", "service_assigne_id", "agent_assigne_id",
            "agent_service_id", "date_planification", "updated_at",
            "commentaire_interne", "description",
            "date_prise_en_charge", "date_resolution", "date_cloture",
        }
        for u in updates:
            col_name = u.split("=")[0].strip()
            if col_name not in ALLOWED_UPDATE_COLS:
                raise HTTPException(status_code=400, detail=f"Colonne non autorisée: {col_name}")

        updates.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE demandes_citoyens SET {', '.join(updates)} WHERE id = :id"
        await db.execute(text(query), params)

    # Ajouter à l'historique
    action = HistoriqueAction.commentaire
    if update.statut and update.statut.value != old_statut:
        action = HistoriqueAction.changement_statut

    await db.execute(text("""
        INSERT INTO demandes_historique (
            demande_id, agent_id, agent_nom, action,
            ancien_statut, nouveau_statut, commentaire, commentaire_interne
        )
        VALUES (
            CAST(:demande_id AS uuid), CAST(:agent_id AS uuid), :agent_nom, :action,
            :ancien_statut, :nouveau_statut, :commentaire, :interne
        )
    """), {
        "demande_id": demande_id,
        "agent_id": current_user.get("id"),
        "agent_nom": f"{current_user.get('prenom', '')} {current_user.get('nom', '')}".strip() or current_user.get("email"),
        "action": action.value,
        "ancien_statut": old_statut,
        "nouveau_statut": update.statut.value if update.statut else old_statut,
        "commentaire": update.commentaire,
        "interne": update.commentaire_interne,
    })

    await db.commit()

    # Envoyer email si demandé ou si changement de statut important
    statuts_avec_notif = ["envoye", "en_cours", "accepte", "planifie", "traite", "rejete"]
    should_notify = (
        (update.envoyer_email and update.commentaire) or
        (update.statut and update.statut.value in statuts_avec_notif and update.statut.value != old_statut)
    )

    if should_notify and not update.commentaire_interne:
        from config import settings

        # Récupérer les infos complètes de la demande
        demande_info = await db.execute(text("""
            SELECT
                d.numero_suivi, d.description,
                d.declarant_email, d.declarant_nom, d.declarant_langue,
                d.date_planification,
                c.nom as categorie_nom
            FROM demandes_citoyens d
            LEFT JOIN demandes_categories c ON d.categorie_id = c.id
            WHERE d.id = :id
        """), {"id": demande_id})
        demande_row = demande_info.fetchone()

        if demande_row:
            # Récupérer le project_id
            project_result = await db.execute(text("""
                SELECT project_id FROM demandes_citoyens WHERE id = :id
            """), {"id": demande_id})
            project_id = project_result.scalar()

            demande_data = {
                "numero_suivi": demande_row.numero_suivi,
                "description": demande_row.description,
                "declarant_email": demande_row.declarant_email,
                "declarant_nom": demande_row.declarant_nom,
                "declarant_langue": demande_row.declarant_langue or "fr",
                "categorie_nom": demande_row.categorie_nom,
                "date_planification": demande_row.date_planification,
            }

            background_tasks.add_task(
                send_demande_status_email,
                settings.database_url,
                project_id,
                demande_data,
                update.statut.value if update.statut else old_statut,
                update.commentaire,
            )

            # Marquer l'email comme envoyé dans l'historique
            await db.execute(text("""
                UPDATE demandes_historique
                SET email_envoye = TRUE
                WHERE demande_id = :demande_id
                ORDER BY created_at DESC
                LIMIT 1
            """), {"demande_id": demande_id})
            await db.commit()

    # Notification service si nouvelle assignation
    if update.service_assigne_id:
        demande_info_result = await db.execute(text("""
            SELECT d.id, d.numero_suivi, d.description, d.adresse_approximative AS adresse,
                   c.nom AS categorie_nom
            FROM demandes_citoyens d
            LEFT JOIN demandes_categories c ON d.categorie_id = c.id
            WHERE d.id = CAST(:id AS uuid)
        """), {"id": demande_id})
        demande_info_row = demande_info_result.fetchone()
        if demande_info_row:
            background_tasks.add_task(
                notify_service_new_demande,
                db,
                {
                    "id": str(demande_info_row.id),
                    "numero_suivi": demande_info_row.numero_suivi,
                    "description": demande_info_row.description,
                    "adresse": demande_info_row.adresse,
                    "categorie_nom": demande_info_row.categorie_nom,
                },
                update.service_assigne_id,
            )

    # Planifier rappel si date de planification
    if update.date_planification:
        background_tasks.add_task(
            schedule_intervention_reminder,
            db,
            demande_id,
            update.date_planification,
            update.agent_assigne_id,
        )

    return await get_demande(demande_id, db, current_user)


@router.post("/{demande_id}/envoyer-email-photos")
async def send_email_with_photos(
    demande_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Envoie manuellement un email au citoyen avec les photos d'intervention jointes.
    Utile pour renvoyer les photos après que la demande a été traitée.
    """
    # Vérifier que la demande existe et récupérer les infos
    result = await db.execute(text("""
        SELECT d.id, d.numero_suivi, d.description,
               d.declarant_email, d.declarant_nom, d.declarant_langue,
               d.statut, d.photos_intervention,
               c.nom AS categorie_nom
        FROM demandes_citoyens d
        LEFT JOIN demandes_categories c ON d.categorie_id = c.id
        WHERE d.id = CAST(:id AS uuid)
    """), {"id": demande_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    if not row.declarant_email:
        raise HTTPException(status_code=400, detail="Pas d'email pour ce déclarant")

    if not row.photos_intervention or len(row.photos_intervention) == 0:
        raise HTTPException(status_code=400, detail="Aucune photo d'intervention disponible")

    # Préparer les données de la demande
    demande_data = {
        "id": str(row.id),
        "numero_suivi": row.numero_suivi,
        "description": row.description,
        "declarant_email": row.declarant_email,
        "declarant_nom": row.declarant_nom,
        "declarant_langue": row.declarant_langue or "fr",
        "categorie_nom": row.categorie_nom,
    }

    # Envoyer en arrière-plan
    from services.notifications import notify_citizen_status_changed
    background_tasks.add_task(
        notify_citizen_status_changed,
        db,
        demande_data,
        "traite",
        "Voici les photos de l'intervention réalisée.",
        True  # include_photos
    )

    # Logger l'action dans l'historique
    await db.execute(text("""
        INSERT INTO demandes_historique (
            demande_id, agent_id, agent_nom, action,
            ancien_statut, nouveau_statut, commentaire
        )
        VALUES (
            CAST(:demande_id AS uuid), :agent_id, :agent_nom, 'email_photos',
            :statut, :statut, 'Email envoyé avec photos d''intervention'
        )
    """), {
        "demande_id": demande_id,
        "agent_id": current_user.get("id"),
        "agent_nom": current_user.get("name", current_user.get("email")),
        "statut": row.statut,
    })
    await db.commit()

    return {
        "success": True,
        "message": f"Email avec {len(row.photos_intervention)} photo(s) envoyé à {row.declarant_email}"
    }


@router.get("/{demande_id}/historique", response_model=List[HistoriqueResponse])
async def get_demande_historique(
    demande_id: str,
    include_interne: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère l'historique complet d'une demande."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        query = """
            SELECT id, demande_id, agent_id, agent_nom, action,
                   ancien_statut, nouveau_statut, commentaire,
                   COALESCE(commentaire_interne, FALSE) as commentaire_interne,
                   COALESCE(email_envoye, FALSE) as email_envoye,
                   email_sujet, created_at
            FROM demandes_historique
            WHERE demande_id = CAST(:demande_id AS uuid)
        """
        if not include_interne:
            query += " AND COALESCE(commentaire_interne, FALSE) = FALSE"
        query += " ORDER BY created_at ASC"

        result = await db.execute(text(query), {"demande_id": demande_id})
        rows = result.fetchall()

        historique = []
        for row in rows:
            try:
                action = HistoriqueAction(row.action)
            except ValueError:
                logger.warning(f"Action inconnue dans historique: '{row.action}' pour demande {demande_id}")
                action = HistoriqueAction.commentaire  # fallback

            historique.append(HistoriqueResponse(
                id=str(row.id),
                demande_id=str(row.demande_id),
                agent_id=str(row.agent_id) if row.agent_id else None,
                agent_nom=row.agent_nom,
                action=action,
                ancien_statut=row.ancien_statut,
                nouveau_statut=row.nouveau_statut,
                commentaire=row.commentaire,
                commentaire_interne=row.commentaire_interne,
                email_envoye=row.email_envoye,
                email_sujet=row.email_sujet,
                created_at=row.created_at,
            ))
        return historique

    except Exception as e:
        logger.error(f"Erreur historique demande {demande_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur historique: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIONS RAPIDES SUR DEMANDES
# ═══════════════════════════════════════════════════════════════════════════════

@router.patch("/{demande_id}/statut")
async def update_demande_statut(
    demande_id: str,
    statut: DemandeStatut,
    commentaire: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Change le statut d'une demande."""
    update = DemandeUpdateAgent(statut=statut, commentaire=commentaire)
    return await update_demande(demande_id, update, background_tasks, db, current_user)


@router.patch("/{demande_id}/assigner")
async def assigner_demande(
    demande_id: str,
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Assigne une demande à un agent."""
    update = DemandeUpdateAgent(agent_assigne_id=agent_id)
    return await update_demande(demande_id, update, BackgroundTasks(), db, current_user)


@router.patch("/{demande_id}/planifier")
async def planifier_demande(
    demande_id: str,
    date_planification: date,
    commentaire: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Planifie une intervention pour une demande."""
    update = DemandeUpdateAgent(
        statut=DemandeStatut.planifie,
        date_planification=date_planification,
        commentaire=commentaire
    )
    return await update_demande(demande_id, update, BackgroundTasks(), db, current_user)


class PrioriteUpdate(BaseModel):
    priorite: DemandePriorite


@router.patch("/{demande_id}/priorite")
async def update_demande_priorite(
    demande_id: str,
    body: PrioriteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Change la priorité d'une demande."""
    update = DemandeUpdateAgent(priorite=body.priorite)
    return await update_demande(demande_id, update, BackgroundTasks(), db, current_user)


@router.post("/{demande_id}/commentaires")
async def add_demande_commentaire(
    demande_id: str,
    contenu: str,
    interne: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Ajoute un commentaire à une demande."""
    # Vérifier que la demande existe
    check = await db.execute(
        text("SELECT id FROM demandes_citoyens WHERE id = :id"),
        {"id": demande_id}
    )
    if not check.fetchone():
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    # Ajouter le commentaire à l'historique
    await db.execute(text("""
        INSERT INTO demandes_historique (
            demande_id, agent_id, agent_nom, action, commentaire, commentaire_interne
        )
        VALUES (:demande_id, :agent_id, :agent_nom, 'commentaire', :commentaire, :interne)
    """), {
        "demande_id": demande_id,
        "agent_id": current_user.get("id"),
        "agent_nom": current_user.get("email", "Agent"),
        "commentaire": contenu,
        "interne": interne,
    })
    await db.commit()

    return {"message": "Commentaire ajouté", "demande_id": demande_id}


# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGES TCHAT (DEMANDES ↔ SERVICE TERRAIN)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{demande_id}/messages", response_model=List[MessageResponse])
async def list_demande_messages(
    demande_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Liste les messages tchat d'une demande."""
    # Vérifier que la demande existe
    check = await db.execute(
        text("SELECT id FROM demandes_citoyens WHERE id = CAST(:id AS uuid)"),
        {"id": demande_id}
    )
    if not check.fetchone():
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    # Récupérer les messages du canal backoffice uniquement
    result = await db.execute(text("""
        SELECT id, demande_id, sender_type, sender_id, sender_nom, message,
               lu_par_service, lu_par_demandes, created_at
        FROM demandes_messages
        WHERE demande_id = CAST(:demande_id AS uuid)
          AND COALESCE(canal, 'backoffice') = 'backoffice'
        ORDER BY created_at ASC
    """), {"demande_id": demande_id})
    messages = result.fetchall()

    return [
        MessageResponse(
            id=str(m.id),
            demande_id=str(m.demande_id),
            sender_type=m.sender_type,
            sender_id=str(m.sender_id) if m.sender_id else None,
            sender_nom=m.sender_nom or "Inconnu",
            message=m.message,
            lu_par_service=m.lu_par_service,
            lu_par_demandes=m.lu_par_demandes,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.post("/{demande_id}/messages", response_model=MessageResponse, status_code=201)
async def create_demande_message(
    demande_id: str,
    data: MessageCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Envoie un message tchat (côté back-office demandes)."""
    # Vérifier que la demande existe et récupérer infos pour notification
    check = await db.execute(
        text("""
            SELECT d.id, d.numero_suivi, d.service_assigne_id
            FROM demandes_citoyens d
            WHERE d.id = CAST(:id AS uuid)
        """),
        {"id": demande_id}
    )
    demande_row = check.fetchone()
    if not demande_row:
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    # Créer le message (sender_type = 'demandes' pour le back-office)
    sender_nom = current_user.get("email", "Agent")
    if current_user.get("prenom") or current_user.get("nom"):
        sender_nom = f"{current_user.get('prenom', '')} {current_user.get('nom', '')}".strip()

    result = await db.execute(text("""
        INSERT INTO demandes_messages (
            demande_id, sender_type, sender_id, sender_nom, message, lu_par_demandes, canal
        )
        VALUES (
            CAST(:demande_id AS uuid), 'demandes', CAST(:sender_id AS uuid), :sender_nom, :message, TRUE, 'backoffice'
        )
        RETURNING id, demande_id, sender_type, sender_id, sender_nom, message,
                  lu_par_service, lu_par_demandes, created_at
    """), {
        "demande_id": demande_id,
        "sender_id": current_user.get("id"),
        "sender_nom": sender_nom,
        "message": data.message,
    })
    await db.commit()
    m = result.fetchone()

    # Notifier les agents du service si un service est assigné
    if demande_row.service_assigne_id:
        background_tasks.add_task(
            notify_agent_new_message,
            db,
            {
                "id": str(demande_row.id),
                "numero_suivi": demande_row.numero_suivi,
                "service_assigne_id": str(demande_row.service_assigne_id),
            },
            data.message,
            sender_nom,
        )

    return MessageResponse(
        id=str(m.id),
        demande_id=str(m.demande_id),
        sender_type=m.sender_type,
        sender_id=str(m.sender_id) if m.sender_id else None,
        sender_nom=m.sender_nom,
        message=m.message,
        lu_par_service=m.lu_par_service,
        lu_par_demandes=m.lu_par_demandes,
        created_at=m.created_at,
    )


@router.put("/{demande_id}/messages/marquer-lu")
async def mark_messages_as_read(
    demande_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Marque tous les messages backoffice de la demande comme lus par le back-office."""
    result = await db.execute(text("""
        UPDATE demandes_messages
        SET lu_par_demandes = TRUE
        WHERE demande_id = CAST(:demande_id AS uuid)
          AND lu_par_demandes = FALSE
          AND COALESCE(canal, 'backoffice') = 'backoffice'
        RETURNING id
    """), {"demande_id": demande_id})
    await db.commit()
    updated = result.fetchall()

    return {"marked_as_read": len(updated)}


# ═══════════════════════════════════════════════════════════════════════════════
# QUARTIERS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/quartiers", response_model=List[QuartierResponse])
async def list_quartiers(
    project_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Liste les quartiers d'un projet."""
    result = await db.execute(text("""
        SELECT p.id, p.name, p.description, p.color, p.population,
               p.code_iris, p.code_insee, p.project_id, p.perimetre_type,
               p.created_at, p.updated_at,
               COUNT(d.id) AS total_demandes,
               COUNT(d.id) FILTER (WHERE d.statut IN ('nouveau', 'en_cours', 'planifie')) AS demandes_en_cours
        FROM perimetres p
        LEFT JOIN demandes_citoyens d ON d.quartier_id = p.id
        WHERE p.project_id = :project_id AND p.perimetre_type = 'quartier'
        GROUP BY p.id
        ORDER BY p.name
    """), {"project_id": project_id})

    return [
        QuartierResponse(
            id=str(row.id),
            name=row.name,
            description=row.description,
            color=row.color,
            population=row.population,
            code_iris=row.code_iris,
            code_insee=row.code_insee,
            project_id=str(row.project_id) if row.project_id else None,
            perimetre_type=row.perimetre_type,
            created_at=row.created_at,
            updated_at=row.updated_at,
            total_demandes=row.total_demandes,
            demandes_en_cours=row.demandes_en_cours,
        )
        for row in result.fetchall()
    ]


@router.post("/quartiers/import-iris", response_model=IRISImportResponse)
async def import_iris(
    project_id: str,
    request: IRISImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Importe les quartiers IRIS depuis data.gouv.fr pour une commune.
    Code commune: 5 chiffres (ex: 75056 pour Paris).
    """
    code_commune = request.code_commune
    errors = []
    imported = 0
    ignored = 0

    try:
        # URL de l'API Geo de data.gouv.fr
        # https://geo.api.gouv.fr/communes/{code}/iris
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://geo.api.gouv.fr/communes/{code_commune}",
                params={"fields": "nom", "geometry": "contour", "format": "geojson"}
            )

            if response.status_code == 404:
                return IRISImportResponse(
                    success=False,
                    message=f"Commune {code_commune} non trouvée",
                    errors=["Code commune invalide"],
                )

            commune_data = response.json()

            # Récupérer les IRIS
            iris_response = await client.get(
                f"https://geo.api.gouv.fr/communes/{code_commune}/iris",
                params={"format": "geojson"}
            )

            if iris_response.status_code != 200:
                # Commune sans IRIS (< 5000 hab), importer le contour de la commune
                geom = commune_data.get("geometry")
                if geom and geom.get("type") in ["Polygon", "MultiPolygon"]:
                    # Créer un seul quartier pour toute la commune
                    coords = geom["coordinates"][0]
                    wkt = f"POLYGON(({', '.join([f'{c[0]} {c[1]}' for c in coords])}))"

                    await db.execute(text("""
                        INSERT INTO perimetres (name, project_id, perimetre_type, geom, code_insee)
                        VALUES (:name, :project_id, 'quartier', ST_GeomFromText(:wkt, 4326), :code)
                        ON CONFLICT DO NOTHING
                    """), {
                        "name": commune_data.get("properties", {}).get("nom", f"Commune {code_commune}"),
                        "project_id": project_id,
                        "wkt": wkt,
                        "code": code_commune,
                    })

                    await db.commit()
                    imported = 1

                    return IRISImportResponse(
                        success=True,
                        quartiers_importes=1,
                        message=f"Commune importée (pas d'IRIS disponible pour les communes < 5000 hab)",
                    )
                else:
                    return IRISImportResponse(
                        success=False,
                        message="Pas de données géographiques disponibles",
                        errors=["Contour de commune non disponible"],
                    )

            iris_data = iris_response.json()

            # Supprimer les existants si demandé
            if request.remplacer_existants:
                await db.execute(text("""
                    DELETE FROM perimetres
                    WHERE project_id = :project_id
                      AND perimetre_type = 'quartier'
                      AND code_insee = :code
                """), {"project_id": project_id, "code": code_commune})

            # Importer chaque IRIS
            for feature in iris_data.get("features", []):
                try:
                    props = feature.get("properties", {})
                    geom = feature.get("geometry", {})

                    if geom.get("type") != "Polygon":
                        ignored += 1
                        continue

                    coords = geom["coordinates"][0]
                    wkt = f"POLYGON(({', '.join([f'{c[0]} {c[1]}' for c in coords])}))"

                    iris_code = props.get("code", "")
                    iris_nom = props.get("nom", f"IRIS {iris_code}")

                    result = await db.execute(text("""
                        INSERT INTO perimetres (
                            name, description, project_id, perimetre_type,
                            geom, code_iris, code_insee
                        )
                        VALUES (
                            :name, :description, :project_id, 'quartier',
                            ST_GeomFromText(:wkt, 4326), :code_iris, :code_insee
                        )
                        ON CONFLICT DO NOTHING
                        RETURNING id
                    """), {
                        "name": iris_nom,
                        "description": f"IRIS {iris_code} - {props.get('type_iris', '')}",
                        "project_id": project_id,
                        "wkt": wkt,
                        "code_iris": iris_code,
                        "code_insee": code_commune,
                    })

                    if result.fetchone():
                        imported += 1
                    else:
                        ignored += 1

                except Exception as e:
                    errors.append(f"Erreur IRIS {props.get('code', '?')}: {str(e)}")
                    ignored += 1

            await db.commit()

            return IRISImportResponse(
                success=True,
                quartiers_importes=imported,
                quartiers_ignores=ignored,
                errors=errors,
                message=f"Import terminé: {imported} quartiers importés, {ignored} ignorés",
            )

    except httpx.TimeoutException:
        return IRISImportResponse(
            success=False,
            message="Timeout lors de la connexion à data.gouv.fr",
            errors=["Service data.gouv.fr non disponible"],
        )
    except Exception as e:
        await db.rollback()
        return IRISImportResponse(
            success=False,
            message=f"Erreur lors de l'import: {str(e)}",
            errors=[str(e)],
        )


# ═══════════════════════════════════════════════════════════════════════════════
# DÉTECTION DES DOUBLONS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/public/doublons/check", response_model=DoublonCheckResponse)
async def check_doublons_public(
    project_id: str,
    check: DoublonCheck,
    db: AsyncSession = Depends(get_db),
):
    """
    Vérifie s'il existe des demandes similaires à proximité.
    API publique utilisable par le portail citoyen avant soumission.
    """
    try:
        # Utiliser la fonction SQL de détection des doublons
        result = await db.execute(text("""
            SELECT * FROM find_duplicate_demandes(
                CAST(:categorie_id AS uuid),
                :lat,
                :lng,
                CAST(:project_id AS uuid),
                :rayon,
                :jours
            )
        """), {
            "categorie_id": check.categorie_id,
            "lat": check.latitude,
            "lng": check.longitude,
            "project_id": project_id,
            "rayon": check.rayon_metres,
            "jours": check.jours,
        })

        rows = result.fetchall()
        doublons = []

        for row in rows:
            # Calculer le score de similarité
            days_diff = (datetime.now(row.created_at.tzinfo) - row.created_at).days
            score = calculate_similarity_score(row.distance_metres, days_diff)

            doublons.append(DoublonPotentiel(
                id=str(row.id),
                numero_suivi=row.numero_suivi,
                description=row.description[:200] + "..." if len(row.description) > 200 else row.description,
                statut=row.statut,
                distance_metres=round(row.distance_metres, 1),
                created_at=row.created_at,
                declarant_email=mask_email(row.declarant_email),
                photos=row.photos or [],
                score_similarite=score,
            ))

        message = "Aucun doublon potentiel détecté"
        if len(doublons) > 0:
            message = f"{len(doublons)} demande(s) similaire(s) détectée(s) à proximité"

        return DoublonCheckResponse(
            doublons_trouves=len(doublons),
            doublons=doublons,
            message=message,
        )

    except Exception as e:
        # Si la fonction SQL n'existe pas encore, fallback sur requête simple
        if "find_duplicate_demandes" in str(e):
            # Requête SQL directe sans la fonction
            result = await db.execute(text("""
                SELECT
                    d.id,
                    d.numero_suivi,
                    d.description,
                    d.statut,
                    ST_Distance(
                        d.geom::geography,
                        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                    ) AS distance_metres,
                    d.created_at,
                    d.declarant_email,
                    d.photos
                FROM demandes_citoyens d
                WHERE d.project_id = CAST(:project_id AS uuid)
                  AND d.categorie_id = CAST(:categorie_id AS uuid)
                  AND d.geom IS NOT NULL
                  AND d.created_at >= (CURRENT_TIMESTAMP - (:jours || ' days')::INTERVAL)
                  AND d.statut NOT IN ('rejete', 'cloture')
                  AND COALESCE(d.est_doublon, FALSE) = FALSE
                  AND ST_DWithin(
                      d.geom::geography,
                      ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                      :rayon
                  )
                ORDER BY distance_metres ASC
                LIMIT 10
            """), {
                "categorie_id": check.categorie_id,
                "lat": check.latitude,
                "lng": check.longitude,
                "project_id": project_id,
                "rayon": check.rayon_metres,
                "jours": check.jours,
            })

            rows = result.fetchall()
            doublons = []

            for row in rows:
                days_diff = (datetime.now(row.created_at.tzinfo) - row.created_at).days if row.created_at.tzinfo else (datetime.now() - row.created_at.replace(tzinfo=None)).days
                score = calculate_similarity_score(row.distance_metres, days_diff)

                doublons.append(DoublonPotentiel(
                    id=str(row.id),
                    numero_suivi=row.numero_suivi,
                    description=row.description[:200] + "..." if len(row.description) > 200 else row.description,
                    statut=row.statut,
                    distance_metres=round(row.distance_metres, 1),
                    created_at=row.created_at,
                    declarant_email=mask_email(row.declarant_email),
                    photos=row.photos or [],
                    score_similarite=score,
                ))

            message = "Aucun doublon potentiel détecté"
            if len(doublons) > 0:
                message = f"{len(doublons)} demande(s) similaire(s) détectée(s) à proximité"

            return DoublonCheckResponse(
                doublons_trouves=len(doublons),
                doublons=doublons,
                message=message,
            )
        raise HTTPException(status_code=500, detail=f"Erreur vérification doublons: {str(e)}")


def calculate_similarity_score(distance_metres: float, days_diff: int) -> int:
    """Calcule un score de similarité entre 0 et 100."""
    score = 0

    # Score basé sur la distance (max 50 points)
    # 0m = 50 points, 50m = 0 points
    if distance_metres < 50:
        score += max(0, int(50 - distance_metres))

    # Score basé sur la date (max 50 points)
    # 0 jours = 50 points, 30 jours = 0 points
    if days_diff < 30:
        score += max(0, int(50 - (days_diff * 50 / 30)))

    return min(100, score)


def mask_email(email: str) -> str:
    """Masque partiellement un email pour la vie privée."""
    if not email or "@" not in email:
        return "***@***"
    parts = email.split("@")
    user = parts[0]
    domain = parts[1]
    if len(user) <= 2:
        masked_user = user[0] + "***"
    else:
        masked_user = user[0] + "***" + user[-1]
    return f"{masked_user}@{domain}"


@router.get("/{demande_id}/doublons", response_model=List[DoublonPotentiel])
async def get_demande_doublons(
    demande_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Récupère les doublons potentiels d'une demande existante.
    Utilisé dans le back-office pour la modération.
    """
    # Récupérer la demande
    demande = await db.execute(text("""
        SELECT d.categorie_id, ST_Y(d.geom) as lat, ST_X(d.geom) as lng, d.project_id
        FROM demandes_citoyens d
        WHERE d.id = :id
    """), {"id": demande_id})
    row = demande.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Demande non trouvée")

    if not row.lat or not row.lng:
        return []

    # Chercher les doublons
    result = await db.execute(text("""
        SELECT
            d.id,
            d.numero_suivi,
            d.description,
            d.statut,
            ST_Distance(
                d.geom::geography,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
            ) AS distance_metres,
            d.created_at,
            d.declarant_email,
            d.photos
        FROM demandes_citoyens d
        WHERE d.project_id = CAST(:project_id AS uuid)
          AND d.categorie_id = CAST(:categorie_id AS uuid)
          AND d.geom IS NOT NULL
          AND d.id != CAST(:exclude_id AS uuid)
          AND d.created_at >= (CURRENT_TIMESTAMP - INTERVAL '30 days')
          AND d.statut NOT IN ('rejete', 'cloture')
          AND COALESCE(d.est_doublon, FALSE) = FALSE
          AND ST_DWithin(
              d.geom::geography,
              ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
              50
          )
        ORDER BY distance_metres ASC
        LIMIT 10
    """), {
        "categorie_id": str(row.categorie_id),
        "lat": row.lat,
        "lng": row.lng,
        "project_id": str(row.project_id),
        "exclude_id": demande_id,
    })

    doublons = []
    for r in result.fetchall():
        days_diff = (datetime.now(r.created_at.tzinfo) - r.created_at).days if r.created_at.tzinfo else (datetime.now() - r.created_at.replace(tzinfo=None)).days
        score = calculate_similarity_score(r.distance_metres, days_diff)

        doublons.append(DoublonPotentiel(
            id=str(r.id),
            numero_suivi=r.numero_suivi,
            description=r.description[:200] + "..." if len(r.description) > 200 else r.description,
            statut=r.statut,
            distance_metres=round(r.distance_metres, 1),
            created_at=r.created_at,
            declarant_email=r.declarant_email,  # Pas de masquage pour les agents
            photos=r.photos or [],
            score_similarite=score,
        ))

    return doublons


@router.get("/{demande_id}/doublons-lies")
async def get_doublons_lies(
    demande_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Récupère les demandes qui sont des doublons de la demande spécifiée.
    """
    result = await db.execute(text("""
        SELECT
            d.id,
            d.numero_suivi,
            d.description,
            d.statut,
            d.created_at,
            d.declarant_email
        FROM demandes_citoyens d
        WHERE d.doublon_de_id = CAST(:demande_id AS uuid)
        ORDER BY d.created_at DESC
    """), {"demande_id": demande_id})

    return [
        {
            "id": str(r.id),
            "numero_suivi": r.numero_suivi,
            "description": r.description[:100] + "..." if len(r.description) > 100 else r.description,
            "statut": r.statut,
            "created_at": r.created_at,
            "declarant_email": r.declarant_email,
        }
        for r in result.fetchall()
    ]


@router.post("/{demande_id}/marquer-doublon")
async def marquer_comme_doublon(
    demande_id: str,
    data: DoublonMarquer,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Marque une demande comme doublon d'une autre.
    Change le statut en 'cloture' et lie à la demande originale.
    """
    # Vérifier que les deux demandes existent
    check_result = await db.execute(text("""
        SELECT id, numero_suivi FROM demandes_citoyens
        WHERE id IN (CAST(:id1 AS uuid), CAST(:id2 AS uuid))
    """), {"id1": demande_id, "id2": data.doublon_de_id})

    found = check_result.fetchall()
    if len(found) != 2:
        raise HTTPException(status_code=404, detail="Demande(s) non trouvée(s)")

    # Marquer comme doublon
    await db.execute(text("""
        UPDATE demandes_citoyens
        SET doublon_de_id = CAST(:original_id AS uuid),
            est_doublon = TRUE,
            statut = 'cloture',
            date_cloture = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = CAST(:demande_id AS uuid)
    """), {
        "demande_id": demande_id,
        "original_id": data.doublon_de_id,
    })

    # Ajouter à l'historique
    await db.execute(text("""
        INSERT INTO demandes_historique (
            demande_id, agent_id, agent_nom, action,
            ancien_statut, nouveau_statut, commentaire
        )
        VALUES (
            CAST(:demande_id AS uuid), :agent_id, :agent_nom, 'cloture',
            (SELECT statut FROM demandes_citoyens WHERE id = CAST(:demande_id AS uuid)),
            'cloture',
            :commentaire
        )
    """), {
        "demande_id": demande_id,
        "agent_id": current_user.get("id"),
        "agent_nom": current_user.get("name", current_user.get("email")),
        "commentaire": data.commentaire or f"Marqué comme doublon de la demande originale",
    })

    await db.commit()

    return {
        "success": True,
        "message": "Demande marquée comme doublon",
        "demande_id": demande_id,
        "doublon_de_id": data.doublon_de_id,
    }


@router.post("/{demande_id}/dissocier-doublon")
async def dissocier_doublon(
    demande_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Dissocie une demande précédemment marquée comme doublon.
    Remet le statut à 'nouveau'.
    """
    result = await db.execute(text("""
        UPDATE demandes_citoyens
        SET doublon_de_id = NULL,
            est_doublon = FALSE,
            statut = 'nouveau',
            date_cloture = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = CAST(:demande_id AS uuid) AND est_doublon = TRUE
        RETURNING id
    """), {"demande_id": demande_id})

    if not result.fetchone():
        raise HTTPException(
            status_code=404,
            detail="Demande non trouvée ou n'est pas un doublon"
        )

    # Ajouter à l'historique
    await db.execute(text("""
        INSERT INTO demandes_historique (
            demande_id, agent_id, agent_nom, action,
            ancien_statut, nouveau_statut, commentaire
        )
        VALUES (
            CAST(:demande_id AS uuid), :agent_id, :agent_nom, 'reouverture',
            'cloture', 'nouveau',
            'Doublon dissocié - demande réouverte'
        )
    """), {
        "demande_id": demande_id,
        "agent_id": current_user.get("id"),
        "agent_nom": current_user.get("name", current_user.get("email")),
    })

    await db.commit()

    return {
        "success": True,
        "message": "Doublon dissocié, demande réouverte",
        "demande_id": demande_id,
    }
