"""
Router pour la gestion des zones géographiques hiérarchiques.

Les zones sont stockées dans la table 'perimetres' avec une structure hiérarchique:
- Level 1: Commune (parent_id = NULL)
- Level 2: Quartier / IRIS
- Level 3: Secteur

Elles peuvent être:
- Globales (is_global=TRUE): partagées par tous les projets
- Spécifiques à un projet (project_id défini)
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import httpx

from database import get_db
from routers.auth import get_current_user
from schemas.zones import (
    ZoneCreate, ZoneUpdate, ZoneResponse, ZoneWithGeometry,
    ZoneGeoJSON, ZonesGeoJSONCollection,
    ZoneHierarchyItem, ZoneHierarchyResponse, ZoneChildrenResponse,
    ZoneStatsResponse, ZonePointHierarchy,
    IRISImportRequest, IRISImportResponse, ZoneOverlapCheck
)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES STATIQUES (AVANT LES ROUTES PARAMÉTRÉES)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/hierarchy", response_model=ZoneHierarchyResponse)
async def get_zones_hierarchy(
    level: Optional[int] = Query(None, ge=1, le=3, description="Filtrer par niveau"),
    project_id: Optional[str] = Query(None, description="Filtrer par projet"),
    include_global: bool = Query(True, description="Inclure les zones globales"),
    db: AsyncSession = Depends(get_db),
):
    """
    Récupère l'arbre hiérarchique des zones.

    Retourne une structure imbriquée avec les enfants dans chaque zone.
    """
    # Récupérer toutes les zones avec leurs infos
    filters = []
    params = {}

    if level is not None:
        filters.append("p.level = :level")
        params["level"] = level

    project_filter_parts = []
    if project_id:
        project_filter_parts.append("p.project_id = CAST(:project_id AS uuid)")
        params["project_id"] = project_id
    if include_global:
        project_filter_parts.append("p.is_global = TRUE")
        project_filter_parts.append("p.project_id IS NULL")

    if project_filter_parts:
        filters.append(f"({' OR '.join(project_filter_parts)})")

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    result = await db.execute(text(f"""
        SELECT
            p.id, p.name, p.code, p.perimetre_type as zone_type,
            p.level, p.parent_id, p.is_global,
            CAST(p.project_id AS text) as project_id,
            parent.name as parent_name,
            (SELECT COUNT(*) FROM perimetres c WHERE c.parent_id = p.id) as children_count,
            COALESCE((SELECT COUNT(*) FROM demandes_citoyens d WHERE d.quartier_id = p.id), 0) as total_demandes
        FROM perimetres p
        LEFT JOIN perimetres parent ON p.parent_id = parent.id
        {where_clause}
        ORDER BY p.level, p.name
    """), params)

    rows = result.fetchall()

    # Construire l'arbre
    zones_by_id = {}
    root_zones = []

    for row in rows:
        zone = ZoneHierarchyItem(
            id=str(row.id),
            name=row.name,
            code=row.code,
            zone_type=row.zone_type or "quartier",
            level=row.level or 2,
            parent_id=str(row.parent_id) if row.parent_id else None,
            parent_name=row.parent_name,
            is_global=row.is_global or False,
            project_id=row.project_id,
            children=[],
            total_demandes=row.total_demandes,
            children_count=row.children_count,
        )
        zones_by_id[str(row.id)] = zone

    # Rattacher les enfants à leurs parents
    for zone_id, zone in zones_by_id.items():
        if zone.parent_id and zone.parent_id in zones_by_id:
            zones_by_id[zone.parent_id].children.append(zone)
        else:
            root_zones.append(zone)

    return ZoneHierarchyResponse(
        zones=root_zones,
        total_count=len(zones_by_id),
    )


@router.get("/geojson", response_model=ZonesGeoJSONCollection)
async def get_zones_geojson(
    zone_type: Optional[str] = Query(None, description="Filtrer par type"),
    level: Optional[int] = Query(None, ge=1, le=3, description="Filtrer par niveau"),
    project_id: Optional[str] = Query(None, description="Filtrer par projet"),
    include_global: bool = Query(True, description="Inclure les zones globales"),
    db: AsyncSession = Depends(get_db),
):
    """Récupère toutes les zones au format GeoJSON FeatureCollection."""

    filters = []
    params = {}

    if zone_type:
        filters.append("perimetre_type = :zone_type")
        params["zone_type"] = zone_type

    if level is not None:
        filters.append("level = :level")
        params["level"] = level

    project_filter_parts = []
    if project_id:
        project_filter_parts.append("project_id = CAST(:project_id AS uuid)")
        params["project_id"] = project_id
    if include_global:
        project_filter_parts.append("is_global = TRUE")
        project_filter_parts.append("project_id IS NULL")

    if project_filter_parts:
        filters.append(f"({' OR '.join(project_filter_parts)})")

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    result = await db.execute(text(f"""
        SELECT
            id, name, code, perimetre_type as zone_type, level,
            parent_id, is_global, metadata, created_at,
            ST_AsGeoJSON(geom)::json as geometry
        FROM perimetres
        {where_clause}
        ORDER BY level, name
    """), params)

    features = []
    for row in result.fetchall():
        features.append(ZoneGeoJSON(
            type="Feature",
            id=str(row.id),
            properties={
                "name": row.name,
                "code": row.code,
                "zone_type": row.zone_type or "quartier",
                "level": row.level or 2,
                "parent_id": str(row.parent_id) if row.parent_id else None,
                "is_global": row.is_global or False,
                "metadata": row.metadata or {},
            },
            geometry=row.geometry,
        ))

    return ZonesGeoJSONCollection(type="FeatureCollection", features=features)


@router.post("/check-overlap", response_model=ZoneOverlapCheck)
async def check_overlap(
    geojson: dict,
    exclude_zone_id: Optional[str] = Query(None, description="ID de zone à exclure (pour édition)"),
    project_id: Optional[str] = Query(None, description="Vérifier dans un projet spécifique"),
    db: AsyncSession = Depends(get_db),
):
    """Vérifie si une géométrie chevauche des zones existantes."""

    geojson_str = json.dumps(geojson)

    params = {"geojson": geojson_str}
    filters = []

    if exclude_zone_id:
        filters.append("id != CAST(:exclude_id AS uuid)")
        params["exclude_id"] = exclude_zone_id

    if project_id:
        filters.append("(project_id = CAST(:project_id AS uuid) OR is_global = TRUE)")
        params["project_id"] = project_id

    where_extra = f"AND {' AND '.join(filters)}" if filters else ""

    result = await db.execute(text(f"""
        SELECT name FROM perimetres
        WHERE ST_Intersects(geom, ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326))
          AND NOT ST_Touches(geom, ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326))
          {where_extra}
    """), params)

    overlapping = [row.name for row in result.fetchall()]

    return ZoneOverlapCheck(
        has_overlap=len(overlapping) > 0,
        overlapping_zones=overlapping,
    )


@router.post("/import-iris", response_model=IRISImportResponse)
async def import_iris(
    request: IRISImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Importe une commune et ses zones IRIS depuis geo.api.gouv.fr.

    Crée:
    - La commune (level=1, parent_id=NULL)
    - Les IRIS comme quartiers (level=2, parent_id=commune)

    Pour les communes < 5000 habitants (sans IRIS), crée uniquement la commune.
    """
    if current_user.get("role") not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants")

    code_commune = request.code_commune
    project_id = request.project_id
    is_global = project_id is None
    errors = []
    imported = 0
    ignored = 0
    commune_id = None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Récupérer les infos de la commune avec son contour
            response = await client.get(
                f"https://geo.api.gouv.fr/communes/{code_commune}",
                params={"fields": "nom,population", "geometry": "contour", "format": "geojson"}
            )

            if response.status_code == 404:
                return IRISImportResponse(
                    success=False,
                    message=f"Commune {code_commune} non trouvée",
                    errors=["Code commune invalide"],
                )

            commune_data = response.json()
            commune_nom = commune_data.get("properties", {}).get("nom", f"Commune {code_commune}")
            commune_pop = commune_data.get("properties", {}).get("population")
            commune_geom = commune_data.get("geometry")

            # Supprimer les existants si demandé
            if request.remplacer_existants:
                await db.execute(text("""
                    DELETE FROM perimetres
                    WHERE code_insee = :code_insee
                       OR code = :code_commune
                       OR metadata->>'code_insee' = :code_insee
                """), {"code_insee": code_commune, "code_commune": code_commune})

            # 2. Créer la commune (level=1)
            if commune_geom:
                geojson_str = json.dumps(commune_geom)

                result = await db.execute(text("""
                    INSERT INTO perimetres (
                        name, code, perimetre_type, level, parent_id,
                        is_global, project_id, population, code_insee,
                        metadata, geom
                    )
                    VALUES (
                        :name, :code, 'commune', 1, NULL,
                        :is_global, CAST(:project_id AS uuid), :population, :code_insee,
                        :metadata,
                        ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326)
                    )
                    RETURNING id
                """), {
                    "name": commune_nom,
                    "code": code_commune,
                    "is_global": is_global,
                    "project_id": project_id,
                    "population": commune_pop,
                    "code_insee": code_commune,
                    "metadata": json.dumps({"source": "geo.api.gouv.fr", "type": "commune"}),
                    "geojson": geojson_str,
                })

                row = result.fetchone()
                if row:
                    commune_id = str(row.id)
                    imported += 1

            # 3. Récupérer et importer les IRIS
            iris_response = await client.get(
                f"https://geo.api.gouv.fr/communes/{code_commune}/iris",
                params={"format": "geojson"}
            )

            if iris_response.status_code != 200:
                # Commune sans IRIS (< 5000 hab)
                await db.commit()
                return IRISImportResponse(
                    success=True,
                    commune_id=commune_id,
                    zones_importees=imported,
                    message=f"Commune '{commune_nom}' importée (pas d'IRIS pour communes < 5000 hab)",
                )

            iris_data = iris_response.json()

            for feature in iris_data.get("features", []):
                try:
                    props = feature.get("properties", {})
                    geom = feature.get("geometry", {})

                    if geom.get("type") not in ["Polygon", "MultiPolygon"]:
                        ignored += 1
                        continue

                    iris_code = props.get("code", "")
                    iris_nom = props.get("nom", f"IRIS {iris_code}")
                    iris_type = props.get("type_iris", "")

                    geojson_str = json.dumps(geom)

                    await db.execute(text("""
                        INSERT INTO perimetres (
                            name, code, perimetre_type, level, parent_id,
                            is_global, project_id, code_iris, code_insee,
                            metadata, geom
                        )
                        VALUES (
                            :name, :code, 'iris', 2, CAST(:parent_id AS uuid),
                            :is_global, CAST(:project_id AS uuid), :code_iris, :code_insee,
                            :metadata,
                            ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326)
                        )
                    """), {
                        "name": iris_nom,
                        "code": iris_code,
                        "parent_id": commune_id,
                        "is_global": is_global,
                        "project_id": project_id,
                        "code_iris": iris_code,
                        "code_insee": code_commune,
                        "metadata": json.dumps({
                            "source": "geo.api.gouv.fr",
                            "type_iris": iris_type,
                            "commune": commune_nom,
                        }),
                        "geojson": geojson_str,
                    })

                    imported += 1

                except Exception as e:
                    errors.append(f"Erreur IRIS {props.get('code', '?')}: {str(e)}")
                    ignored += 1

            await db.commit()

            return IRISImportResponse(
                success=True,
                commune_id=commune_id,
                zones_importees=imported,
                zones_ignorees=ignored,
                errors=errors,
                message=f"Import terminé: {imported} zones importées (1 commune + {imported-1} IRIS)",
            )

    except httpx.TimeoutException:
        return IRISImportResponse(
            success=False,
            message="Timeout lors de la connexion à geo.api.gouv.fr",
            errors=["Service geo.api.gouv.fr non disponible"],
        )
    except Exception as e:
        await db.rollback()
        return IRISImportResponse(
            success=False,
            message=f"Erreur lors de l'import: {str(e)}",
            errors=[str(e)],
        )


