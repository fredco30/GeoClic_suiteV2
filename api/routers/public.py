"""
Router pour le portail citoyen public.
Endpoints SANS authentification pour consultation et signalements.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime
import logging
import json

from database import get_db
from schemas.public import (
    # Équipements
    EquipmentPublic,
    EquipmentListResponse,
    PhotoPublic,
    # Signalements
    SignalementCreate,
    SignalementResponse,
    SignalementStatusResponse,
    SignalementStatut,
    # Catégories
    CategoryPublic,
    CategoriesResponse,
    # Carte
    MapMarker,
    MapBounds,
    MapDataResponse,
    # Utilitaires
    generate_tracking_number,
    int_to_hex_color,
    STATUT_LABELS,
)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS ÉQUIPEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/equipment/{identifier}", response_model=EquipmentPublic)
async def get_equipment(
    identifier: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Récupère les informations publiques d'un équipement.
    L'identifiant peut être un short_code (GC-XXXXXX) ou un UUID.
    Utilisé lors du scan d'un QR code.
    """
    try:
        # Déterminer si c'est un short_code ou un UUID
        is_short_code = identifier.startswith("GC-")

        if is_short_code:
            # Rechercher par short_code
            result = await db.execute(text("""
                SELECT sc.short_code, sc.point_id,
                       p.id, p.name, p.type, p.subtype, p.condition_state,
                       p.zone_name, p.photos, p.custom_properties,
                       p.updated_at, p.lexique_code,
                       ST_Y(p.geom) as latitude, ST_X(p.geom) as longitude,
                       l.label as type_label, l.icon_name, l.color_value
                FROM short_codes sc
                JOIN geoclic_staging p ON sc.point_id = p.id
                LEFT JOIN lexique l ON p.lexique_code = l.code
                WHERE sc.short_code = :code
            """), {"code": identifier})

            # Incrémenter le compteur de scans
            await db.execute(text("""
                UPDATE short_codes
                SET scans_count = scans_count + 1, last_scanned_at = CURRENT_TIMESTAMP
                WHERE short_code = :code
            """), {"code": identifier})
            await db.commit()
        else:
            # Rechercher par UUID
            result = await db.execute(text("""
                SELECT sc.short_code,
                       p.id, p.name, p.type, p.subtype, p.condition_state,
                       p.zone_name, p.photos, p.custom_properties,
                       p.updated_at, p.lexique_code,
                       ST_Y(p.geom) as latitude, ST_X(p.geom) as longitude,
                       l.label as type_label, l.icon_name, l.color_value
                FROM geoclic_staging p
                LEFT JOIN short_codes sc ON sc.point_id = p.id
                LEFT JOIN lexique l ON p.lexique_code = l.code
                WHERE p.id = :id
            """), {"id": identifier})

        row = result.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Équipement non trouvé",
            )

        # Parser les photos
        photos = []
        if row.photos:
            photos_data = row.photos if isinstance(row.photos, list) else json.loads(row.photos)
            for photo in photos_data[:5]:  # Max 5 photos publiques
                if isinstance(photo, dict):
                    photos.append(PhotoPublic(
                        url=photo.get('url', ''),
                        thumbnail_url=photo.get('thumbnail_url'),
                        caption=photo.get('caption'),
                    ))
                elif isinstance(photo, str):
                    photos.append(PhotoPublic(url=photo))

        # Construire la réponse
        return EquipmentPublic(
            id=str(row.id),
            short_code=row.short_code,
            name=row.name,
            category=row.type_label or row.type,
            subcategory=row.subtype,
            photos=photos,
            condition=row.condition_state,
            location=row.zone_name,
            latitude=row.latitude,
            longitude=row.longitude,
            custom_fields={},  # À filtrer selon configuration de visibilité
            last_updated=row.updated_at,
            can_report=True,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}",
        )


