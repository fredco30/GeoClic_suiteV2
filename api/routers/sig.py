"""
Router pour l'intégration SIG Desktop.
Fournit les endpoints pour la synchronisation bidirectionnelle
entre GéoClic SIG Desktop et l'écosystème Data.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime
import hashlib
import json
import random
import string
import tempfile
import zipfile
import os
import shutil

from database import get_db
from routers.auth import get_current_user, get_current_user_optional
from schemas.sig import (
    # Types Format B
    TypeFormatB,
    TypeSyncRequest,
    TypeSyncResponse,
    # Lexique
    LexiqueEntry,
    LexiqueTreeResponse,
    # Champs
    FieldConfig,
    FieldConfigSyncRequest,
    # Projets
    ProjectCreate,
    ProjectResponse,
    ProjectListResponse,
    # Points
    PointSIG,
    PointSyncRequest,
    PointSyncResponse,
    CoordinateSIG,
    # QR Codes
    ShortCodeCreate,
    ShortCodeResponse,
    # Statut
    SyncStatusResponse,
    OfflinePackage,
    # Périmètres
    PerimetreCreate,
    PerimetreResponse,
    # Conversions
    format_b_to_lexique,
    lexique_to_format_b,
)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def generate_short_code() -> str:
    """Génère un code court unique pour QR codes (GC-XXXXXX)."""
    # Caractères sans ambiguïté (pas de I, O, 0, 1)
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    code = ''.join(random.choices(chars, k=6))
    return f"GC-{code}"


def coords_to_wkt(coordinates: List[CoordinateSIG], geom_type: str) -> str:
    """Convertit des coordonnées en WKT."""
    if not coordinates:
        return None

    if geom_type == "POINT":
        return f"POINT({coordinates[0].longitude} {coordinates[0].latitude})"
    elif geom_type == "LINESTRING":
        points = ", ".join([f"{c.longitude} {c.latitude}" for c in coordinates])
        return f"LINESTRING({points})"
    elif geom_type == "POLYGON":
        # Fermer le polygone si nécessaire
        coords = coordinates.copy()
        if coords[0].latitude != coords[-1].latitude or coords[0].longitude != coords[-1].longitude:
            coords.append(coords[0])
        points = ", ".join([f"{c.longitude} {c.latitude}" for c in coords])
        return f"POLYGON(({points}))"
    return None


def wkt_to_coords(wkt: str) -> List[CoordinateSIG]:
    """Parse un WKT en liste de coordonnées."""
    if not wkt:
        return []

    try:
        # Extraire les coordonnées du WKT
        import re
        coords_match = re.search(r'\(([^()]+)\)', wkt)
        if not coords_match:
            return []

        coords_str = coords_match.group(1)
        # Pour les polygones avec parenthèses imbriquées
        coords_str = coords_str.replace('(', '').replace(')', '')

        coords = []
        for pair in coords_str.split(','):
            parts = pair.strip().split(' ')
            if len(parts) >= 2:
                lng = float(parts[0])
                lat = float(parts[1])
                alt = float(parts[2]) if len(parts) > 2 else None
                coords.append(CoordinateSIG(latitude=lat, longitude=lng, altitude=alt))

        return coords
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS STATUT
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    project_id: Optional[str] = Query(None, description="Filtrer par projet"),
    db: AsyncSession = Depends(get_db),
):
    """
    Récupère le statut de synchronisation global ou pour un projet.
    Utilisé par le SIG Desktop pour vérifier s'il y a des mises à jour.
    """
    try:
        # Compter les types
        types_query = "SELECT COUNT(*) FROM lexique WHERE level = 0"
        if project_id:
            types_query += " AND project_id = :project_id"

        result = await db.execute(
            text(types_query),
            {"project_id": project_id} if project_id else {}
        )
        types_count = result.scalar() or 0

        # Compter les points
        points_query = "SELECT COUNT(*) FROM geoclic_staging"
        if project_id:
            points_query += " WHERE project_id = :project_id"

        result = await db.execute(
            text(points_query),
            {"project_id": project_id} if project_id else {}
        )
        points_count = result.scalar() or 0

        # Dernière mise à jour
        result = await db.execute(text("""
            SELECT MAX(updated_at) FROM geoclic_staging
        """))
        last_updated = result.scalar()

        # Calculer la version (hash de la dernière mise à jour)
        version_str = str(last_updated) if last_updated else "0"
        version = int(hashlib.md5(version_str.encode()).hexdigest()[:8], 16) % 1000000

        return SyncStatusResponse(
            current_version=version,
            types_count=types_count,
            points_count=points_count,
            last_updated=last_updated,
            last_sync=last_updated,
            last_sync_status="success",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du statut: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS PROJETS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    is_active: bool = Query(True, description="Filtrer par projets actifs"),
    include_system: bool = Query(False, description="Inclure les projets système (pour Demandes)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional),
):
    """Liste tous les projets disponibles. Par défaut exclut les projets système."""
    try:
        # Filtre pour exclure les projets système par défaut (sauf si demandé)
        system_filter = "" if include_system else "AND COALESCE(is_system, FALSE) = FALSE"

        result = await db.execute(text(f"""
            SELECT id, name, description, status, is_active,
                   COALESCE(is_system, FALSE) as is_system,
                   collectivite_name, min_lat, max_lat, min_lng, max_lng,
                   created_at, updated_at
            FROM projects
            WHERE is_active = :is_active
            {system_filter}
            ORDER BY name
        """), {"is_active": is_active})

        rows = result.fetchall()
        projects = []
        for row in rows:
            projects.append(ProjectResponse(
                id=str(row.id),
                name=row.name,
                description=row.description,
                status=row.status,
                is_active=row.is_active,
                is_system=row.is_system or False,
                collectivite_name=row.collectivite_name,
                min_lat=row.min_lat,
                max_lat=row.max_lat,
                min_lng=row.min_lng,
                max_lng=row.max_lng,
                created_at=row.created_at,
                updated_at=row.updated_at,
            ))

        return ProjectListResponse(projects=projects, total=len(projects))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des projets: {str(e)}",
        )


@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Crée un nouveau projet depuis le SIG Desktop.
    Le projet sera synchronisé avec GéoClic Data.
    """
    try:
        result = await db.execute(text("""
            INSERT INTO projects (name, description, collectivite_name,
                                  min_lat, max_lat, min_lng, max_lng)
            VALUES (:name, :description, :collectivite_name,
                    :min_lat, :max_lat, :min_lng, :max_lng)
            RETURNING id, name, description, status, is_active,
                      collectivite_name, min_lat, max_lat, min_lng, max_lng,
                      created_at, updated_at
        """), {
            "name": project.name,
            "description": project.description,
            "collectivite_name": project.collectivite_name,
            "min_lat": project.min_lat,
            "max_lat": project.max_lat,
            "min_lng": project.min_lng,
            "max_lng": project.max_lng,
        })

        await db.commit()
        row = result.fetchone()

        return ProjectResponse(
            id=str(row.id),
            name=row.name,
            description=row.description,
            status=row.status,
            is_active=row.is_active,
            collectivite_name=row.collectivite_name,
            min_lat=row.min_lat,
            max_lat=row.max_lat,
            min_lng=row.min_lng,
            max_lng=row.max_lng,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du projet: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS TYPES (Format B - Compatible SIG Desktop)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/types", response_model=List[TypeFormatB])
async def get_types(
    project_id: Optional[str] = Query(None, description="Filtrer par projet"),
    db: AsyncSession = Depends(get_db),
):
    """
    Récupère les types au format B (compatible SIG Desktop existant).
    Convertit automatiquement depuis le lexique 6 niveaux.
    """
    try:
        query = """
            SELECT id, code, label, parent_code, project_id, level,
                   display_order, icon_name, color_value, is_active
            FROM lexique
            WHERE is_active = TRUE
        """
        params = {}

        if project_id:
            query += " AND (project_id = :project_id OR project_id IS NULL)"
            params["project_id"] = project_id

        query += " ORDER BY level, display_order"

        result = await db.execute(text(query), params)
        rows = result.fetchall()

        # Construire les entrées de lexique
        entries = []
        for row in rows:
            entries.append(LexiqueEntry(
                id=row.id,
                code=row.code,
                label=row.label,
                parent_code=row.parent_code,
                project_id=str(row.project_id) if row.project_id else None,
                level=row.level,
                display_order=row.display_order,
                icon_name=row.icon_name,
                color_value=row.color_value,
                is_active=row.is_active,
            ))

        # Convertir en Format B
        return lexique_to_format_b(entries)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des types: {str(e)}",
        )


