"""
Router pour la synchronisation Mobile ↔ Serveur.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from typing import Optional
import json
import uuid
import hashlib

from database import get_db
from routers.auth import get_current_user
from schemas.sync import (
    SyncRequest, SyncResponse, SyncStatusResponse,
    LexiqueEntrySync, ChampDynamiqueSync, ProjectSync,
    OfflinePackageResponse
)
from schemas.point import PointResponse, CoordinateSchema, PhotoMetadataSchema

router = APIRouter()


async def get_lexique_version(db: AsyncSession) -> str:
    """Calcule un hash MD5 du lexique pour détecter les changements."""
    result = await db.execute(
        text("SELECT code, label, created_at FROM lexique ORDER BY code")
    )
    rows = result.fetchall()
    content = "|".join([f"{r[0]}:{r[1]}:{r[2]}" for r in rows])
    return hashlib.md5(content.encode()).hexdigest()[:16]


async def get_lexique_entries(db: AsyncSession, project_id: str = None) -> list:
    """Récupère les entrées du lexique (filtrées par projet si spécifié)."""
    if project_id:
        result = await db.execute(
            text("""
                SELECT code, label, parent_code, level, icon_name,
                       color_value, display_order, is_active, project_id
                FROM lexique
                WHERE is_active = TRUE AND project_id = :project_id
                ORDER BY level, display_order, label
            """),
            {"project_id": project_id}
        )
    else:
        result = await db.execute(
            text("""
                SELECT code, label, parent_code, level, icon_name,
                       color_value, display_order, is_active, project_id
                FROM lexique
                WHERE is_active = TRUE
                ORDER BY level, display_order, label
            """)
        )
    entries = []
    for row in result.fetchall():
        # Convertir color_value int → string hex pour le mobile
        color_val = row[5]
        if color_val is not None and isinstance(color_val, int):
            # Extraire RGB depuis ARGB int (ignorer le canal alpha)
            r = (color_val >> 16) & 0xFF
            g = (color_val >> 8) & 0xFF
            b = color_val & 0xFF
            color_val = f"#{r:02x}{g:02x}{b:02x}"

        entries.append(LexiqueEntrySync(
            code=row[0],
            label=row[1],
            parent_code=row[2],
            level=row[3] or 0,
            icon_name=row[4],
            color_value=color_val,
            display_order=row[6] or 0,
            is_active=row[7] if row[7] is not None else True,
            project_id=str(row[8]) if row[8] else None,
        ))
    return entries


async def get_champs_dynamiques(db: AsyncSession, project_id: str = None) -> list:
    """Récupère les champs dynamiques (filtrés par projet si spécifié)."""
    try:
        if project_id:
            # Récupérer les champs du projet + champs globaux (sans project_id)
            result = await db.execute(
                text("""
                    SELECT id, type_name, field_name, field_type, is_required,
                           display_order, dropdown_options, min_value, max_value,
                           project_id, help_text
                    FROM type_field_configs
                    WHERE project_id = :project_id OR project_id IS NULL
                    ORDER BY type_name, display_order
                """),
                {"project_id": project_id}
            )
        else:
            result = await db.execute(
                text("""
                    SELECT id, type_name, field_name, field_type, is_required,
                           display_order, dropdown_options, min_value, max_value,
                           project_id, help_text
                    FROM type_field_configs
                    ORDER BY type_name, display_order
                """)
            )
        champs = []
        for row in result.mappings().all():
            options = None
            raw_options = row.get("dropdown_options")
            if raw_options:
                try:
                    options = json.loads(raw_options) if isinstance(raw_options, str) else raw_options
                except:
                    pass

            # Extraire les options avancées du help_text (JSON)
            advanced_opts = {}
            help_text = row.get("help_text")
            if help_text:
                try:
                    advanced_opts = json.loads(help_text) if isinstance(help_text, str) else help_text
                except:
                    advanced_opts = {}

            # condition_value : convertir liste en string si nécessaire
            condition_value = advanced_opts.get("condition_value")
            if isinstance(condition_value, list):
                condition_value = condition_value[0] if len(condition_value) == 1 else ",".join(str(v) for v in condition_value)

            champs.append(ChampDynamiqueSync(
                id=str(row["id"]),
                lexique_code=row["type_name"],
                nom=row["field_name"],
                type=row["field_type"],
                obligatoire=row["is_required"] if row["is_required"] is not None else False,
                ordre=row["display_order"] or 0,
                options=options,
                min_value=row["min_value"],
                max_value=row["max_value"],
                formule=advanced_opts.get("formule"),
                actif=advanced_opts.get("actif", True),
                project_id=str(row["project_id"]) if row.get("project_id") else None,
                condition_field=advanced_opts.get("condition_field"),
                condition_operator=advanced_opts.get("condition_operator"),
                condition_value=condition_value,
            ))
        return champs
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Erreur récupération champs dynamiques: {e}")
        return []


async def get_projects(db: AsyncSession, user_permissions: dict = None) -> list:
    """Récupère les projets (filtrés par permissions si fourni)."""
    query = """
        SELECT id, name, description, collectivite_name, status, is_active
        FROM projects
        WHERE is_active = TRUE
        ORDER BY name
    """
    result = await db.execute(text(query))
    projects = []
    for row in result.mappings().all():
        project_id = str(row["id"])
        # Filtrer par permissions si l'utilisateur n'est pas admin
        if user_permissions and user_permissions.get("projets"):
            if project_id not in user_permissions["projets"]:
                continue
        projects.append(ProjectSync(
            id=project_id,
            name=row["name"],
            description=row.get("description"),
            collectivite=row.get("collectivite_name"),
            collectivite_name=row.get("collectivite_name"),
            status=row.get("status"),
            is_active=row["is_active"] if row["is_active"] is not None else True,
        ))
    return projects


def coords_to_wkt(coords, geom_type: str) -> str:
    """Convertit des coordonnées en WKT."""
    if not coords:
        return None
    if geom_type == "POINT":
        return f"POINT({coords[0].longitude} {coords[0].latitude})"
    elif geom_type == "LINESTRING":
        points = ", ".join([f"{c.longitude} {c.latitude}" for c in coords])
        return f"LINESTRING({points})"
    elif geom_type == "POLYGON":
        if coords[0].latitude != coords[-1].latitude or coords[0].longitude != coords[-1].longitude:
            coords.append(coords[0])
        points = ", ".join([f"{c.longitude} {c.latitude}" for c in coords])
        return f"POLYGON(({points}))"
    return None


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    device_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère le statut de synchronisation."""
    # Dernière sync pour cet utilisateur
    result = await db.execute(
        text("""
            SELECT completed_at
            FROM sync_history
            WHERE user_id = :user_id
            ORDER BY completed_at DESC
            LIMIT 1
        """),
        {"user_id": str(current_user["id"])},
    )
    row = result.first()
    last_sync = row[0] if row else None

    # Points en attente d'upload (drafts locaux - géré côté mobile)
    pending_uploads = 0

    # Points à télécharger (modifiés depuis dernière sync)
    downloads_result = await db.execute(
        text("""
            SELECT COUNT(*)
            FROM geoclic_staging
            WHERE updated_at > :last_sync OR :last_sync IS NULL
        """),
        {"last_sync": last_sync},
    )
    pending_downloads = downloads_result.scalar() or 0

    # Version du lexique
    lexique_version = await get_lexique_version(db)

    # Compteurs
    lexique_count_result = await db.execute(
        text("SELECT COUNT(*) FROM lexique WHERE is_active = TRUE")
    )
    lexique_count = lexique_count_result.scalar() or 0

    projects_count_result = await db.execute(
        text("SELECT COUNT(*) FROM projects WHERE is_active = TRUE")
    )
    projects_count = projects_count_result.scalar() or 0

    return SyncStatusResponse(
        last_sync_at=last_sync,
        pending_uploads=pending_uploads,
        pending_downloads=pending_downloads,
        server_version="1.0.0",
        lexique_version=lexique_version,
        lexique_count=lexique_count,
        projects_count=projects_count,
    )


