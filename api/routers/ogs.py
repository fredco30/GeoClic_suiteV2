"""
Router pour l'intégration OneGeo Suite (OGS).
Publication des données validées vers les tables PostGIS OGS.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import re

from database import get_db
from routers.auth import get_current_user

router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class OGSTableInfo(BaseModel):
    """Information sur une table OGS."""
    table_name: str
    lexique_code: str
    lexique_label: str
    point_count: int
    last_publication: Optional[datetime] = None
    exists: bool = False


class OGSPublishRequest(BaseModel):
    """Requête de publication vers OGS."""
    lexique_code: str
    include_children: bool = True  # Inclure les sous-catégories


class OGSPublishResponse(BaseModel):
    """Réponse de publication vers OGS."""
    success: bool
    table_name: str
    points_published: int
    points_updated: int
    message: str


class OGSStatusResponse(BaseModel):
    """Statut global de l'intégration OGS."""
    total_ogs_tables: int
    total_points_published: int
    tables: List[OGSTableInfo]
    pending_validation: int  # Points en attente de validation


# ============================================================================
# HELPERS
# ============================================================================

def sanitize_table_name(code: str) -> str:
    """Convertit un code lexique en nom de table SQL valide."""
    # Préfixe ogs_, minuscules, remplacer caractères spéciaux
    name = code.lower()
    name = re.sub(r'[^a-z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)  # Éviter les underscores multiples
    name = name.strip('_')
    result = f"ogs_{name}"
    # Double vérification de sécurité
    if not re.match(r'^ogs_[a-z0-9_]+$', result):
        raise HTTPException(status_code=400, detail=f"Code lexique invalide: {code}")
    return result


def validate_ogs_table_name(table_name: str) -> str:
    """Valide qu'un nom de table OGS est sûr pour utilisation SQL."""
    if not table_name.startswith("ogs_"):
        raise HTTPException(status_code=400, detail="Seules les tables OGS (préfixe ogs_) sont autorisées")
    if not re.match(r'^ogs_[a-z0-9_]+$', table_name):
        raise HTTPException(status_code=400, detail=f"Nom de table invalide: {table_name}")
    if len(table_name) > 128:
        raise HTTPException(status_code=400, detail="Nom de table trop long")
    return table_name


def get_pg_type(champ_type: str) -> str:
    """Convertit un type de champ GéoClic en type PostgreSQL."""
    type_mapping = {
        "text": "TEXT",
        "number": "NUMERIC",
        "date": "DATE",
        "select": "TEXT",
        "multiselect": "TEXT[]",
        "photo": "JSONB",
        "file": "JSONB",
        "geometry": "GEOMETRY",
        "slider": "NUMERIC",
        "color": "TEXT",
        "signature": "TEXT",
        "qrcode": "TEXT",
        "calculated": "NUMERIC",
    }
    return type_mapping.get(champ_type, "TEXT")


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/status", response_model=OGSStatusResponse)
async def get_ogs_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère le statut global de l'intégration OGS."""
    # Lister les tables OGS existantes
    tables_result = await db.execute(
        text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'ogs_%'
        """)
    )
    existing_tables = {row[0] for row in tables_result.fetchall()}

    # Récupérer les catégories de niveau 0 (racines) avec leurs stats
    lexique_result = await db.execute(
        text("""
            SELECT
                l.code,
                l.label,
                COUNT(DISTINCT p.id) as point_count,
                MAX(p.updated_at) as last_update
            FROM lexique l
            LEFT JOIN geoclic_staging p ON (
                p.lexique_code = l.code
                OR p.lexique_code LIKE l.code || '%'
            ) AND p.sync_status = 'validated'
            WHERE l.is_active = TRUE AND l.level = 0
            GROUP BY l.code, l.label
            ORDER BY l.label
        """)
    )
    lexique_rows = lexique_result.mappings().all()

    tables = []
    total_published = 0

    for row in lexique_rows:
        table_name = sanitize_table_name(row["code"])
        exists = table_name in existing_tables

        # Compter les points dans la table OGS si elle existe
        published_count = 0
        if exists:
            try:
                count_result = await db.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                )
                published_count = count_result.scalar() or 0
                total_published += published_count
            except:
                pass

        tables.append(OGSTableInfo(
            table_name=table_name,
            lexique_code=row["code"],
            lexique_label=row["label"],
            point_count=row["point_count"] or 0,
            last_publication=row["last_update"],
            exists=exists,
        ))

    # Points en attente de validation
    pending_result = await db.execute(
        text("SELECT COUNT(*) FROM geoclic_staging WHERE sync_status = 'pending'")
    )
    pending_count = pending_result.scalar() or 0

    return OGSStatusResponse(
        total_ogs_tables=len(existing_tables),
        total_points_published=total_published,
        tables=tables,
        pending_validation=pending_count,
    )


@router.post("/publish", response_model=OGSPublishResponse)
async def publish_to_ogs(
    request: OGSPublishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Publie les points validés vers une table OneGeo Suite.
    Crée la table automatiquement si elle n'existe pas.
    """
    # Vérifier les permissions (admin ou moderator)
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs peuvent publier vers OGS"
        )

    lexique_code = request.lexique_code
    table_name = sanitize_table_name(lexique_code)

    # Vérifier que la catégorie existe
    lexique_result = await db.execute(
        text("SELECT code, label FROM lexique WHERE code = :code"),
        {"code": lexique_code}
    )
    lexique_row = lexique_result.first()
    if not lexique_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catégorie '{lexique_code}' non trouvée"
        )

    # Récupérer les champs dynamiques pour cette catégorie
    champs_result = await db.execute(
        text("""
            SELECT nom, type FROM champs_dynamiques
            WHERE lexique_code = :code AND actif = TRUE
            ORDER BY ordre
        """),
        {"code": lexique_code}
    )
    champs = champs_result.mappings().all()

    # Construire la condition WHERE pour les points
    if request.include_children:
        where_condition = "lexique_code = :code OR lexique_code LIKE :code_pattern"
        params = {"code": lexique_code, "code_pattern": f"{lexique_code}_%"}
    else:
        where_condition = "lexique_code = :code"
        params = {"code": lexique_code}

    # Vérifier s'il y a des points validés à publier
    count_result = await db.execute(
        text(f"""
            SELECT COUNT(*) FROM geoclic_staging
            WHERE ({where_condition}) AND sync_status = 'validated'
        """),
        params
    )
    points_count = count_result.scalar() or 0

    if points_count == 0:
        return OGSPublishResponse(
            success=True,
            table_name=table_name,
            points_published=0,
            points_updated=0,
            message="Aucun point validé à publier pour cette catégorie"
        )

    # Vérifier si la table existe
    table_exists_result = await db.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = :table_name
            )
        """),
        {"table_name": table_name}
    )
    table_exists = table_exists_result.scalar()

    # Créer la table si elle n'existe pas
    if not table_exists:
        # Colonnes de base
        columns = [
            "id UUID PRIMARY KEY",
            "geoclic_id UUID UNIQUE NOT NULL",
            "nom TEXT",
            "lexique_code TEXT",
            "geom GEOMETRY(POINT, 4326)",
            "condition_state TEXT",
            "point_status TEXT",
            "commentaire TEXT",
            "photos JSONB",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "published_by UUID",
        ]

        # Ajouter les champs dynamiques
        for champ in champs:
            pg_type = get_pg_type(champ["type"])
            col_name = re.sub(r'[^a-z0-9_]', '_', champ["nom"].lower())
            columns.append(f"{col_name} {pg_type}")

        create_sql = f"""
            CREATE TABLE {table_name} (
                {', '.join(columns)}
            )
        """
        await db.execute(text(create_sql))

        # Créer un index spatial
        await db.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_geom
            ON {table_name} USING GIST (geom)
        """))

    # Récupérer les points validés
    points_result = await db.execute(
        text(f"""
            SELECT
                id, name, lexique_code, geom, condition_state, point_status,
                comment, photos, custom_properties, created_at, updated_at
            FROM geoclic_staging
            WHERE ({where_condition}) AND sync_status = 'validated'
        """),
        params
    )
    points = points_result.mappings().all()

    points_published = 0
    points_updated = 0

    for point in points:
        # Vérifier si le point existe déjà dans la table OGS
        existing_result = await db.execute(
            text(f"SELECT id FROM {table_name} WHERE geoclic_id = :geoclic_id"),
            {"geoclic_id": str(point["id"])}
        )
        existing = existing_result.first()

        # Préparer les valeurs des champs dynamiques
        custom_props = point.get("custom_properties") or {}
        dynamic_columns = []
        dynamic_values = []
        dynamic_params = {}

        for i, champ in enumerate(champs):
            col_name = re.sub(r'[^a-z0-9_]', '_', champ["nom"].lower())
            param_name = f"dyn_{i}"
            dynamic_columns.append(col_name)
            dynamic_values.append(f":{param_name}")
            dynamic_params[param_name] = custom_props.get(champ["nom"])

        if existing:
            # Mise à jour
            set_clauses = [
                "nom = :nom",
                "lexique_code = :lexique_code",
                "geom = :geom",
                "condition_state = :condition_state",
                "point_status = :point_status",
                "commentaire = :commentaire",
                "photos = :photos",
                "updated_at = :updated_at",
                "published_at = CURRENT_TIMESTAMP",
                "published_by = :published_by",
            ]
            for i, col in enumerate(dynamic_columns):
                set_clauses.append(f"{col} = :dyn_{i}")

            update_sql = f"""
                UPDATE {table_name}
                SET {', '.join(set_clauses)}
                WHERE geoclic_id = :geoclic_id
            """
            await db.execute(
                text(update_sql),
                {
                    "geoclic_id": str(point["id"]),
                    "nom": point["name"],
                    "lexique_code": point["lexique_code"],
                    "geom": point["geom"],
                    "condition_state": point["condition_state"],
                    "point_status": point["point_status"],
                    "commentaire": point["comment"],
                    "photos": point["photos"],
                    "updated_at": point["updated_at"],
                    "published_by": str(current_user["id"]),
                    **dynamic_params,
                }
            )
            points_updated += 1
        else:
            # Insertion
            base_columns = [
                "id", "geoclic_id", "nom", "lexique_code", "geom",
                "condition_state", "point_status", "commentaire", "photos",
                "created_at", "updated_at", "published_by"
            ]
            base_values = [
                "gen_random_uuid()", ":geoclic_id", ":nom", ":lexique_code", ":geom",
                ":condition_state", ":point_status", ":commentaire", ":photos",
                ":created_at", ":updated_at", ":published_by"
            ]

            all_columns = base_columns + dynamic_columns
            all_values = base_values + dynamic_values

            insert_sql = f"""
                INSERT INTO {table_name} ({', '.join(all_columns)})
                VALUES ({', '.join(all_values)})
            """
            await db.execute(
                text(insert_sql),
                {
                    "geoclic_id": str(point["id"]),
                    "nom": point["name"],
                    "lexique_code": point["lexique_code"],
                    "geom": point["geom"],
                    "condition_state": point["condition_state"],
                    "point_status": point["point_status"],
                    "commentaire": point["comment"],
                    "photos": point["photos"],
                    "created_at": point["created_at"],
                    "updated_at": point["updated_at"],
                    "published_by": str(current_user["id"]),
                    **dynamic_params,
                }
            )
            points_published += 1

    # Mettre à jour le statut des points publiés
    await db.execute(
        text(f"""
            UPDATE geoclic_staging
            SET sync_status = 'synced',
                ogs_published_at = CURRENT_TIMESTAMP,
                ogs_table_name = :table_name
            WHERE ({where_condition}) AND sync_status = 'validated'
        """),
        {**params, "table_name": table_name}
    )

    await db.commit()

    return OGSPublishResponse(
        success=True,
        table_name=table_name,
        points_published=points_published,
        points_updated=points_updated,
        message=f"Publication réussie vers {table_name}: {points_published} nouveaux, {points_updated} mis à jour"
    )