@router.post("/types/sync", response_model=TypeSyncResponse)
async def sync_types(
    request: TypeSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Synchronise les types depuis le SIG Desktop vers la base.
    Convertit automatiquement du Format B vers le lexique 6 niveaux.
    """
    try:
        # Convertir Format B vers Lexique
        lexique_entries = format_b_to_lexique(request.types, request.project_id)

        # Si replace_all, supprimer les types existants du projet
        if request.replace_all:
            await db.execute(text("""
                DELETE FROM lexique WHERE project_id = :project_id
            """), {"project_id": request.project_id})

        types_count = 0
        subtypes_count = 0

        # Insérer/mettre à jour les entrées
        for entry in lexique_entries:
            await db.execute(text("""
                INSERT INTO lexique (code, label, parent_code, project_id, level,
                                     display_order, icon_name, color_value, triggers_form)
                VALUES (:code, :label, :parent_code, :project_id, :level,
                        :display_order, :icon_name, :color_value, :triggers_form)
                ON CONFLICT (code, project_id) DO UPDATE SET
                    label = EXCLUDED.label,
                    parent_code = EXCLUDED.parent_code,
                    display_order = EXCLUDED.display_order,
                    icon_name = EXCLUDED.icon_name,
                    color_value = EXCLUDED.color_value,
                    triggers_form = EXCLUDED.triggers_form
            """), {
                "code": entry.code,
                "label": entry.label,
                "parent_code": entry.parent_code,
                "project_id": entry.project_id,
                "level": entry.level,
                "display_order": entry.display_order,
                "icon_name": entry.icon_name,
                "color_value": entry.color_value,
                "triggers_form": entry.triggers_form,
            })

            if entry.level == 0:
                types_count += 1
            else:
                subtypes_count += 1

        await db.commit()

        # Calculer la version
        version = int(datetime.now().timestamp()) % 1000000

        return TypeSyncResponse(
            success=True,
            types_count=types_count,
            subtypes_count=subtypes_count,
            version=version,
            message=f"Synchronisation réussie: {types_count} types, {subtypes_count} sous-types",
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la synchronisation des types: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS LEXIQUE COMPLET (6 niveaux)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/lexique", response_model=LexiqueTreeResponse)
async def get_lexique_tree(
    project_id: str = Query(..., description="UUID du projet"),
    db: AsyncSession = Depends(get_db),
):
    """
    Récupère l'arbre complet du lexique pour un projet.
    Format hiérarchique avec children imbriqués.
    """
    try:
        result = await db.execute(text("""
            SELECT id, code, label, parent_code, project_id::text, level,
                   display_order, icon_name, color_value, is_active,
                   triggers_form, form_type_ref
            FROM lexique
            WHERE (project_id = :project_id OR project_id IS NULL)
              AND is_active = TRUE
            ORDER BY level, display_order
        """), {"project_id": project_id})

        rows = result.fetchall()

        # Construire l'arbre
        entries_map = {}
        root_entries = []

        for row in rows:
            entry = LexiqueEntry(
                id=row.id,
                code=row.code,
                label=row.label,
                parent_code=row.parent_code,
                project_id=row.project_id,
                level=row.level,
                display_order=row.display_order,
                icon_name=row.icon_name,
                color_value=row.color_value,
                is_active=row.is_active,
                triggers_form=row.triggers_form or False,
                form_type_ref=row.form_type_ref,
                children=[],
            )
            entries_map[row.code] = entry

            if row.parent_code is None:
                root_entries.append(entry)
            elif row.parent_code in entries_map:
                entries_map[row.parent_code].children.append(entry)

        # Calculer la version
        version = hashlib.md5(json.dumps([e.code for e in root_entries]).encode()).hexdigest()[:8]

        return LexiqueTreeResponse(
            project_id=project_id,
            entries=root_entries,
            version=version,
            last_updated=datetime.now(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du lexique: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS CHAMPS DYNAMIQUES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/fields/{type_name}", response_model=List[FieldConfig])
async def get_field_configs(
    type_name: str,
    project_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Récupère la configuration des champs pour un type."""
    try:
        query = """
            SELECT id, type_name, field_name, field_label, field_type,
                   is_required, dropdown_options, default_value,
                   display_order, unit, min_value, max_value, help_text
            FROM type_field_configs
            WHERE type_name = :type_name
        """
        params = {"type_name": type_name}

        if project_id:
            # Note: il faudrait ajouter project_id à type_field_configs si pas déjà fait
            pass

        query += " ORDER BY display_order"

        result = await db.execute(text(query), params)
        rows = result.fetchall()

        configs = []
        for row in rows:
            options = None
            if row.dropdown_options:
                if isinstance(row.dropdown_options, str):
                    options = json.loads(row.dropdown_options)
                else:
                    options = row.dropdown_options

            configs.append(FieldConfig(
                id=row.id,
                type_name=row.type_name,
                field_name=row.field_name,
                field_label=row.field_label,
                field_type=row.field_type,
                is_required=row.is_required,
                dropdown_options=options,
                default_value=row.default_value,
                display_order=row.display_order,
                unit=row.unit,
                min_value=row.min_value,
                max_value=row.max_value,
                help_text=row.help_text,
            ))

        return configs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des champs: {str(e)}",
        )