# ═══════════════════════════════════════════════════════════════════════════════
# LISTE ET DÉTAILS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("", response_model=List[ZoneResponse])
async def list_zones(
    zone_type: Optional[str] = Query(None, description="Filtrer par type (quartier, secteur, commune)"),
    level: Optional[int] = Query(None, ge=1, le=3, description="Filtrer par niveau"),
    parent_id: Optional[str] = Query(None, description="Filtrer par zone parente"),
    project_id: Optional[str] = Query(None, description="Filtrer par projet"),
    include_global: bool = Query(True, description="Inclure les zones globales"),
    search: Optional[str] = Query(None, description="Recherche par nom"),
    db: AsyncSession = Depends(get_db),
):
    """Liste toutes les zones avec le nombre de points associés."""

    filters = []
    params = {}

    if zone_type:
        filters.append("p.perimetre_type = :zone_type")
        params["zone_type"] = zone_type

    if level is not None:
        filters.append("p.level = :level")
        params["level"] = level

    if parent_id:
        filters.append("p.parent_id = CAST(:parent_id AS uuid)")
        params["parent_id"] = parent_id

    if search:
        filters.append("p.name ILIKE :search")
        params["search"] = f"%{search}%"

    # Filtre projet + global
    project_filter_parts = []
    if project_id:
        project_filter_parts.append("p.project_id = CAST(:project_id AS uuid)")
        params["project_id"] = project_id
    if include_global:
        project_filter_parts.append("p.is_global = TRUE")
        project_filter_parts.append("p.project_id IS NULL")

    if project_filter_parts:
        filters.append(f"({' OR '.join(project_filter_parts)})")

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    result = await db.execute(text(f"""
        SELECT
            p.id, p.name, p.code, p.perimetre_type as zone_type,
            p.level, p.parent_id, p.is_global,
            CAST(p.project_id AS text) as project_id,
            p.metadata, p.created_at, p.updated_at,
            p.population, p.code_iris, p.code_insee,
            parent.name as parent_name,
            COALESCE(COUNT(g.id), 0) as point_count
        FROM perimetres p
        LEFT JOIN perimetres parent ON p.parent_id = parent.id
        LEFT JOIN geoclic_staging g ON ST_Contains(p.geom, g.geom)
        {where_clause}
        GROUP BY p.id, parent.name
        ORDER BY p.level, p.name
    """), params)

    return [
        ZoneResponse(
            id=str(row.id),
            name=row.name,
            code=row.code,
            zone_type=row.zone_type or "quartier",
            level=row.level or 2,
            parent_id=str(row.parent_id) if row.parent_id else None,
            parent_name=row.parent_name,
            is_global=row.is_global or False,
            project_id=row.project_id,
            metadata=row.metadata or {},
            created_at=row.created_at,
            updated_at=row.updated_at,
            point_count=row.point_count,
            population=row.population,
            code_iris=row.code_iris,
            code_insee=row.code_insee,
        )
        for row in result.fetchall()
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES AVEC PARAMÈTRES (APRÈS LES ROUTES STATIQUES)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{zone_id}", response_model=ZoneWithGeometry)
async def get_zone(
    zone_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Récupère une zone avec sa géométrie."""

    result = await db.execute(text("""
        SELECT
            p.id, p.name, p.code, p.perimetre_type as zone_type,
            p.level, p.parent_id, p.is_global,
            CAST(p.project_id AS text) as project_id,
            p.metadata, p.created_at, p.updated_at,
            p.population, p.code_iris, p.code_insee,
            parent.name as parent_name,
            ST_AsGeoJSON(p.geom)::json as geojson,
            ST_XMin(p.geom) as min_lng, ST_YMin(p.geom) as min_lat,
            ST_XMax(p.geom) as max_lng, ST_YMax(p.geom) as max_lat,
            COALESCE(COUNT(g.id), 0) as point_count
        FROM perimetres p
        LEFT JOIN perimetres parent ON p.parent_id = parent.id
        LEFT JOIN geoclic_staging g ON ST_Contains(p.geom, g.geom)
        WHERE p.id = CAST(:zone_id AS uuid)
        GROUP BY p.id, parent.name
    """), {"zone_id": zone_id})

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Zone non trouvée")

    return ZoneWithGeometry(
        id=str(row.id),
        name=row.name,
        code=row.code,
        zone_type=row.zone_type or "quartier",
        level=row.level or 2,
        parent_id=str(row.parent_id) if row.parent_id else None,
        parent_name=row.parent_name,
        is_global=row.is_global or False,
        project_id=row.project_id,
        metadata=row.metadata or {},
        created_at=row.created_at,
        updated_at=row.updated_at,
        point_count=row.point_count,
        population=row.population,
        code_iris=row.code_iris,
        code_insee=row.code_insee,
        geojson=row.geojson,
        bbox=[row.min_lng, row.min_lat, row.max_lng, row.max_lat] if row.min_lng else None,
    )


@router.get("/{zone_id}/children", response_model=List[ZoneResponse])
async def get_zone_children(
    zone_id: str,
    recursive: bool = Query(False, description="Inclure tous les descendants"),
    db: AsyncSession = Depends(get_db),
):
    """Récupère les zones enfants directes (ou tous les descendants si recursive=True)."""

    # Vérifier que la zone existe et récupérer son nom
    parent_result = await db.execute(text("""
        SELECT name FROM perimetres WHERE id = CAST(:zone_id AS uuid)
    """), {"zone_id": zone_id})

    parent_row = parent_result.fetchone()
    if not parent_row:
        raise HTTPException(status_code=404, detail="Zone parente non trouvée")

    if recursive:
        # Utiliser la fonction SQL récursive
        result = await db.execute(text("""
            SELECT
                p.id, p.name, p.code, p.perimetre_type as zone_type,
                p.level, p.parent_id, p.is_global,
                CAST(p.project_id AS text) as project_id,
                p.metadata, p.created_at, p.updated_at,
                p.population, p.code_iris, p.code_insee,
                parent.name as parent_name,
                0 as point_count
            FROM get_zone_children(CAST(:zone_id AS uuid), TRUE) c
            JOIN perimetres p ON p.id = c.zone_id
            LEFT JOIN perimetres parent ON p.parent_id = parent.id
            ORDER BY c.depth, p.name
        """), {"zone_id": zone_id})
    else:
        # Enfants directs seulement
        result = await db.execute(text("""
            SELECT
                p.id, p.name, p.code, p.perimetre_type as zone_type,
                p.level, p.parent_id, p.is_global,
                CAST(p.project_id AS text) as project_id,
                p.metadata, p.created_at, p.updated_at,
                p.population, p.code_iris, p.code_insee,
                parent.name as parent_name,
                COALESCE(COUNT(g.id), 0) as point_count
            FROM perimetres p
            LEFT JOIN perimetres parent ON p.parent_id = parent.id
            LEFT JOIN geoclic_staging g ON ST_Contains(p.geom, g.geom)
            WHERE p.parent_id = CAST(:zone_id AS uuid)
            GROUP BY p.id, parent.name
            ORDER BY p.name
        """), {"zone_id": zone_id})

    return [
        ZoneResponse(
            id=str(row.id),
            name=row.name,
            code=row.code,
            zone_type=row.zone_type or "quartier",
            level=row.level or 2,
            parent_id=str(row.parent_id) if row.parent_id else None,
            parent_name=row.parent_name,
            is_global=row.is_global or False,
            project_id=row.project_id,
            metadata=row.metadata or {},
            created_at=row.created_at,
            updated_at=row.updated_at,
            point_count=row.point_count,
            population=row.population,
            code_iris=row.code_iris,
            code_insee=row.code_insee,
        )
        for row in result.fetchall()
    ]


@router.get("/{zone_id}/stats", response_model=ZoneStatsResponse)
async def get_zone_stats(
    zone_id: str,
    include_children: bool = Query(False, description="Inclure les stats des zones enfants"),
    db: AsyncSession = Depends(get_db),
):
    """Récupère les statistiques des demandes pour une zone."""

    # Stats directes depuis la vue
    result = await db.execute(text("""
        SELECT * FROM v_stats_demandes_par_zone
        WHERE zone_id = CAST(:zone_id AS uuid)
    """), {"zone_id": zone_id})

    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Zone non trouvée")

    stats = ZoneStatsResponse(
        zone_id=str(row.zone_id),
        zone_name=row.zone_name,
        level=row.level or 2,
        zone_type=row.perimetre_type or "quartier",
        parent_id=str(row.parent_id) if row.parent_id else None,
        parent_name=row.parent_name,
        total_demandes=row.total_demandes or 0,
        nouvelles=row.nouvelles or 0,
        acceptees=row.acceptees or 0,
        en_cours=row.en_cours or 0,
        traitees=row.traitees or 0,
        rejetees=row.rejetees or 0,
        temps_moyen_heures=float(row.temps_moyen_heures) if row.temps_moyen_heures else None,
    )

    # Stats avec enfants si demandé
    if include_children:
        children_result = await db.execute(text("""
            WITH RECURSIVE descendants AS (
                SELECT id FROM perimetres WHERE id = CAST(:zone_id AS uuid)
                UNION ALL
                SELECT p.id FROM perimetres p
                JOIN descendants d ON p.parent_id = d.id
            )
            SELECT COALESCE(SUM(
                (SELECT COUNT(*) FROM demandes_citoyens WHERE quartier_id = d.id)
            ), 0) as total
            FROM descendants d
        """), {"zone_id": zone_id})

        total_row = children_result.fetchone()
        stats.total_avec_enfants = total_row.total if total_row else stats.total_demandes

    return stats


# ═══════════════════════════════════════════════════════════════════════════════
# CRÉATION ET MODIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("", response_model=ZoneWithGeometry)
async def create_zone(
    zone: ZoneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Crée une nouvelle zone avec sa géométrie GeoJSON."""

    if current_user.get("role") not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants")

    # Vérifier le format GeoJSON
    geom_type = zone.geojson.get("type")
    if geom_type not in ["Polygon", "MultiPolygon"]:
        raise HTTPException(
            status_code=400,
            detail=f"Type de géométrie invalide: {geom_type}. Attendu: Polygon ou MultiPolygon"
        )

    # Déterminer is_global
    is_global = zone.is_global if zone.is_global is not None else (zone.project_id is None)

    # Déterminer le level si non spécifié
    level = zone.level
    if level is None:
        level = {
            "commune": 1,
            "quartier": 2,
            "iris": 2,
            "secteur": 3,
            "zone_travaux": 3,
        }.get(zone.zone_type, 2)

    geojson_str = json.dumps(zone.geojson)

    result = await db.execute(text("""
        INSERT INTO perimetres (
            name, code, perimetre_type, level, parent_id,
            is_global, project_id, population, code_iris, code_insee,
            metadata, geom
        )
        VALUES (
            :name, :code, :zone_type, :level, CAST(:parent_id AS uuid),
            :is_global, CAST(:project_id AS uuid), :population, :code_iris, :code_insee,
            :metadata,
            ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326)
        )
        RETURNING id
    """), {
        "name": zone.name,
        "code": zone.code,
        "zone_type": zone.zone_type or "quartier",
        "level": level,
        "parent_id": zone.parent_id,
        "is_global": is_global,
        "project_id": zone.project_id,
        "population": zone.population,
        "code_iris": zone.code_iris,
        "code_insee": zone.code_insee,
        "metadata": json.dumps(zone.metadata) if zone.metadata else "{}",
        "geojson": geojson_str,
    })

    row = result.fetchone()
    await db.commit()

    return await get_zone(str(row.id), db)


@router.put("/{zone_id}", response_model=ZoneWithGeometry)
async def update_zone(
    zone_id: str,
    zone: ZoneUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Met à jour une zone existante."""

    if current_user.get("role") not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants")

    # Vérifier que la zone existe
    existing = await db.execute(
        text("SELECT id FROM perimetres WHERE id = CAST(:zone_id AS uuid)"),
        {"zone_id": zone_id}
    )
    if not existing.fetchone():
        raise HTTPException(status_code=404, detail="Zone non trouvée")

    # Construire la requête de mise à jour
    updates = []
    params = {"zone_id": zone_id}

    if zone.name is not None:
        updates.append("name = :name")
        params["name"] = zone.name

    if zone.code is not None:
        updates.append("code = :code")
        params["code"] = zone.code

    if zone.zone_type is not None:
        updates.append("perimetre_type = :zone_type")
        params["zone_type"] = zone.zone_type

    if zone.level is not None:
        updates.append("level = :level")
        params["level"] = zone.level

    if zone.parent_id is not None:
        updates.append("parent_id = CAST(:parent_id AS uuid)")
        params["parent_id"] = zone.parent_id if zone.parent_id != "" else None

    if zone.is_global is not None:
        updates.append("is_global = :is_global")
        params["is_global"] = zone.is_global

    if zone.project_id is not None:
        updates.append("project_id = CAST(:project_id AS uuid)")
        params["project_id"] = zone.project_id if zone.project_id != "" else None

    if zone.population is not None:
        updates.append("population = :population")
        params["population"] = zone.population

    if zone.code_iris is not None:
        updates.append("code_iris = :code_iris")
        params["code_iris"] = zone.code_iris

    if zone.code_insee is not None:
        updates.append("code_insee = :code_insee")
        params["code_insee"] = zone.code_insee

    if zone.metadata is not None:
        updates.append("metadata = :metadata")
        params["metadata"] = json.dumps(zone.metadata)

    if zone.geojson is not None:
        updates.append("geom = ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326)")
        params["geojson"] = json.dumps(zone.geojson)

    if updates:
        # Sécurité : vérifier que les noms de colonnes sont dans la whitelist
        ALLOWED_UPDATE_COLS = {
            "name", "code", "perimetre_type", "level", "parent_id",
            "is_global", "project_id", "population", "code_iris", "code_insee",
            "metadata", "geom", "updated_at",
        }
        for u in updates:
            col_name = u.split("=")[0].strip().split("(")[0].strip()
            if col_name not in ALLOWED_UPDATE_COLS:
                raise HTTPException(status_code=400, detail=f"Colonne non autorisée: {col_name}")

        updates.append("updated_at = CURRENT_TIMESTAMP")
        await db.execute(
            text(f"UPDATE perimetres SET {', '.join(updates)} WHERE id = CAST(:zone_id AS uuid)"),
            params
        )
        await db.commit()

    return await get_zone(zone_id, db)


@router.delete("/{zone_id}")
async def delete_zone(
    zone_id: str,
    force: bool = Query(False, description="Supprimer même si la zone a des enfants"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Supprime une zone."""

    if current_user.get("role") not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Droits insuffisants")

    # Vérifier si la zone a des enfants
    children_result = await db.execute(text("""
        SELECT COUNT(*) as count FROM perimetres
        WHERE parent_id = CAST(:zone_id AS uuid)
    """), {"zone_id": zone_id})

    children_count = children_result.fetchone().count

    if children_count > 0 and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Cette zone a {children_count} zone(s) enfant(s). Utilisez force=true pour supprimer quand même."
        )

    # Supprimer les enfants d'abord si force=true
    if force and children_count > 0:
        await db.execute(text("""
            WITH RECURSIVE descendants AS (
                SELECT id FROM perimetres WHERE parent_id = CAST(:zone_id AS uuid)
                UNION ALL
                SELECT p.id FROM perimetres p
                JOIN descendants d ON p.parent_id = d.id
            )
            DELETE FROM perimetres WHERE id IN (SELECT id FROM descendants)
        """), {"zone_id": zone_id})

    # Supprimer la zone
    result = await db.execute(
        text("DELETE FROM perimetres WHERE id = CAST(:zone_id AS uuid) RETURNING id"),
        {"zone_id": zone_id}
    )

    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Zone non trouvée")

    await db.commit()

    deleted_count = 1 + (children_count if force else 0)
    return {"message": f"Zone supprimée ({deleted_count} zone(s) au total)"}
