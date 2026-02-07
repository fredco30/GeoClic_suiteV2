"""
Router pour les Points géographiques.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List
from datetime import datetime
from io import StringIO, BytesIO
from pathlib import Path
import json
import uuid
import csv
import zipfile
import os

from config import settings

from database import get_db
from routers.auth import get_current_user
from schemas.point import (
    PointCreate,
    PointUpdate,
    PointResponse,
    PointListResponse,
    SyncStatus,
    CoordinateSchema,
    PhotoMetadataSchema,
)

router = APIRouter()


def check_user_permissions(
    current_user: dict,
    project_id: Optional[str] = None,
    lexique_code: Optional[str] = None,
) -> None:
    """
    Vérifie que l'utilisateur a les permissions pour accéder au projet et/ou catégorie.
    Lève une HTTPException 403 si les permissions sont insuffisantes.
    Les admins passent toujours.
    """
    # Les admins ont tous les droits
    if current_user.get("is_super_admin") or current_user.get("role_data") == "admin":
        return

    user_permissions = current_user.get("permissions") or {}
    allowed_projects = user_permissions.get("projets", [])
    allowed_categories = user_permissions.get("categories", [])

    # Vérifier l'accès au projet
    if project_id and allowed_projects:
        if project_id not in allowed_projects:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Vous n'avez pas accès au projet '{project_id}'. Contactez un administrateur.",
            )

    # Vérifier l'accès à la catégorie (lexique_code)
    if lexique_code and allowed_categories:
        # Vérifier si le code ou un de ses parents est autorisé
        code_parts = lexique_code.split("_")  # ex: "ECL_LAM_LED" -> ["ECL", "LAM", "LED"]
        is_allowed = False
        for i in range(len(code_parts)):
            partial_code = "_".join(code_parts[:i+1])
            if partial_code in allowed_categories:
                is_allowed = True
                break
        if not is_allowed and lexique_code not in allowed_categories:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Vous n'avez pas accès à la catégorie '{lexique_code}'. Contactez un administrateur.",
            )


def coords_to_wkt(coords: List[CoordinateSchema], geom_type: str) -> str:
    """Convertit des coordonnées en WKT."""
    if not coords:
        return None

    if geom_type == "POINT":
        return f"POINT({coords[0].longitude} {coords[0].latitude})"
    elif geom_type == "LINESTRING":
        points = ", ".join([f"{c.longitude} {c.latitude}" for c in coords])
        return f"LINESTRING({points})"
    elif geom_type == "POLYGON":
        # Fermer le polygone si nécessaire
        if coords[0].latitude != coords[-1].latitude or coords[0].longitude != coords[-1].longitude:
            coords.append(coords[0])
        points = ", ".join([f"{c.longitude} {c.latitude}" for c in coords])
        return f"POLYGON(({points}))"
    return None


def row_to_point_response(row: dict) -> PointResponse:
    """Convertit une ligne DB en PointResponse."""
    # Parser les coordonnées depuis geom
    coordinates = []
    if row.get("geom_coords"):
        try:
            coords_data = json.loads(row["geom_coords"]) if isinstance(row["geom_coords"], str) else row["geom_coords"]
            coordinates = [CoordinateSchema(latitude=c[0], longitude=c[1]) for c in coords_data]
        except:
            pass

    # Parser les photos
    photos = []
    if row.get("photos"):
        try:
            photos_data = json.loads(row["photos"]) if isinstance(row["photos"], str) else row["photos"]
            photos = [PhotoMetadataSchema(**p) for p in photos_data]
        except:
            pass

    return PointResponse(
        id=str(row["id"]),
        name=row["name"],
        lexique_code=row.get("lexique_code"),
        type=row["type"],
        subtype=row.get("subtype"),
        geom_type=row.get("geom_type", "POINT"),
        coordinates=coordinates,
        gps_precision=row.get("gps_precision"),
        gps_source=row.get("gps_source"),
        altitude=row.get("altitude"),
        condition_state=row.get("condition_state"),
        point_status=row.get("point_status"),
        sync_status=row.get("sync_status", "draft"),
        rejection_comment=row.get("rejection_comment"),
        comment=row.get("comment"),
        materiau=row.get("materiau"),
        hauteur=row.get("hauteur"),
        largeur=row.get("largeur"),
        date_installation=row.get("date_installation"),
        priorite=row.get("priorite"),
        cout_remplacement=row.get("cout_remplacement"),
        custom_properties=row.get("custom_properties"),
        project_id=str(row["project_id"]) if row.get("project_id") else None,
        zone_name=row.get("zone_name"),
        photos=photos,
        created_by=str(row["created_by"]) if row.get("created_by") else None,
        updated_by=str(row["updated_by"]) if row.get("updated_by") else None,
        created_at=row["created_at"],
        updated_at=row.get("updated_at"),
        color_value=row.get("color_value"),
        icon_name=row.get("icon_name"),
    )


@router.get("", response_model=PointListResponse)
async def list_points(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    project_id: Optional[str] = None,
    sync_status: Optional[SyncStatus] = None,
    type_filter: Optional[str] = None,
    lexique_code: Optional[str] = None,
    search: Optional[str] = Query(None, min_length=1, description="Recherche dans nom et commentaire"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Liste les points avec pagination, filtres et recherche."""
    offset = (page - 1) * page_size

    # Construction de la requête
    where_clauses = []
    params = {"limit": page_size, "offset": offset}

    if project_id:
        where_clauses.append("project_id = :project_id")
        params["project_id"] = project_id

    if sync_status:
        where_clauses.append("sync_status = :sync_status")
        params["sync_status"] = sync_status.value

    if type_filter:
        where_clauses.append("type = :type_filter")
        params["type_filter"] = type_filter

    if lexique_code:
        # Support comma-separated codes for hierarchical filtering
        codes = [c.strip() for c in lexique_code.split(',') if c.strip()]
        if len(codes) == 1:
            where_clauses.append("lexique_code = :lexique_code")
            params["lexique_code"] = codes[0]
        else:
            lc_placeholders = ", ".join([f":lc_{i}" for i in range(len(codes))])
            where_clauses.append(f"lexique_code IN ({lc_placeholders})")
            for i, c in enumerate(codes):
                params[f"lc_{i}"] = c

    if search:
        # Recherche insensible à la casse dans nom et commentaire
        where_clauses.append("(LOWER(name) LIKE :search OR LOWER(comment) LIKE :search)")
        params["search"] = f"%{search.lower()}%"

    # Sécurité : les where_clauses ci-dessus sont toutes des littérales du code
    # avec valeurs paramétrées (:param). Aucune donnée utilisateur dans la structure SQL.
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Compter le total
    count_result = await db.execute(
        text(f"SELECT COUNT(*) FROM geoclic_staging WHERE {where_sql}"),
        params,
    )
    total = count_result.scalar()

    # Récupérer les points avec coordonnées extraites
    result = await db.execute(
        text(f"""
            SELECT *,
                   ST_AsGeoJSON(geom)::json->'coordinates' as geom_coords
            FROM geoclic_staging
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )
    rows = result.mappings().all()

    # Convertir les rows
    items = []
    for row in rows:
        row_dict = dict(row)
        # Convertir geom_coords en format attendu
        if row_dict.get("geom_coords"):
            coords = row_dict["geom_coords"]
            if row_dict.get("geom_type") == "POINT":
                row_dict["geom_coords"] = [[coords[1], coords[0]]]  # [lat, lng]
            elif isinstance(coords[0], list):
                row_dict["geom_coords"] = [[c[1], c[0]] for c in coords]
        items.append(row_to_point_response(row_dict))

    return PointListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.post("", response_model=PointResponse, status_code=status.HTTP_201_CREATED)
async def create_point(
    point: PointCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Crée un nouveau point."""
    import logging
    logger = logging.getLogger(__name__)

    # Vérifier les permissions de l'utilisateur
    check_user_permissions(current_user, point.project_id, point.lexique_code)

    point_id = str(uuid.uuid4())
    wkt = coords_to_wkt(point.coordinates, point.geom_type.value)

    photos_json = json.dumps([p.model_dump() for p in point.photos]) if point.photos else "[]"
    custom_props_json = json.dumps(point.custom_properties) if point.custom_properties else None

    try:
        result = await db.execute(
            text("""
                INSERT INTO geoclic_staging (
                    id, project_id, name, lexique_code, type, subtype,
                    geom_type, geom, gps_precision, gps_source, altitude,
                    condition_state, point_status, sync_status, comment,
                    materiau, hauteur, largeur, date_installation,
                    priorite, cout_remplacement, custom_properties,
                    photos, color_value, icon_name, created_by
                ) VALUES (
                    :id, CAST(:project_id AS uuid), :name, :lexique_code, :type, :subtype,
                    :geom_type, ST_GeomFromText(:wkt, 4326), :gps_precision, :gps_source, :altitude,
                    :condition_state, :point_status, 'draft', :comment,
                    :materiau, :hauteur, :largeur, :date_installation,
                    :priorite, :cout_remplacement, CAST(:custom_properties AS jsonb),
                    CAST(:photos AS jsonb), :color_value, :icon_name, CAST(:created_by AS uuid)
                )
                RETURNING *, ST_AsGeoJSON(geom)::json->'coordinates' as geom_coords
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
        await db.commit()
        row = result.mappings().first()
        row_dict = dict(row)

        # Convertir les coordonnées
        if row_dict.get("geom_coords"):
            coords = row_dict["geom_coords"]
            if row_dict.get("geom_type") == "POINT":
                row_dict["geom_coords"] = [[coords[1], coords[0]]]

        return row_to_point_response(row_dict)

    except Exception as e:
        await db.rollback()
        logger.error(f"Erreur création point: {type(e).__name__}: {e}")
        logger.error(f"User: {current_user.get('id')}, project: {point.project_id}, name: {point.name}")
        raise HTTPException(status_code=500, detail=f"Erreur création point: {type(e).__name__}: {str(e)}")


# ============================================================================
# ROUTES SPÉCIFIQUES (doivent être AVANT /{point_id})
# ============================================================================

@router.get("/check-duplicate")
async def check_duplicate(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(10, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Vérifie les doublons potentiels dans un rayon donné (en mètres)."""
    result = await db.execute(
        text("""
            SELECT id, name, type,
                   ST_Distance(
                       geom::geography,
                       ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                   ) as distance,
                   ST_Y(geom::geometry) as latitude,
                   ST_X(geom::geometry) as longitude
            FROM geoclic_staging
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                :radius
            )
            ORDER BY distance
            LIMIT 10
        """),
        {"lat": lat, "lng": lng, "radius": radius},
    )
    rows = result.mappings().all()

    nearby_points = [
        {
            "id": str(row["id"]),
            "name": row["name"],
            "type": row["type"],
            "distance": round(row["distance"], 2),
            "latitude": row["latitude"],
            "longitude": row["longitude"],
        }
        for row in rows
    ]

    return {
        "has_duplicate": len(nearby_points) > 0,
        "nearby_points": nearby_points,
        "min_distance": nearby_points[0]["distance"] if nearby_points else None,
        "search_radius": radius,
    }


@router.get("/export/geojson")
async def export_geojson(
    project_id: Optional[str] = None,
    sync_status: Optional[SyncStatus] = None,
    lexique_code: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Exporte les points en GeoJSON avec tous les champs dynamiques."""
    where_clauses = []
    params = {}

    if project_id:
        where_clauses.append("project_id = :project_id")
        params["project_id"] = project_id

    if sync_status:
        where_clauses.append("sync_status = :sync_status")
        params["sync_status"] = sync_status.value

    if lexique_code:
        # Support comma-separated codes for hierarchical filtering
        codes = [c.strip() for c in lexique_code.split(',') if c.strip()]
        if len(codes) == 1:
            where_clauses.append("lexique_code = :lexique_code")
            params["lexique_code"] = codes[0]
        else:
            lc_placeholders = ", ".join([f":lc_{i}" for i in range(len(codes))])
            where_clauses.append(f"lexique_code IN ({lc_placeholders})")
            for i, c in enumerate(codes):
                params[f"lc_{i}"] = c

    if date_start:
        where_clauses.append("created_at >= :date_start")
        params["date_start"] = date_start

    if date_end:
        where_clauses.append("created_at <= :date_end")
        params["date_end"] = f"{date_end} 23:59:59"

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    result = await db.execute(
        text(f"""
            SELECT id, name, type, subtype, lexique_code,
                   condition_state, point_status, sync_status,
                   comment, photos, custom_properties,
                   materiau, hauteur, largeur,
                   created_at, updated_at,
                   ST_AsGeoJSON(geom)::json as geometry
            FROM geoclic_staging
            WHERE {where_sql}
            ORDER BY created_at DESC
        """),
        params,
    )
    rows = result.mappings().all()

    features = []
    for row in rows:
        # Propriétés de base
        properties = {
            "name": row["name"],
            "type": row["type"],
            "subtype": row["subtype"],
            "lexique_code": row["lexique_code"],
            "condition_state": row["condition_state"],
            "point_status": row["point_status"],
            "sync_status": row["sync_status"],
            "comment": row["comment"],
            "materiau": row["materiau"],
            "hauteur": row["hauteur"],
            "largeur": row["largeur"],
            "photos": row["photos"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        }

        # Ajouter les champs dynamiques (custom_properties)
        if row["custom_properties"]:
            custom = row["custom_properties"]
            if isinstance(custom, str):
                custom = json.loads(custom)
            for key, value in custom.items():
                properties[f"custom_{key}"] = value

        feature = {
            "type": "Feature",
            "id": str(row["id"]),
            "geometry": row["geometry"],
            "properties": properties,
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    return geojson


@router.get("/export/csv")
async def export_csv(
    project_id: Optional[str] = None,
    sync_status: Optional[SyncStatus] = None,
    lexique_code: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Exporte les points en CSV avec tous les champs dynamiques."""
    where_clauses = []
    params = {}

    if project_id:
        where_clauses.append("project_id = :project_id")
        params["project_id"] = project_id

    if sync_status:
        where_clauses.append("sync_status = :sync_status")
        params["sync_status"] = sync_status.value

    if lexique_code:
        # Support comma-separated codes for hierarchical filtering
        codes = [c.strip() for c in lexique_code.split(',') if c.strip()]
        if len(codes) == 1:
            where_clauses.append("lexique_code = :lexique_code")
            params["lexique_code"] = codes[0]
        else:
            lc_placeholders = ", ".join([f":lc_{i}" for i in range(len(codes))])
            where_clauses.append(f"lexique_code IN ({lc_placeholders})")
            for i, c in enumerate(codes):
                params[f"lc_{i}"] = c

    if date_start:
        where_clauses.append("created_at >= :date_start")
        params["date_start"] = date_start

    if date_end:
        where_clauses.append("created_at <= :date_end")
        params["date_end"] = f"{date_end} 23:59:59"

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    result = await db.execute(
        text(f"""
            SELECT id, name, type, subtype, lexique_code,
                   condition_state, point_status, sync_status,
                   comment, materiau, hauteur, largeur,
                   photos, custom_properties,
                   ST_Y(geom::geometry) as latitude,
                   ST_X(geom::geometry) as longitude,
                   created_at, updated_at
            FROM geoclic_staging
            WHERE {where_sql}
            ORDER BY created_at DESC
        """),
        params,
    )
    rows = result.mappings().all()

    # Collecter tous les champs dynamiques uniques
    all_custom_keys = set()
    parsed_rows = []
    for row in rows:
        row_dict = dict(row)
        custom = row["custom_properties"]
        if custom:
            if isinstance(custom, str):
                custom = json.loads(custom)
            row_dict["_custom"] = custom
            all_custom_keys.update(custom.keys())
        else:
            row_dict["_custom"] = {}
        parsed_rows.append(row_dict)

    # Trier les clés custom pour cohérence
    custom_keys_sorted = sorted(all_custom_keys)

    output = StringIO()
    writer = csv.writer(output, delimiter=';')

    # En-têtes de base + champs dynamiques
    base_headers = [
        "ID", "Nom", "Type", "Sous-type", "Code Lexique",
        "État", "Statut", "Sync", "Commentaire",
        "Matériau", "Hauteur", "Largeur",
        "Latitude", "Longitude", "Photos",
        "Date création", "Date modification"
    ]
    headers = base_headers + [f"[{k}]" for k in custom_keys_sorted]
    writer.writerow(headers)

    # Données
    for row in parsed_rows:
        # Gérer les photos (liste → chaîne)
        photos_str = ""
        if row["photos"]:
            photos = row["photos"]
            if isinstance(photos, str):
                photos = json.loads(photos)
            if isinstance(photos, list):
                photos_str = " | ".join(str(p) for p in photos)

        base_data = [
            str(row["id"]),
            row["name"] or "",
            row["type"] or "",
            row["subtype"] or "",
            row["lexique_code"] or "",
            row["condition_state"] or "",
            row["point_status"] or "",
            row["sync_status"] or "",
            row["comment"] or "",
            row["materiau"] or "",
            str(row["hauteur"]) if row["hauteur"] else "",
            str(row["largeur"]) if row["largeur"] else "",
            str(row["latitude"]) if row["latitude"] else "",
            str(row["longitude"]) if row["longitude"] else "",
            photos_str,
            row["created_at"].isoformat() if row["created_at"] else "",
            row["updated_at"].isoformat() if row["updated_at"] else "",
        ]

        # Ajouter les valeurs des champs dynamiques
        custom_data = []
        for key in custom_keys_sorted:
            value = row["_custom"].get(key, "")
            # Convertir les listes en chaîne
            if isinstance(value, list):
                value = " | ".join(str(v) for v in value)
            custom_data.append(str(value) if value else "")

        writer.writerow(base_data + custom_data)

    output.seek(0)

    # Nom du fichier avec date
    filename = f"geoclic_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/export/zip")
async def export_zip_with_photos(
    project_id: Optional[str] = None,
    sync_status: Optional[SyncStatus] = None,
    lexique_code: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    max_points: int = Query(100, ge=1, le=500, description="Nombre max de points à exporter"),
    max_photos: int = Query(200, ge=1, le=1000, description="Nombre max de photos à inclure"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Exporte les points en ZIP avec les fichiers photos physiques.

    Contenu du ZIP:
    - data.geojson : Données des points au format GeoJSON
    - data.csv : Données des points au format CSV
    - photos/ : Dossier contenant les fichiers photos

    Les fichiers photos sont nommés: {id_point_court}_{numero}.jpg
    """
    # Construire les filtres
    where_clauses = []
    params = {}

    if project_id:
        where_clauses.append("project_id = :project_id")
        params["project_id"] = project_id

    if sync_status:
        where_clauses.append("sync_status = :sync_status")
        params["sync_status"] = sync_status.value

    if lexique_code:
        # Support comma-separated codes for hierarchical filtering
        codes = [c.strip() for c in lexique_code.split(',') if c.strip()]
        if len(codes) == 1:
            where_clauses.append("lexique_code = :lexique_code")
            params["lexique_code"] = codes[0]
        else:
            lc_placeholders = ", ".join([f":lc_{i}" for i in range(len(codes))])
            where_clauses.append(f"lexique_code IN ({lc_placeholders})")
            for i, c in enumerate(codes):
                params[f"lc_{i}"] = c

    if date_start:
        where_clauses.append("created_at >= :date_start")
        params["date_start"] = date_start

    if date_end:
        where_clauses.append("created_at <= :date_end")
        params["date_end"] = f"{date_end} 23:59:59"

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Récupérer les points (limité)
    result = await db.execute(
        text(f"""
            SELECT id, name, type, subtype, lexique_code,
                   condition_state, point_status, sync_status,
                   comment, photos, custom_properties,
                   materiau, hauteur, largeur,
                   created_at, updated_at,
                   ST_AsGeoJSON(geom)::json as geometry,
                   ST_X(geom::geometry) as longitude,
                   ST_Y(geom::geometry) as latitude
            FROM geoclic_staging
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :max_points
        """),
        {**params, "max_points": max_points},
    )
    rows = result.mappings().all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun point trouvé avec ces critères"
        )

    # Créer le ZIP en mémoire
    zip_buffer = BytesIO()
    photos_added = 0
    photos_errors = []

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Préparer les données GeoJSON et CSV
        features = []
        csv_rows = []
        csv_headers = ["id", "name", "type", "lexique_code", "latitude", "longitude",
                       "condition_state", "point_status", "sync_status", "comment",
                       "photos_count", "created_at"]

        for row in rows:
            point_id = str(row["id"])
            short_id = point_id[:8]  # ID court pour les noms de fichiers

            # Traiter les photos
            photos_data = row["photos"] or []
            if isinstance(photos_data, str):
                try:
                    photos_data = json.loads(photos_data)
                except:
                    photos_data = []

            photo_files_in_zip = []
            for idx, photo in enumerate(photos_data):
                if photos_added >= max_photos:
                    break

                # Extraire l'URL de la photo
                photo_url = photo.get("url") if isinstance(photo, dict) else photo
                if not photo_url:
                    continue

                # Construire le chemin du fichier physique
                # URL format: /api/photos/2026/01/filename.jpg
                if photo_url.startswith("/api/photos/"):
                    relative_path = photo_url.replace("/api/photos/", "")
                    file_path = Path(settings.photo_storage_path) / relative_path
                else:
                    continue

                # Ajouter au ZIP si le fichier existe
                if file_path.exists():
                    # Extension du fichier original
                    ext = file_path.suffix or ".jpg"
                    zip_filename = f"photos/{short_id}_{idx + 1}{ext}"

                    try:
                        zip_file.write(file_path, zip_filename)
                        photo_files_in_zip.append(zip_filename)
                        photos_added += 1
                    except Exception as e:
                        photos_errors.append(f"{point_id}: {str(e)}")
                else:
                    photos_errors.append(f"{point_id}: fichier non trouvé {file_path}")

            # Préparer le feature GeoJSON
            properties = {
                "id": point_id,
                "name": row["name"],
                "type": row["type"],
                "subtype": row["subtype"],
                "lexique_code": row["lexique_code"],
                "condition_state": row["condition_state"],
                "point_status": row["point_status"],
                "sync_status": row["sync_status"],
                "comment": row["comment"],
                "materiau": row["materiau"],
                "hauteur": row["hauteur"],
                "largeur": row["largeur"],
                "photos": photo_files_in_zip,  # Chemins relatifs dans le ZIP
                "photos_metadata": photos_data,  # Métadonnées originales
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
            }

            # Ajouter les champs dynamiques
            if row["custom_properties"]:
                custom = row["custom_properties"]
                if isinstance(custom, str):
                    custom = json.loads(custom)
                for key, value in custom.items():
                    properties[f"custom_{key}"] = value

            feature = {
                "type": "Feature",
                "id": point_id,
                "geometry": row["geometry"],
                "properties": properties,
            }
            features.append(feature)

            # Préparer la ligne CSV
            csv_rows.append({
                "id": point_id,
                "name": row["name"],
                "type": row["type"],
                "lexique_code": row["lexique_code"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "condition_state": row["condition_state"],
                "point_status": row["point_status"],
                "sync_status": row["sync_status"],
                "comment": row["comment"],
                "photos_count": len(photo_files_in_zip),
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            })

        # Écrire le GeoJSON
        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "points_count": len(features),
                "photos_count": photos_added,
                "photos_errors": len(photos_errors),
            }
        }
        zip_file.writestr("data.geojson", json.dumps(geojson, ensure_ascii=False, indent=2))

        # Écrire le CSV
        csv_output = StringIO()
        writer = csv.DictWriter(csv_output, fieldnames=csv_headers, delimiter=';')
        writer.writeheader()
        writer.writerows(csv_rows)
        zip_file.writestr("data.csv", csv_output.getvalue())

        # Écrire un fichier README
        readme_content = f"""# Export GéoClic Data
Exporté le: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

## Contenu
- data.geojson : {len(features)} points au format GeoJSON
- data.csv : {len(features)} points au format CSV (séparateur: ;)
- photos/ : {photos_added} fichiers photos

## Format des noms de photos
Les photos sont nommées: {{id_point_court}}_{{numero}}.jpg
Exemple: 3a32b799_1.jpg = première photo du point 3a32b799-xxxx-xxxx-xxxx

## Erreurs photos ({len(photos_errors)})
{chr(10).join(photos_errors) if photos_errors else "Aucune erreur"}
"""
        zip_file.writestr("README.txt", readme_content)

    # Retourner le ZIP
    zip_buffer.seek(0)
    filename = f"geoclic_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ============================================================================
# ROUTES AVEC PARAMÈTRE DYNAMIQUE (doivent être APRÈS les routes spécifiques)
# ============================================================================

@router.get("/{point_id}", response_model=PointResponse)
async def get_point(
    point_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère un point par son ID."""
    result = await db.execute(
        text("""
            SELECT *, ST_AsGeoJSON(geom)::json->'coordinates' as geom_coords
            FROM geoclic_staging
            WHERE id = :id
        """),
        {"id": point_id},
    )
    row = result.mappings().first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Point non trouvé",
        )

    row_dict = dict(row)
    if row_dict.get("geom_coords"):
        coords = row_dict["geom_coords"]
        if row_dict.get("geom_type") == "POINT":
            row_dict["geom_coords"] = [[coords[1], coords[0]]]
        elif isinstance(coords[0], list):
            row_dict["geom_coords"] = [[c[1], c[0]] for c in coords]

    return row_to_point_response(row_dict)


@router.patch("/{point_id}", response_model=PointResponse)
async def update_point(
    point_id: str,
    updates: PointUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Met à jour un point."""
    # Vérifier que le point existe et est modifiable
    result = await db.execute(
        text("SELECT sync_status, project_id, lexique_code FROM geoclic_staging WHERE id = :id"),
        {"id": point_id},
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Point non trouvé")

    # Vérifier les permissions sur le point existant
    check_user_permissions(current_user, str(row[1]) if row[1] else None, row[2])

    # Vérifier les permissions sur les nouvelles valeurs (si modification)
    update_data = updates.model_dump(exclude_unset=True)
    if "lexique_code" in update_data:
        check_user_permissions(current_user, None, update_data["lexique_code"])

    # Vérifier si modifiable (draft ou rejected)
    if row[0] not in ("draft", "rejected"):
        raise HTTPException(
            status_code=400,
            detail=f"Point non modifiable (statut: {row[0]})",
        )

    # Construire la requête de mise à jour
    update_fields = []
    params = {"id": point_id, "updated_by": str(current_user["id"])}

    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "coordinates" and value:
            # Reconvertir les dicts en CoordinateSchema (model_dump les a sérialisés)
            coord_objects = [CoordinateSchema(**c) if isinstance(c, dict) else c for c in value]
            wkt = coords_to_wkt(coord_objects, "POINT")  # TODO: gérer le type
            update_fields.append("geom = ST_GeomFromText(:wkt, 4326)")
            params["wkt"] = wkt
        elif key == "photos" and value:
            update_fields.append("photos = CAST(:photos AS jsonb)")
            # value est déjà une liste de dicts après model_dump()
            params["photos"] = json.dumps(value if isinstance(value[0], dict) else [p.model_dump() for p in value])
        elif key == "custom_properties" and value:
            update_fields.append("custom_properties = CAST(:custom_properties AS jsonb)")
            params["custom_properties"] = json.dumps(value)
        elif key == "sync_status" and value:
            update_fields.append("sync_status = :sync_status")
            # value est déjà une string après model_dump()
            params["sync_status"] = value.value if hasattr(value, 'value') else value
        else:
            update_fields.append(f"{key} = :{key}")
            params[key] = value

    update_fields.append("updated_by = :updated_by")

    if not update_fields:
        raise HTTPException(status_code=400, detail="Aucune modification")

    import logging
    logger = logging.getLogger(__name__)

    try:
        sql = f"""
            UPDATE geoclic_staging
            SET {', '.join(update_fields)}
            WHERE id = :id
            RETURNING *, ST_AsGeoJSON(geom)::json->'coordinates' as geom_coords
        """
        logger.info(f"UPDATE point {point_id}: fields={list(update_data.keys())}")
        result = await db.execute(text(sql), params)
        await db.commit()
        row = result.mappings().first()

        if not row:
            raise HTTPException(status_code=404, detail="Point non trouvé après mise à jour")

        row_dict = dict(row)

        if row_dict.get("geom_coords"):
            coords = row_dict["geom_coords"]
            if row_dict.get("geom_type") == "POINT":
                row_dict["geom_coords"] = [[coords[1], coords[0]]]

        return row_to_point_response(row_dict)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Erreur PATCH point {point_id}: {type(e).__name__}: {e}")
        logger.error(f"Fields: {list(update_data.keys())}, Params keys: {list(params.keys())}")
        raise HTTPException(status_code=500, detail=f"Erreur mise à jour point: {type(e).__name__}: {str(e)}")


@router.delete("/{point_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_point(
    point_id: str,
    force: bool = Query(False, description="Forcer la suppression quel que soit le statut"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Supprime un point.

    - Les brouillons (draft) peuvent être supprimés par tous
    - Les points validés/en attente nécessitent force=true ou rôle admin/moderator
    """
    result = await db.execute(
        text("SELECT sync_status FROM geoclic_staging WHERE id = :id"),
        {"id": point_id},
    )
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Point non trouvé")

    sync_status = row[0]

    # Brouillons: suppression libre
    # Autres statuts: nécessite force=true ou droits élevés
    if sync_status != "draft":
        is_admin_or_mod = current_user.get("is_super_admin") or current_user.get("role_data") in ("admin",)
        if not force and not is_admin_or_mod:
            raise HTTPException(
                status_code=400,
                detail=f"Point en statut '{sync_status}'. Utilisez force=true ou connectez-vous en admin/modérateur pour supprimer.",
            )

    await db.execute(
        text("DELETE FROM geoclic_staging WHERE id = :id"),
        {"id": point_id},
    )
    await db.commit()


@router.post("/{point_id}/submit", response_model=PointResponse)
async def submit_for_validation(
    point_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Soumet un point pour validation."""
    result = await db.execute(
        text("""
            UPDATE geoclic_staging
            SET sync_status = 'pending', updated_by = :user_id
            WHERE id = :id AND sync_status IN ('draft', 'rejected')
            RETURNING *, ST_AsGeoJSON(geom)::json->'coordinates' as geom_coords
        """),
        {"id": point_id, "user_id": str(current_user["id"])},
    )
    await db.commit()
    row = result.mappings().first()

    if not row:
        raise HTTPException(
            status_code=400,
            detail="Point non trouvé ou non soumissible",
        )

    row_dict = dict(row)
    if row_dict.get("geom_coords"):
        coords = row_dict["geom_coords"]
        if row_dict.get("geom_type") == "POINT":
            row_dict["geom_coords"] = [[coords[1], coords[0]]]

    return row_to_point_response(row_dict)


@router.post("/{point_id}/validate", response_model=PointResponse)
async def validate_point(
    point_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Valide un point (modérateur/admin)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    result = await db.execute(
        text("""
            UPDATE geoclic_staging
            SET sync_status = 'validated',
                validated_by = :user_id,
                validated_at = CURRENT_TIMESTAMP
            WHERE id = :id AND sync_status = 'pending'
            RETURNING *, ST_AsGeoJSON(geom)::json->'coordinates' as geom_coords
        """),
        {"id": point_id, "user_id": str(current_user["id"])},
    )
    await db.commit()
    row = result.mappings().first()

    if not row:
        raise HTTPException(
            status_code=400,
            detail="Point non trouvé ou non validable",
        )

    row_dict = dict(row)
    if row_dict.get("geom_coords"):
        coords = row_dict["geom_coords"]
        if row_dict.get("geom_type") == "POINT":
            row_dict["geom_coords"] = [[coords[1], coords[0]]]

    return row_to_point_response(row_dict)


@router.post("/{point_id}/reject", response_model=PointResponse)
async def reject_point(
    point_id: str,
    comment: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Rejette un point (modérateur/admin)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    result = await db.execute(
        text("""
            UPDATE geoclic_staging
            SET sync_status = 'rejected',
                rejection_comment = :comment,
                updated_by = :user_id
            WHERE id = :id AND sync_status = 'pending'
            RETURNING *, ST_AsGeoJSON(geom)::json->'coordinates' as geom_coords
        """),
        {"id": point_id, "comment": comment, "user_id": str(current_user["id"])},
    )
    await db.commit()
    row = result.mappings().first()

    if not row:
        raise HTTPException(
            status_code=400,
            detail="Point non trouvé ou non rejetable",
        )

    row_dict = dict(row)
    if row_dict.get("geom_coords"):
        coords = row_dict["geom_coords"]
        if row_dict.get("geom_type") == "POINT":
            row_dict["geom_coords"] = [[coords[1], coords[0]]]

    return row_to_point_response(row_dict)