@router.post("/fields/sync", response_model=dict)
async def sync_field_configs(
    request: FieldConfigSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Synchronise les configurations de champs depuis le SIG."""
    try:
        count = 0
        for config in request.configs:
            options_json = json.dumps(config.dropdown_options) if config.dropdown_options else None

            await db.execute(text("""
                INSERT INTO type_field_configs (
                    type_name, field_name, field_label, field_type,
                    is_required, dropdown_options, default_value,
                    display_order, unit, min_value, max_value, help_text
                )
                VALUES (
                    :type_name, :field_name, :field_label, :field_type,
                    :is_required, :dropdown_options::jsonb, :default_value,
                    :display_order, :unit, :min_value, :max_value, :help_text
                )
                ON CONFLICT (type_name, field_name) DO UPDATE SET
                    field_label = EXCLUDED.field_label,
                    field_type = EXCLUDED.field_type,
                    is_required = EXCLUDED.is_required,
                    dropdown_options = EXCLUDED.dropdown_options,
                    default_value = EXCLUDED.default_value,
                    display_order = EXCLUDED.display_order,
                    unit = EXCLUDED.unit,
                    min_value = EXCLUDED.min_value,
                    max_value = EXCLUDED.max_value,
                    help_text = EXCLUDED.help_text
            """), {
                "type_name": config.type_name,
                "field_name": config.field_name,
                "field_label": config.field_label,
                "field_type": config.field_type,
                "is_required": config.is_required,
                "dropdown_options": options_json,
                "default_value": config.default_value,
                "display_order": config.display_order,
                "unit": config.unit,
                "min_value": config.min_value,
                "max_value": config.max_value,
                "help_text": config.help_text,
            })
            count += 1

        await db.commit()
        return {"success": True, "count": count}
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la synchronisation des champs: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS POINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/points", response_model=List[PointSIG])
async def get_points(
    project_id: Optional[str] = Query(None),
    zone_name: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    limit: int = Query(1000, le=10000),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Récupère les points au format SIG Desktop."""
    try:
        query = """
            SELECT id, name, type, subtype, condition_state, point_status,
                   comment, zone_name, geom_type, ST_AsText(geom) as wkt,
                   gps_precision, gps_source,
                   materiau, hauteur, largeur, date_installation,
                   duree_vie_annees, marque_modele,
                   date_derniere_intervention, date_prochaine_intervention,
                   priorite, cout_remplacement, custom_properties,
                   created_at, updated_at, project_id::text, lexique_code
            FROM geoclic_staging
            WHERE 1=1
        """
        params = {}

        if project_id:
            query += " AND project_id = :project_id"
            params["project_id"] = project_id

        if zone_name:
            query += " AND zone_name = :zone_name"
            params["zone_name"] = zone_name

        if type:
            query += " AND type = :type"
            params["type"] = type

        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        result = await db.execute(text(query), params)
        rows = result.fetchall()

        points = []
        for row in rows:
            coords = wkt_to_coords(row.wkt) if row.wkt else []

            points.append(PointSIG(
                id=str(row.id),
                name=row.name,
                type=row.type,
                subtype=row.subtype,
                condition=row.condition_state or "Neuf",
                status=row.point_status or "Projet",
                comment=row.comment,
                zone_name=row.zone_name,
                geom_type=row.geom_type or "POINT",
                coordinates=coords,
                gps_precision=row.gps_precision,
                gps_source=row.gps_source,
                materiau=row.materiau,
                hauteur=row.hauteur,
                largeur=row.largeur,
                date_installation=row.date_installation,
                duree_vie_annees=row.duree_vie_annees,
                marque_modele=row.marque_modele,
                date_derniere_intervention=row.date_derniere_intervention,
                date_prochaine_intervention=row.date_prochaine_intervention,
                priorite=row.priorite,
                cout_remplacement=row.cout_remplacement,
                custom_properties=row.custom_properties,
                created_at=row.created_at,
                updated_at=row.updated_at,
                project_id=row.project_id,
                lexique_code=row.lexique_code,
            ))

        return points
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des points: {str(e)}",
        )