@router.get("/tables")
async def list_ogs_tables(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Liste toutes les tables OGS existantes avec leurs statistiques."""
    result = await db.execute(
        text("""
            SELECT
                t.table_name,
                (SELECT COUNT(*) FROM information_schema.columns c
                 WHERE c.table_name = t.table_name AND c.table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE t.table_schema = 'public'
            AND t.table_name LIKE 'ogs_%'
            ORDER BY t.table_name
        """)
    )
    tables = []

    for row in result.fetchall():
        table_name = row[0]
        try:
            safe_name = validate_ogs_table_name(table_name)
            count_result = await db.execute(text(f"SELECT COUNT(*) FROM {safe_name}"))
            point_count = count_result.scalar() or 0
        except HTTPException:
            point_count = 0
        except Exception:
            point_count = 0

        tables.append({
            "name": table_name,
            "columns": row[1],
            "point_count": point_count,
        })

    return {"tables": tables}


@router.delete("/tables/{table_name}")
async def delete_ogs_table(
    table_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Supprime une table OGS (admin uniquement)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    # Valider et sécuriser le nom de table (empêche injection SQL)
    safe_name = validate_ogs_table_name(table_name)

    # Vérifier que la table existe
    exists_result = await db.execute(
        text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = :name
            )
        """),
        {"name": safe_name}
    )
    if not exists_result.scalar():
        raise HTTPException(status_code=404, detail="Table non trouvée")

    # Supprimer la table
    await db.execute(text(f"DROP TABLE IF EXISTS {safe_name}"))
    await db.commit()

    return {"success": True, "message": f"Table {safe_name} supprimée"}