@router.get("/offline-package", response_model=OfflinePackageResponse)
async def get_offline_package(
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Récupère le package complet pour le mode offline.
    Inclut: lexique, champs dynamiques, projets, permissions utilisateur.
    Si project_id est fourni, filtre le lexique et les champs par projet.
    À appeler une fois lors de la première connexion ou après une longue absence.
    """
    # Récupérer les permissions utilisateur
    user_permissions = current_user.get("permissions", {})
    user_role = current_user.get("role", "viewer")

    # Pour les admins, pas de filtrage des projets
    if user_role == "admin":
        user_permissions = None

    # Récupérer toutes les données (filtrées par projet si spécifié)
    lexique_version = await get_lexique_version(db)
    lexique_entries = await get_lexique_entries(db, project_id)
    champs_dynamiques = await get_champs_dynamiques(db, project_id)
    projects = await get_projects(db, user_permissions)

    return OfflinePackageResponse(
        server_time=datetime.utcnow(),
        lexique_version=lexique_version,
        lexique_entries=lexique_entries,
        champs_dynamiques=champs_dynamiques,
        projects=projects,
        user_permissions=current_user.get("permissions", {}),
    )


@router.post("", response_model=SyncResponse)
async def sync_data(
    request: SyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Synchronisation bidirectionnelle."""
    errors = []
    points_uploaded = 0
    points_updated = 0
    points_deleted = 0

    # Créer une entrée dans l'historique
    sync_result = await db.execute(
        text("""
            INSERT INTO sync_history (user_id, device_id, sync_type)
            VALUES (:user_id, :device_id, 'full')
            RETURNING id
        """),
        {"user_id": str(current_user["id"]), "device_id": request.device_id},
    )
    sync_id = sync_result.scalar()

    # 1. UPLOAD - Créer les nouveaux points
    for point in request.points_to_upload:
        try:
            # Utiliser un savepoint pour isoler chaque INSERT
            # Si un INSERT échoue, on rollback au savepoint sans affecter les autres
            async with db.begin_nested():
                point_id = str(uuid.uuid4())
                wkt = coords_to_wkt(point.coordinates, point.geom_type.value)
                photos_json = json.dumps([p.model_dump() for p in point.photos]) if point.photos else "[]"
                custom_props_json = json.dumps(point.custom_properties) if point.custom_properties else None

                await db.execute(
                    text("""
                        INSERT INTO geoclic_staging (
                            id, project_id, name, lexique_code, type, subtype,
                            geom_type, geom, gps_precision, gps_source, altitude,
                            condition_state, point_status, sync_status, comment,
                            materiau, hauteur, largeur, date_installation,
                            priorite, cout_remplacement, custom_properties,
                            photos, color_value, icon_name, created_by
                        ) VALUES (
                            :id, :project_id, :name, :lexique_code, :type, :subtype,
                            :geom_type, ST_GeomFromText(:wkt, 4326), :gps_precision, :gps_source, :altitude,
                            :condition_state, :point_status, 'pending', :comment,
                            :materiau, :hauteur, :largeur, :date_installation,
                            :priorite, :cout_remplacement, CAST(:custom_properties AS jsonb),
                            CAST(:photos AS jsonb), :color_value, :icon_name, :created_by
                        )
                    """),
                    {
                        "id": point_id,
                        "project_id": point.project_id,
                        "name": point.name,
                        "lexique_code": point.lexique_code,
                        "type": point.type,
                        "subtype": point.subtype,
                        "geom_type": point.geom_type.value,
                        "wkt": wkt,
                        "gps_precision": point.gps_precision,
                        "gps_source": point.gps_source,
                        "altitude": point.altitude,
                        "condition_state": point.condition_state,
                        "point_status": point.point_status,
                        "comment": point.comment,
                        "materiau": point.materiau,
                        "hauteur": point.hauteur,
                        "largeur": point.largeur,
                        "date_installation": point.date_installation,
                        "priorite": point.priorite,
                        "cout_remplacement": point.cout_remplacement,
                        "custom_properties": custom_props_json,
                        "photos": photos_json,
                        "color_value": point.color_value,
                        "icon_name": point.icon_name,
                        "created_by": str(current_user["id"]),
                    },
                )
            points_uploaded += 1
        except Exception as e:
            errors.append(f"Erreur upload {point.name}: {str(e)}")

    # 2. UPDATE - Mettre à jour les points existants
    for update in request.points_to_update:
        point_id = update.pop("id", None)
        if not point_id:
            continue
        try:
            async with db.begin_nested():
                # Construire les updates
                set_clauses = ["updated_by = :updated_by"]
                params = {"id": point_id, "updated_by": str(current_user["id"])}

                for key, value in update.items():
                    if key == "coordinates" and value:
                        wkt = coords_to_wkt(value, "POINT")
                        set_clauses.append("geom = ST_GeomFromText(:wkt, 4326)")
                        params["wkt"] = wkt
                    else:
                        set_clauses.append(f"{key} = :{key}")
                        params[key] = value

                await db.execute(
                    text(f"""
                        UPDATE geoclic_staging
                        SET {', '.join(set_clauses)}
                        WHERE id = :id
                    """),
                    params,
                )
            points_updated += 1
        except Exception as e:
            errors.append(f"Erreur update {point_id}: {str(e)}")

    # 3. DELETE - Supprimer les points
    for point_id in request.points_to_delete:
        try:
            async with db.begin_nested():
                await db.execute(
                    text("""
                        DELETE FROM geoclic_staging
                        WHERE id = :id AND sync_status = 'draft'
                    """),
                    {"id": point_id},
                )
            points_deleted += 1
        except Exception as e:
            errors.append(f"Erreur delete {point_id}: {str(e)}")

    # 4. DOWNLOAD - Récupérer les points modifiés
    download_result = await db.execute(
        text("""
            SELECT *, ST_AsGeoJSON(geom)::json->'coordinates' as geom_coords
            FROM geoclic_staging
            WHERE (updated_at > :last_sync OR :last_sync IS NULL)
            ORDER BY updated_at DESC
            LIMIT 1000
        """),
        {"last_sync": request.last_sync_at},
    )
    download_rows = download_result.mappings().all()

    points_to_download = []
    for row in download_rows:
        row_dict = dict(row)
        # Convertir les coordonnées
        if row_dict.get("geom_coords"):
            coords = row_dict["geom_coords"]
            if row_dict.get("geom_type") == "POINT":
                row_dict["geom_coords"] = [[coords[1], coords[0]]]
            elif isinstance(coords[0], list):
                row_dict["geom_coords"] = [[c[1], c[0]] for c in coords]

        # Parser les photos
        photos = []
        if row_dict.get("photos"):
            try:
                photos_data = json.loads(row_dict["photos"]) if isinstance(row_dict["photos"], str) else row_dict["photos"]
                photos = [PhotoMetadataSchema(**p) for p in photos_data]
            except:
                pass

        # Convertir les coordonnées
        coordinates = []
        if row_dict.get("geom_coords"):
            coords_data = row_dict["geom_coords"]
            coordinates = [CoordinateSchema(latitude=c[0], longitude=c[1]) for c in coords_data]

        points_to_download.append(PointResponse(
            id=str(row_dict["id"]),
            name=row_dict["name"],
            lexique_code=row_dict.get("lexique_code"),
            type=row_dict["type"],
            subtype=row_dict.get("subtype"),
            geom_type=row_dict.get("geom_type", "POINT"),
            coordinates=coordinates,
            gps_precision=row_dict.get("gps_precision"),
            condition_state=row_dict.get("condition_state"),
            point_status=row_dict.get("point_status"),
            sync_status=row_dict.get("sync_status", "draft"),
            comment=row_dict.get("comment"),
            materiau=row_dict.get("materiau"),
            hauteur=row_dict.get("hauteur"),
            photos=photos,
            project_id=str(row_dict["project_id"]) if row_dict.get("project_id") else None,
            zone_name=row_dict.get("zone_name"),
            created_by=str(row_dict["created_by"]) if row_dict.get("created_by") else None,
            created_at=row_dict["created_at"],
            updated_at=row_dict.get("updated_at"),
        ))

    # Mettre à jour l'historique
    await db.execute(
        text("""
            UPDATE sync_history
            SET completed_at = CURRENT_TIMESTAMP,
                points_uploaded = :uploaded,
                points_downloaded = :downloaded,
                points_failed = :failed
            WHERE id = :id
        """),
        {
            "id": sync_id,
            "uploaded": points_uploaded,
            "downloaded": len(points_to_download),
            "failed": len(errors),
        },
    )

    await db.commit()

    # Vérifier si le lexique a changé
    current_lexique_version = await get_lexique_version(db)
    lexique_updated = (
        request.lexique_version is not None and
        request.lexique_version != current_lexique_version
    )

    # Inclure les données supplémentaires si demandé (filtrées par projet si spécifié)
    lexique_entries = []
    champs_dynamiques = []
    projects = []

    if request.include_lexique or lexique_updated:
        lexique_entries = await get_lexique_entries(db, request.project_id)

    if request.include_champs or lexique_updated:
        champs_dynamiques = await get_champs_dynamiques(db, request.project_id)

    if request.include_projects:
        user_permissions = current_user.get("permissions", {})
        if current_user.get("role") == "admin":
            user_permissions = None
        projects = await get_projects(db, user_permissions)

    return SyncResponse(
        success=len(errors) == 0,
        sync_id=sync_id,
        server_time=datetime.utcnow(),
        points_uploaded=points_uploaded,
        points_updated=points_updated,
        points_deleted=points_deleted,
        points_to_download=points_to_download,
        lexique_updated=lexique_updated,
        lexique_version=current_lexique_version,
        lexique_entries=lexique_entries,
        champs_dynamiques=champs_dynamiques,
        projects=projects,
        errors=errors,
    )