@router.post("/points/sync", response_model=PointSyncResponse)
async def sync_points(
    request: PointSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Synchronise les points depuis le SIG Desktop vers la base.
    Gère les créations et mises à jour (upsert).
    """
    uploaded = 0
    updated = 0
    failed = 0
    errors = []
    server_ids = {}

    try:
        for point in request.points:
            try:
                wkt = coords_to_wkt(point.coordinates, point.geom_type.value)

                if point.id:
                    # Update existing
                    result = await db.execute(text("""
                        UPDATE geoclic_staging SET
                            name = :name,
                            type = :type,
                            subtype = :subtype,
                            condition_state = :condition,
                            point_status = :status,
                            comment = :comment,
                            zone_name = :zone_name,
                            geom_type = :geom_type,
                            geom = ST_GeomFromText(:wkt, 4326),
                            gps_precision = :gps_precision,
                            gps_source = :gps_source,
                            materiau = :materiau,
                            hauteur = :hauteur,
                            largeur = :largeur,
                            date_installation = :date_installation,
                            duree_vie_annees = :duree_vie_annees,
                            marque_modele = :marque_modele,
                            date_derniere_intervention = :date_derniere_intervention,
                            date_prochaine_intervention = :date_prochaine_intervention,
                            priorite = :priorite,
                            cout_remplacement = :cout_remplacement,
                            custom_properties = :custom_properties::jsonb,
                            lexique_code = :lexique_code,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                        RETURNING id
                    """), {
                        "id": point.id,
                        "name": point.name,
                        "type": point.type,
                        "subtype": point.subtype,
                        "condition": point.condition,
                        "status": point.status,
                        "comment": point.comment,
                        "zone_name": point.zone_name or request.zone_name,
                        "geom_type": point.geom_type.value,
                        "wkt": wkt,
                        "gps_precision": point.gps_precision,
                        "gps_source": point.gps_source,
                        "materiau": point.materiau,
                        "hauteur": point.hauteur,
                        "largeur": point.largeur,
                        "date_installation": point.date_installation,
                        "duree_vie_annees": point.duree_vie_annees,
                        "marque_modele": point.marque_modele,
                        "date_derniere_intervention": point.date_derniere_intervention,
                        "date_prochaine_intervention": point.date_prochaine_intervention,
                        "priorite": point.priorite,
                        "cout_remplacement": point.cout_remplacement,
                        "custom_properties": json.dumps(point.custom_properties) if point.custom_properties else "{}",
                        "lexique_code": point.lexique_code,
                    })
                    row = result.fetchone()
                    if row:
                        server_ids[point.id] = str(row.id)
                        updated += 1
                    else:
                        failed += 1
                        errors.append(f"Point {point.id} non trouvé pour mise à jour")
                else:
                    # Insert new
                    result = await db.execute(text("""
                        INSERT INTO geoclic_staging (
                            project_id, name, type, subtype,
                            condition_state, point_status, comment, zone_name,
                            geom_type, geom, gps_precision, gps_source,
                            materiau, hauteur, largeur, date_installation,
                            duree_vie_annees, marque_modele,
                            date_derniere_intervention, date_prochaine_intervention,
                            priorite, cout_remplacement, custom_properties, lexique_code,
                            sync_status, created_by
                        )
                        VALUES (
                            :project_id, :name, :type, :subtype,
                            :condition, :status, :comment, :zone_name,
                            :geom_type, ST_GeomFromText(:wkt, 4326), :gps_precision, :gps_source,
                            :materiau, :hauteur, :largeur, :date_installation,
                            :duree_vie_annees, :marque_modele,
                            :date_derniere_intervention, :date_prochaine_intervention,
                            :priorite, :cout_remplacement, :custom_properties::jsonb, :lexique_code,
                            'draft', :created_by
                        )
                        RETURNING id
                    """), {
                        "project_id": request.project_id,
                        "name": point.name,
                        "type": point.type,
                        "subtype": point.subtype,
                        "condition": point.condition,
                        "status": point.status,
                        "comment": point.comment,
                        "zone_name": point.zone_name or request.zone_name,
                        "geom_type": point.geom_type.value,
                        "wkt": wkt,
                        "gps_precision": point.gps_precision,
                        "gps_source": point.gps_source,
                        "materiau": point.materiau,
                        "hauteur": point.hauteur,
                        "largeur": point.largeur,
                        "date_installation": point.date_installation,
                        "duree_vie_annees": point.duree_vie_annees,
                        "marque_modele": point.marque_modele,
                        "date_derniere_intervention": point.date_derniere_intervention,
                        "date_prochaine_intervention": point.date_prochaine_intervention,
                        "priorite": point.priorite,
                        "cout_remplacement": point.cout_remplacement,
                        "custom_properties": json.dumps(point.custom_properties) if point.custom_properties else "{}",
                        "lexique_code": point.lexique_code,
                        "created_by": current_user.get("id"),
                    })
                    row = result.fetchone()
                    if row:
                        temp_id = point.name  # Utiliser le nom comme clé temporaire
                        server_ids[temp_id] = str(row.id)
                        uploaded += 1

            except Exception as e:
                failed += 1
                errors.append(f"Point {point.name}: {str(e)}")

        await db.commit()

        return PointSyncResponse(
            success=failed == 0,
            uploaded=uploaded,
            updated=updated,
            failed=failed,
            errors=errors,
            server_ids=server_ids,
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la synchronisation des points: {str(e)}",
        )


@router.delete("/points/{point_id}")
async def delete_point(
    point_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Supprime un point."""
    try:
        result = await db.execute(text("""
            DELETE FROM geoclic_staging WHERE id = :id RETURNING id
        """), {"id": point_id})

        await db.commit()
        row = result.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Point non trouvé",
            )

        return {"success": True, "deleted_id": point_id}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS QR CODES / SHORT CODES
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/shortcodes", response_model=ShortCodeResponse)
async def create_short_code(
    request: ShortCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Crée un code court pour un point (QR code).
    Format: GC-XXXXXX
    """
    try:
        # Vérifier si un code existe déjà pour ce point
        result = await db.execute(text("""
            SELECT short_code FROM short_codes WHERE point_id = :point_id
        """), {"point_id": request.point_id})

        existing = result.fetchone()
        if existing:
            return ShortCodeResponse(
                short_code=existing.short_code,
                point_id=request.point_id,
                url=f"https://geoclic.fr/e/{existing.short_code}",
                created_at=datetime.now(),
            )

        # Générer un nouveau code unique
        max_attempts = 10
        for _ in range(max_attempts):
            short_code = generate_short_code()

            # Vérifier l'unicité
            check = await db.execute(text("""
                SELECT 1 FROM short_codes WHERE short_code = :code
            """), {"code": short_code})

            if not check.fetchone():
                # Insérer
                await db.execute(text("""
                    INSERT INTO short_codes (short_code, point_id)
                    VALUES (:code, :point_id)
                """), {"code": short_code, "point_id": request.point_id})

                await db.commit()

                return ShortCodeResponse(
                    short_code=short_code,
                    point_id=request.point_id,
                    url=f"https://geoclic.fr/e/{short_code}",
                    created_at=datetime.now(),
                )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de générer un code unique",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        # La table n'existe peut-être pas encore
        if "short_codes" in str(e):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Table short_codes non créée. Exécutez la migration.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}",
        )


@router.get("/shortcodes/{code}", response_model=ShortCodeResponse)
async def get_short_code(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """Récupère les informations d'un code court."""
    try:
        result = await db.execute(text("""
            SELECT short_code, point_id::text, created_at
            FROM short_codes
            WHERE short_code = :code
        """), {"code": code})

        row = result.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Code non trouvé",
            )

        return ShortCodeResponse(
            short_code=row.short_code,
            point_id=row.point_id,
            url=f"https://geoclic.fr/e/{row.short_code}",
            created_at=row.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT OFFLINE PACKAGE
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/offline-package/{project_id}", response_model=OfflinePackage)
async def get_offline_package(
    project_id: str,
    include_points: bool = Query(True),
    radius_km: Optional[float] = Query(None, description="Rayon en km autour du centre du projet"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Récupère un package complet pour le mode offline.
    Inclut: projet, lexique, champs dynamiques, et optionnellement les points.
    """
    try:
        # Récupérer le projet
        result = await db.execute(text("""
            SELECT id, name, description, status, is_active,
                   collectivite_name, min_lat, max_lat, min_lng, max_lng,
                   created_at, updated_at
            FROM projects WHERE id = :id
        """), {"id": project_id})

        project_row = result.fetchone()
        if not project_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Projet non trouvé",
            )

        project = ProjectResponse(
            id=str(project_row.id),
            name=project_row.name,
            description=project_row.description,
            status=project_row.status,
            is_active=project_row.is_active,
            collectivite_name=project_row.collectivite_name,
            min_lat=project_row.min_lat,
            max_lat=project_row.max_lat,
            min_lng=project_row.min_lng,
            max_lng=project_row.max_lng,
            created_at=project_row.created_at,
            updated_at=project_row.updated_at,
        )

        # Récupérer le lexique
        lexique_result = await db.execute(text("""
            SELECT id, code, label, parent_code, project_id::text, level,
                   display_order, icon_name, color_value, is_active,
                   triggers_form, form_type_ref
            FROM lexique
            WHERE (project_id = :project_id OR project_id IS NULL)
              AND is_active = TRUE
            ORDER BY level, display_order
        """), {"project_id": project_id})

        lexique_entries = []
        for row in lexique_result.fetchall():
            lexique_entries.append(LexiqueEntry(
                id=row.id,
                code=row.code,
                label=row.label,
                parent_code=row.parent_code,
                project_id=row.project_id,
                level=row.level,
                display_order=row.display_order,
                icon_name=row.icon_name,
                color_value=row.color_value,
                is_active=row.is_active,
                triggers_form=row.triggers_form or False,
                form_type_ref=row.form_type_ref,
            ))

        # Récupérer les champs dynamiques
        fields_result = await db.execute(text("""
            SELECT id, type_name, field_name, field_label, field_type,
                   is_required, dropdown_options, default_value,
                   display_order, unit, min_value, max_value, help_text
            FROM type_field_configs
            ORDER BY type_name, display_order
        """))

        field_configs = []
        for row in fields_result.fetchall():
            options = None
            if row.dropdown_options:
                if isinstance(row.dropdown_options, str):
                    options = json.loads(row.dropdown_options)
                else:
                    options = row.dropdown_options

            field_configs.append(FieldConfig(
                id=row.id,
                type_name=row.type_name,
                field_name=row.field_name,
                field_label=row.field_label,
                field_type=row.field_type,
                is_required=row.is_required,
                dropdown_options=options,
                default_value=row.default_value,
                display_order=row.display_order,
                unit=row.unit,
                min_value=row.min_value,
                max_value=row.max_value,
                help_text=row.help_text,
            ))

        # Récupérer les points (si demandé)
        points = []
        total_points = 0

        if include_points:
            points_query = """
                SELECT id, name, type, subtype, condition_state, point_status,
                       comment, zone_name, geom_type, ST_AsText(geom) as wkt,
                       gps_precision, gps_source,
                       materiau, hauteur, largeur, date_installation,
                       duree_vie_annees, marque_modele,
                       date_derniere_intervention, date_prochaine_intervention,
                       priorite, cout_remplacement, custom_properties,
                       created_at, updated_at, project_id::text, lexique_code
                FROM geoclic_staging
                WHERE project_id = :project_id
            """

            # Si rayon spécifié et emprise projet disponible, filtrer
            if radius_km and project.min_lat and project.max_lat:
                center_lat = (project.min_lat + project.max_lat) / 2
                center_lng = (project.min_lng + project.max_lng) / 2
                points_query += f"""
                    AND ST_DWithin(
                        geom::geography,
                        ST_SetSRID(ST_MakePoint({center_lng}, {center_lat}), 4326)::geography,
                        {radius_km * 1000}
                    )
                """

            points_query += " ORDER BY created_at DESC LIMIT 5000"

            points_result = await db.execute(text(points_query), {"project_id": project_id})

            for row in points_result.fetchall():
                coords = wkt_to_coords(row.wkt) if row.wkt else []
                points.append(PointSIG(
                    id=str(row.id),
                    name=row.name,
                    type=row.type,
                    subtype=row.subtype,
                    condition=row.condition_state or "Neuf",
                    status=row.point_status or "Projet",
                    comment=row.comment,
                    zone_name=row.zone_name,
                    geom_type=row.geom_type or "POINT",
                    coordinates=coords,
                    gps_precision=row.gps_precision,
                    gps_source=row.gps_source,
                    materiau=row.materiau,
                    hauteur=row.hauteur,
                    largeur=row.largeur,
                    date_installation=row.date_installation,
                    duree_vie_annees=row.duree_vie_annees,
                    marque_modele=row.marque_modele,
                    date_derniere_intervention=row.date_derniere_intervention,
                    date_prochaine_intervention=row.date_prochaine_intervention,
                    priorite=row.priorite,
                    cout_remplacement=row.cout_remplacement,
                    custom_properties=row.custom_properties,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    project_id=row.project_id,
                    lexique_code=row.lexique_code,
                ))

            total_points = len(points)

        # Calculer la version du lexique
        lexique_version = hashlib.md5(
            json.dumps([e.code for e in lexique_entries]).encode()
        ).hexdigest()[:8]

        return OfflinePackage(
            server_time=datetime.now(),
            project=project,
            lexique_version=lexique_version,
            lexique_entries=lexique_entries,
            field_configs=field_configs,
            points=points,
            total_points=total_points,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération du package offline: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT IMPORT DE FICHIERS (Shapefile, GeoPackage, GeoJSON)
# ═══════════════════════════════════════════════════════════════════════════════

def validate_shapefile_zip(zip_path: str, extract_dir: str) -> str:
    """
    Valide et extrait un fichier ZIP contenant un Shapefile.
    Retourne le chemin vers le fichier .shp.
    """
    required_extensions = {'.shp', '.shx', '.dbf'}

    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Protection path traversal
        for member in zf.namelist():
            if member.startswith('/') or '..' in member:
                raise ValueError(f"Chemin invalide dans le ZIP: {member}")
        zf.extractall(extract_dir)

    # Trouver tous les fichiers extraits et créer un mapping case-insensitive
    extracted_files = []
    files_by_lower = {}  # Mapping: extension.lower() -> chemin réel
    for root, dirs, files in os.walk(extract_dir):
        for f in files:
            full_path = os.path.join(root, f)
            extracted_files.append(full_path)
            # Stocker par nom de base + extension en minuscules
            base = os.path.splitext(f)[0]
            ext = os.path.splitext(f)[1].lower()
            key = (os.path.join(root, base).lower(), ext)
            files_by_lower[key] = full_path

    # Trouver le fichier .shp (case-insensitive)
    shp_files = [f for f in extracted_files if f.lower().endswith('.shp')]

    if not shp_files:
        raise ValueError("Aucun fichier .shp trouvé dans l'archive")

    if len(shp_files) > 1:
        raise ValueError("L'archive contient plusieurs fichiers .shp, veuillez n'en inclure qu'un seul")

    shp_path = shp_files[0]
    base_name_lower = os.path.splitext(shp_path)[0].lower()

    # Vérifier les fichiers requis (case-insensitive)
    missing = []
    for ext in required_extensions:
        key = (base_name_lower, ext)
        if key not in files_by_lower:
            missing.append(ext)

    if missing:
        raise ValueError(f"Fichiers manquants pour le Shapefile: {', '.join(missing)}")

    return shp_path


def convert_to_geojson(file_path: str, file_type: str, layer_name: str = None) -> dict:
    """
    Convertit un fichier Shapefile ou GeoPackage en GeoJSON.
    Pour les GeoPackages multi-couches, spécifier layer_name ou la première couche est utilisée.
    """
    try:
        import fiona
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fiona n'est pas installé. Contactez l'administrateur.",
        )

    features = []
    crs = None
    layers_info = []

    try:
        # Pour GeoPackage, lister les couches disponibles
        if file_type == 'geopackage':
            available_layers = fiona.listlayers(file_path)
            layers_info = available_layers
            if not available_layers:
                raise ValueError("Le GeoPackage ne contient aucune couche")
            # Utiliser la couche spécifiée ou la première
            layer_to_read = layer_name if layer_name in available_layers else available_layers[0]
        else:
            layer_to_read = None

        # Ouvrir le fichier
        open_kwargs = {'layer': layer_to_read} if layer_to_read else {}
        with fiona.open(file_path, **open_kwargs) as src:
            crs = src.crs
            schema = src.schema

            for feature in src:
                # Convertir la géométrie
                geom = feature.get('geometry')
                props = dict(feature.get('properties', {}))

                # Nettoyer les propriétés (convertir types non-sérialisables)
                clean_props = {}
                for k, v in props.items():
                    if v is None:
                        clean_props[k] = None
                    elif isinstance(v, (str, int, float, bool)):
                        clean_props[k] = v
                    elif hasattr(v, 'isoformat'):  # datetime
                        clean_props[k] = v.isoformat()
                    else:
                        clean_props[k] = str(v)

                features.append({
                    'type': 'Feature',
                    'geometry': dict(geom) if geom else None,
                    'properties': clean_props
                })

    except fiona.errors.DriverError as e:
        raise ValueError(f"Impossible d'ouvrir le fichier (format non supporté ou fichier corrompu): {str(e)}")
    except Exception as e:
        raise ValueError(f"Erreur de lecture du fichier: {str(e)}")

    result = {
        'type': 'FeatureCollection',
        'features': features,
    }

    # Ajouter les métadonnées
    if crs:
        result['crs'] = {'type': 'name', 'properties': {'name': str(crs)}}

    # Pour GeoPackage, inclure les infos sur les couches disponibles
    if layers_info and len(layers_info) > 1:
        result['_metadata'] = {
            'available_layers': layers_info,
            'loaded_layer': layer_to_read,
            'note': 'Ce GeoPackage contient plusieurs couches. Seule la première a été chargée.'
        }

    return result


# Limite de taille de fichier (50 Mo)
MAX_UPLOAD_SIZE = 50 * 1024 * 1024


@router.post("/import")
async def import_file(
    file: UploadFile = File(..., description="Fichier à importer (.zip pour Shapefile, .gpkg pour GeoPackage)"),
    layer: Optional[str] = Query(None, description="Nom de la couche à lire (pour GeoPackage multi-couches)"),
    current_user: dict = Depends(get_current_user_optional),
):
    """
    Importe un fichier géospatial et le convertit en GeoJSON.

    Formats supportés:
    - Shapefile: fichier .zip contenant .shp, .shx, .dbf (et optionnellement .prj)
    - GeoPackage: fichier .gpkg
    - GeoJSON: fichier .geojson ou .json (passthrough)

    Limite: 50 Mo maximum.
    Retourne un FeatureCollection GeoJSON.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nom de fichier manquant",
        )

    filename_lower = file.filename.lower()

    # Déterminer le type de fichier
    if filename_lower.endswith('.geojson') or filename_lower.endswith('.json'):
        # GeoJSON - lecture directe
        try:
            content = await file.read()
            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Fichier trop volumineux. Maximum: {MAX_UPLOAD_SIZE // (1024*1024)} Mo",
                )
            data = json.loads(content.decode('utf-8'))

            if data.get('type') == 'FeatureCollection':
                return JSONResponse(content=data)
            elif data.get('type') == 'Feature':
                return JSONResponse(content={
                    'type': 'FeatureCollection',
                    'features': [data]
                })
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Format GeoJSON invalide: doit être FeatureCollection ou Feature",
                )
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erreur de parsing JSON: {str(e)}",
            )

    elif filename_lower.endswith('.zip'):
        # Shapefile dans une archive ZIP
        temp_dir = tempfile.mkdtemp(prefix='geoclic_import_')
        try:
            # Sauvegarder le fichier uploadé (nom sécurisé pour éviter path traversal)
            safe_filename = os.path.basename(file.filename) if file.filename else "upload.zip"
            zip_path = os.path.join(temp_dir, safe_filename)
            content = await file.read()
            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Fichier trop volumineux. Maximum: {MAX_UPLOAD_SIZE // (1024*1024)} Mo",
                )
            with open(zip_path, 'wb') as f:
                f.write(content)

            # Extraire et valider le Shapefile
            extract_dir = os.path.join(temp_dir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)

            shp_path = validate_shapefile_zip(zip_path, extract_dir)

            # Convertir en GeoJSON
            geojson_data = convert_to_geojson(shp_path, 'shapefile')

            return JSONResponse(content=geojson_data)

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            print(f"Erreur Shapefile import: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors du traitement du Shapefile",
            )
        finally:
            # Nettoyer le répertoire temporaire
            shutil.rmtree(temp_dir, ignore_errors=True)

    elif filename_lower.endswith('.gpkg'):
        # GeoPackage
        temp_dir = tempfile.mkdtemp(prefix='geoclic_import_')
        try:
            # Sauvegarder le fichier uploadé (nom sécurisé pour éviter path traversal)
            safe_filename = os.path.basename(file.filename) if file.filename else "upload.gpkg"
            gpkg_path = os.path.join(temp_dir, safe_filename)
            content = await file.read()
            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Fichier trop volumineux. Maximum: {MAX_UPLOAD_SIZE // (1024*1024)} Mo",
                )
            with open(gpkg_path, 'wb') as f:
                f.write(content)

            # Convertir en GeoJSON (avec support couche optionnelle)
            geojson_data = convert_to_geojson(gpkg_path, 'geopackage', layer_name=layer)

            return JSONResponse(content=geojson_data)

        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            print(f"Erreur GeoPackage import: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors du traitement du GeoPackage",
            )
        finally:
            # Nettoyer le répertoire temporaire
            shutil.rmtree(temp_dir, ignore_errors=True)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format de fichier non supporté. Utilisez .zip (Shapefile), .gpkg (GeoPackage) ou .geojson/.json",
        )