@router.get("/equipment/{identifier}/photos", response_model=List[PhotoPublic])
async def get_equipment_photos(
    identifier: str,
    db: AsyncSession = Depends(get_db),
):
    """Récupère les photos publiques d'un équipement."""
    try:
        is_short_code = identifier.startswith("GC-")

        if is_short_code:
            result = await db.execute(text("""
                SELECT p.photos
                FROM short_codes sc
                JOIN geoclic_staging p ON sc.point_id = p.id
                WHERE sc.short_code = :code
            """), {"code": identifier})
        else:
            result = await db.execute(text("""
                SELECT photos FROM geoclic_staging WHERE id = :id
            """), {"id": identifier})

        row = result.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Équipement non trouvé",
            )

        photos = []
        if row.photos:
            photos_data = row.photos if isinstance(row.photos, list) else json.loads(row.photos)
            for photo in photos_data:
                if isinstance(photo, dict):
                    photos.append(PhotoPublic(
                        url=photo.get('url', ''),
                        thumbnail_url=photo.get('thumbnail_url'),
                        caption=photo.get('caption'),
                    ))
                elif isinstance(photo, str):
                    photos.append(PhotoPublic(url=photo))

        return photos
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS SIGNALEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/report", response_model=SignalementResponse)
async def create_report(
    signalement: SignalementCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Crée un nouveau signalement citoyen.
    Nécessite un email ou un téléphone.
    """
    try:
        # Résoudre le point_id si short_code fourni
        point_id = signalement.point_id
        if signalement.short_code and not point_id:
            result = await db.execute(text("""
                SELECT point_id FROM short_codes WHERE short_code = :code
            """), {"code": signalement.short_code})
            row = result.fetchone()
            if row:
                point_id = str(row.point_id)

        # Générer le numéro de suivi
        numero_suivi = generate_tracking_number()

        # Photos en JSON
        photos_json = json.dumps(signalement.photos) if signalement.photos else "[]"

        # Récupérer les infos de la requête
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")[:500]

        # Insérer le signalement
        result = await db.execute(text("""
            INSERT INTO signalements (
                point_id, type_probleme, description, urgence,
                email, telephone, nom_signalant,
                latitude, longitude, adresse,
                photos, ip_address, user_agent
            )
            VALUES (
                :point_id, :type_probleme, :description, :urgence,
                :email, :telephone, :nom_signalant,
                :latitude, :longitude, :adresse,
                :photos::jsonb, :ip_address::inet, :user_agent
            )
            RETURNING id, created_at
        """), {
            "point_id": point_id,
            "type_probleme": signalement.type_probleme.value,
            "description": signalement.description,
            "urgence": signalement.urgence.value,
            "email": signalement.email,
            "telephone": signalement.telephone,
            "nom_signalant": signalement.nom_signalant,
            "latitude": signalement.latitude,
            "longitude": signalement.longitude,
            "adresse": signalement.adresse,
            "photos": photos_json,
            "ip_address": ip_address,
            "user_agent": user_agent,
        })

        await db.commit()
        row = result.fetchone()

        return SignalementResponse(
            id=str(row.id),
            numero_suivi=numero_suivi,
            statut=SignalementStatut.NOUVEAU,
            message="Votre signalement a été enregistré. Vous recevrez une notification lors de sa prise en charge.",
            created_at=row.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        # Vérifier si la table existe
        if "signalements" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Le système de signalement n'est pas encore configuré. Veuillez contacter l'administration.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'enregistrement du signalement: {str(e)}",
        )


@router.get("/report/{identifier}", response_model=SignalementStatusResponse)
async def get_report_status(
    identifier: str,
    email: Optional[str] = Query(None, description="Email pour vérification"),
    db: AsyncSession = Depends(get_db),
):
    """
    Consulte le statut d'un signalement.
    L'identifiant peut être le numéro de suivi (SIG-YYYY-XXXXX) ou l'UUID.
    """
    try:
        # Rechercher le signalement
        if identifier.startswith("SIG-"):
            # Note: Le numéro de suivi n'est pas stocké actuellement
            # On pourrait l'ajouter ou utiliser une recherche par email + date
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Recherche par numéro de suivi non encore implémentée. Utilisez l'UUID.",
            )
        else:
            query = """
                SELECT id, type_probleme, description, statut,
                       commentaire_public, created_at, updated_at
                FROM signalements
                WHERE id = :id
            """
            params = {"id": identifier}

            # Vérifier l'email si fourni (sécurité basique)
            if email:
                query = query.replace("WHERE id = :id", "WHERE id = :id AND email = :email")
                params["email"] = email

            result = await db.execute(text(query), params)

        row = result.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signalement non trouvé",
            )

        statut = SignalementStatut(row.statut)

        return SignalementStatusResponse(
            id=str(row.id),
            numero_suivi=f"SIG-{row.created_at.year}-{str(row.id)[:5].upper()}",
            type_probleme=row.type_probleme,
            description=row.description[:200] + "..." if len(row.description) > 200 else row.description,
            statut=statut,
            statut_label=STATUT_LABELS.get(statut, str(statut)),
            commentaire_public=row.commentaire_public,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS CARTE PUBLIQUE
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/map/points", response_model=MapDataResponse)
async def get_map_points(
    project_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    min_lng: Optional[float] = Query(None),
    max_lng: Optional[float] = Query(None),
    limit: int = Query(500, le=2000),
    db: AsyncSession = Depends(get_db),
):
    """
    Récupère les points pour affichage sur la carte publique.
    Données simplifiées pour performance.
    """
    try:
        query = """
            SELECT p.id, sc.short_code, p.name, p.type,
                   ST_Y(p.geom) as latitude, ST_X(p.geom) as longitude,
                   l.icon_name, l.color_value
            FROM geoclic_staging p
            LEFT JOIN short_codes sc ON sc.point_id = p.id
            LEFT JOIN lexique l ON p.lexique_code = l.code
            WHERE p.sync_status IN ('validated', 'published')
        """
        params = {}

        if project_id:
            query += " AND p.project_id = :project_id"
            params["project_id"] = project_id

        if category:
            query += " AND (p.type = :category OR p.lexique_code = :category OR p.lexique_code LIKE :category_prefix)"
            params["category"] = category
            params["category_prefix"] = f"{category}%"

        # Filtre géographique
        if all([min_lat, max_lat, min_lng, max_lng]):
            query += """
                AND ST_Intersects(
                    p.geom,
                    ST_MakeEnvelope(:min_lng, :min_lat, :max_lng, :max_lat, 4326)
                )
            """
            params.update({
                "min_lat": min_lat,
                "max_lat": max_lat,
                "min_lng": min_lng,
                "max_lng": max_lng,
            })

        query += f" LIMIT {limit}"

        result = await db.execute(text(query), params)
        rows = result.fetchall()

        markers = []
        for row in rows:
            if row.latitude and row.longitude:
                markers.append(MapMarker(
                    id=str(row.id),
                    short_code=row.short_code,
                    name=row.name,
                    category=row.type,
                    latitude=row.latitude,
                    longitude=row.longitude,
                    icon=row.icon_name,
                    color=int_to_hex_color(row.color_value),
                ))

        # Calculer les bounds si des points existent
        bounds = None
        if markers:
            lats = [m.latitude for m in markers]
            lngs = [m.longitude for m in markers]
            bounds = MapBounds(
                min_lat=min(lats),
                max_lat=max(lats),
                min_lng=min(lngs),
                max_lng=max(lngs),
            )

        return MapDataResponse(
            markers=markers,
            bounds=bounds,
            total=len(markers),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS CATÉGORIES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/categories", response_model=CategoriesResponse)
async def get_public_categories(
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Récupère les catégories visibles publiquement.
    Pour les filtres de la carte et des signalements.
    """
    try:
        query = """
            SELECT DISTINCT l.code, l.label, l.level, l.parent_code,
                   l.icon_name, l.color_value
            FROM lexique l
            WHERE l.is_active = TRUE
        """
        params = {}

        if project_id:
            query += " AND (l.project_id = :project_id OR l.project_id IS NULL)"
            params["project_id"] = project_id

        query += " ORDER BY l.level, l.display_order"

        result = await db.execute(text(query), params)
        rows = result.fetchall()

        # Construire l'arbre
        categories_map = {}
        root_categories = []

        for row in rows:
            cat = CategoryPublic(
                code=row.code,
                label=row.label,
                icon=row.icon_name,
                color=int_to_hex_color(row.color_value),
                children=[],
            )
            categories_map[row.code] = cat

            if row.parent_code is None:
                root_categories.append(cat)
            elif row.parent_code in categories_map:
                categories_map[row.parent_code].children.append(cat)

        return CategoriesResponse(categories=root_categories)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT TYPES DE PROBLÈMES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/report-types", response_model=List[dict])
async def get_report_types():
    """
    Récupère la liste des types de problèmes pour les signalements.
    """
    return [
        {"code": "Dégradation", "label": "Dégradation / Vandalisme", "icon": "mdi-hammer"},
        {"code": "Panne", "label": "Panne / Dysfonctionnement", "icon": "mdi-flash-off"},
        {"code": "Danger", "label": "Danger / Sécurité", "icon": "mdi-alert"},
        {"code": "Propreté", "label": "Propreté / Déchets", "icon": "mdi-trash-can"},
        {"code": "Accessibilité", "label": "Accessibilité PMR", "icon": "mdi-wheelchair-accessibility"},
        {"code": "Autre", "label": "Autre problème", "icon": "mdi-help-circle"},
    ]


@router.get("/urgency-levels", response_model=List[dict])
async def get_urgency_levels():
    """
    Récupère la liste des niveaux d'urgence pour les signalements.
    """
    return [
        {"code": "faible", "label": "Faible - Peut attendre", "color": "#4CAF50"},
        {"code": "normal", "label": "Normal", "color": "#2196F3"},
        {"code": "urgent", "label": "Urgent - À traiter rapidement", "color": "#FF9800"},
        {"code": "critique", "label": "Critique - Danger immédiat", "color": "#F44336"},
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# FORMULAIRE DE CONTACT (site commercial)
# ═══════════════════════════════════════════════════════════════════════════════

class ContactFormRequest(BaseModel):
    nom: str
    email: EmailStr
    collectivite: str = ""
    objet: str
    message: str


@router.post("/contact")
async def submit_contact_form(
    data: ContactFormRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reçoit un message du formulaire de contact du site commercial.
    Stocke en base et envoie un email de notification.
    SANS authentification (endpoint public).
    """
    logger = logging.getLogger("geoclic.contact")

    # Validation basique anti-spam
    if len(data.message) < 10:
        raise HTTPException(400, "Le message doit contenir au moins 10 caractères")
    if len(data.nom) < 2:
        raise HTTPException(400, "Nom invalide")

    # Stocker en base
    try:
        await db.execute(text("""
            INSERT INTO contact_messages (nom, email, collectivite, objet, message)
            VALUES (:nom, :email, :collectivite, :objet, :message)
        """), {
            "nom": data.nom,
            "email": data.email,
            "collectivite": data.collectivite,
            "objet": data.objet,
            "message": data.message,
        })
        await db.commit()
    except Exception as e:
        logger.warning(f"Erreur stockage contact (table manquante?): {e}")
        # Continue quand même - l'email sera envoyé

    # Envoyer un email de notification à l'admin
    try:
        from routers.settings import get_email_settings
        email_config = await get_email_settings(db)
        if email_config and email_config.get("smtp_host"):
            import smtplib
            from email.mime.text import MIMEText

            admin_email = email_config.get("smtp_from_email", "contact@geoclic.fr")
            msg = MIMEText(
                f"Nouveau message de contact GéoClic\n\n"
                f"Nom: {data.nom}\n"
                f"Email: {data.email}\n"
                f"Collectivité: {data.collectivite}\n"
                f"Objet: {data.objet}\n\n"
                f"Message:\n{data.message}",
                "plain", "utf-8"
            )
            msg["Subject"] = f"[GéoClic Contact] {data.objet} - {data.collectivite or data.nom}"
            msg["From"] = admin_email
            msg["To"] = admin_email
            msg["Reply-To"] = data.email

            with smtplib.SMTP(email_config["smtp_host"], int(email_config.get("smtp_port", 587))) as server:
                server.starttls()
                if email_config.get("smtp_username"):
                    server.login(email_config["smtp_username"], email_config.get("smtp_password", ""))
                server.send_message(msg)

            logger.info(f"Email contact envoyé pour {data.email}")
    except Exception as e:
        logger.warning(f"Email contact non envoyé (SMTP non configuré?): {e}")

    return {"status": "ok", "message": "Message reçu"}