@router.post("/import/layers")
async def list_file_layers(
    file: UploadFile = File(..., description="Fichier GeoPackage (.gpkg) pour lister les couches"),
    current_user: dict = Depends(get_current_user_optional),
):
    """
    Liste les couches disponibles dans un fichier GeoPackage.
    Utile pour permettre à l'utilisateur de choisir quelle couche importer.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nom de fichier manquant",
        )

    filename_lower = file.filename.lower()

    if not filename_lower.endswith('.gpkg'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seuls les fichiers GeoPackage (.gpkg) supportent les couches multiples",
        )

    temp_dir = tempfile.mkdtemp(prefix='geoclic_layers_')
    try:
        # Sauvegarder le fichier
        gpkg_path = os.path.join(temp_dir, file.filename)
        content = await file.read()
        # Limite plus basse pour juste lister les couches
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Fichier trop volumineux. Maximum: {MAX_UPLOAD_SIZE // (1024*1024)} Mo",
            )
        with open(gpkg_path, 'wb') as f:
            f.write(content)

        try:
            import fiona
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Fiona n'est pas installé.",
            )

        layers = fiona.listlayers(gpkg_path)

        # Récupérer les infos sur chaque couche
        layers_info = []
        for layer_name in layers:
            with fiona.open(gpkg_path, layer=layer_name) as src:
                layers_info.append({
                    'name': layer_name,
                    'geometry_type': src.schema.get('geometry', 'Unknown'),
                    'feature_count': len(src),
                    'properties': list(src.schema.get('properties', {}).keys()),
                    'crs': str(src.crs) if src.crs else None
                })

        return JSONResponse(content={
            'filename': file.filename,
            'layer_count': len(layers),
            'layers': layers_info
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la lecture du GeoPackage: {str(e)}",
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
