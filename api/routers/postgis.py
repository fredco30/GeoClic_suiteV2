"""
Router pour la gestion des connexions PostGIS externes.
Permet d'importer des données depuis des bases PostGIS existantes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import json
import re
import asyncpg

from database import get_db
from routers.auth import get_current_user

router = APIRouter()


# ============================================================================
# SÉCURITÉ - Validation des identifiants SQL
# ============================================================================

def validate_sql_identifier(name: str, label: str = "identifiant") -> str:
    """
    Valide qu'un nom de table/schema/colonne ne contient que des caractères sûrs.
    Empêche les injections SQL via les noms de table/schema.
    """
    if not name or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise HTTPException(
            status_code=400,
            detail=f"{label} invalide: '{name}'. Seuls les caractères alphanumériques et underscores sont autorisés."
        )
    if len(name) > 128:
        raise HTTPException(status_code=400, detail=f"{label} trop long (max 128 caractères)")
    return name


# ============================================================================
# SCHEMAS
# ============================================================================

class PostGISConnectionConfig(BaseModel):
    """Configuration de connexion PostGIS."""
    host: str
    port: int = 5432
    database: str
    username: str
    password: str
    schema_name: str = "public"


class PostGISConnectionStatus(BaseModel):
    """Statut de la connexion PostGIS."""
    configured: bool
    host: Optional[str] = None
    database: Optional[str] = None
    schema_name: Optional[str] = None
    last_test: Optional[str] = None
    last_test_success: Optional[bool] = None


class PostGISTable(BaseModel):
    """Information sur une table PostGIS."""
    table_name: str
    schema_name: str
    geometry_column: Optional[str] = None
    geometry_type: Optional[str] = None
    srid: Optional[int] = None
    row_count: int = 0


class PostGISColumn(BaseModel):
    """Information sur une colonne."""
    column_name: str
    data_type: str
    is_nullable: bool
    is_geometry: bool = False


class PostGISImportFilter(BaseModel):
    """Filtre sécurisé pour l'import PostGIS (remplace where_clause brut)."""
    column: str
    operator: str  # =, !=, >, <, >=, <=, LIKE, IS NULL, IS NOT NULL
    value: Optional[str] = None


class PostGISImportRequest(BaseModel):
    """Requête d'import depuis PostGIS."""
    table_name: str
    schema_name: str = "public"
    project_id: str
    lexique_code: str
    mapping: Dict[str, str]  # source_column -> target_field
    filters: Optional[List[PostGISImportFilter]] = None  # Filtres sécurisés (remplace where_clause)
    limit: Optional[int] = None


class PostGISImportResult(BaseModel):
    """Résultat de l'import PostGIS."""
    success: bool
    imported: int
    skipped: int
    errors: int
    error_details: List[str] = []


# ============================================================================
# HELPERS
# ============================================================================

async def get_postgis_config(db: AsyncSession) -> Optional[Dict[str, Any]]:
    """Récupère la configuration PostGIS depuis la base."""
    result = await db.execute(
        text("""
            SELECT config_value FROM system_settings
            WHERE config_key = 'postgis_connection'
        """)
    )
    row = result.first()
    if row and row[0]:
        return json.loads(row[0])
    return None


async def save_postgis_config(db: AsyncSession, config: Dict[str, Any]) -> None:
    """Sauvegarde la configuration PostGIS (mot de passe chiffré)."""
    # Upsert la configuration
    await db.execute(
        text("""
            INSERT INTO system_settings (config_key, config_value, updated_at)
            VALUES ('postgis_connection', :config, NOW())
            ON CONFLICT (config_key) DO UPDATE
            SET config_value = :config, updated_at = NOW()
        """),
        {"config": json.dumps(config)}
    )
    await db.commit()


async def get_postgis_connection(config: Dict[str, Any]) -> asyncpg.Connection:
    """Crée une connexion asyncpg vers la base PostGIS externe."""
    return await asyncpg.connect(
        host=config["host"],
        port=config["port"],
        database=config["database"],
        user=config["username"],
        password=config["password"],
    )


# ============================================================================
# ENDPOINTS - CONFIGURATION
# ============================================================================

@router.get("/config/status", response_model=PostGISConnectionStatus)
async def get_connection_status(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Récupère le statut de la connexion PostGIS.
    Accessible à tous les utilisateurs (pour savoir si l'import PostGIS est disponible).
    """
    try:
        config = await get_postgis_config(db)
    except Exception as e:
        # Table system_settings n'existe peut-être pas encore
        print(f"Erreur récupération config PostGIS: {e}")
        return PostGISConnectionStatus(configured=False)

    if not config:
        return PostGISConnectionStatus(configured=False)

    return PostGISConnectionStatus(
        configured=True,
        host=config.get("host"),
        database=config.get("database"),
        schema_name=config.get("schema_name", "public"),
        last_test=config.get("last_test"),
        last_test_success=config.get("last_test_success"),
    )


@router.post("/config")
async def configure_connection(
    config: PostGISConnectionConfig,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Configure la connexion PostGIS externe.
    Réservé aux administrateurs (IT).
    """
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")

    # Tester la connexion avant de sauvegarder
    try:
        conn = await get_postgis_connection(config.model_dump())
        await conn.execute("SELECT 1")
        await conn.close()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de se connecter: {str(e)}"
        )

    # Sauvegarder la configuration
    config_dict = config.model_dump()
    config_dict["last_test"] = None
    config_dict["last_test_success"] = None

    await save_postgis_config(db, config_dict)

    return {"message": "Configuration PostGIS enregistrée avec succès"}


@router.post("/config/test")
async def test_connection(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Teste la connexion PostGIS configurée.
    """
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    config = await get_postgis_config(db)
    if not config:
        raise HTTPException(status_code=400, detail="Connexion PostGIS non configurée")

    try:
        conn = await get_postgis_connection(config)

        # Vérifier PostGIS
        result = await conn.fetchval("SELECT PostGIS_Version()")
        await conn.close()

        # Mettre à jour le statut
        from datetime import datetime
        config["last_test"] = datetime.now().isoformat()
        config["last_test_success"] = True
        await save_postgis_config(db, config)

        return {
            "success": True,
            "postgis_version": result,
            "message": "Connexion réussie"
        }

    except Exception as e:
        # Mettre à jour le statut d'échec
        from datetime import datetime
        config["last_test"] = datetime.now().isoformat()
        config["last_test_success"] = False
        await save_postgis_config(db, config)

        raise HTTPException(status_code=400, detail=f"Échec de connexion: {str(e)}")


@router.delete("/config")
async def delete_connection(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Supprime la configuration PostGIS.
    Réservé aux administrateurs.
    """
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")

    await db.execute(
        text("DELETE FROM system_settings WHERE config_key = 'postgis_connection'")
    )
    await db.commit()

    return {"message": "Configuration PostGIS supprimée"}


# ============================================================================
# ENDPOINTS - EXPLORATION
# ============================================================================

@router.get("/tables", response_model=List[PostGISTable])
async def list_tables(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Liste les tables géographiques disponibles dans la base PostGIS externe.
    """
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    config = await get_postgis_config(db)
    if not config:
        raise HTTPException(status_code=400, detail="Connexion PostGIS non configurée")

    try:
        conn = await get_postgis_connection(config)
        schema_name = config.get("schema_name", "public")

        # Récupérer les tables avec géométrie
        tables = await conn.fetch("""
            SELECT
                f_table_name as table_name,
                f_table_schema as schema_name,
                f_geometry_column as geometry_column,
                type as geometry_type,
                srid
            FROM geometry_columns
            WHERE f_table_schema = $1
            ORDER BY f_table_name
        """, schema_name)

        result = []
        for table in tables:
            # Compter les lignes (noms validés via geometry_columns, donc sûrs)
            tbl_name = table["table_name"]
            try:
                count = await conn.fetchval(
                    f'SELECT COUNT(*) FROM "{schema_name}"."{tbl_name}"'
                )
            except Exception:
                count = 0

            result.append(PostGISTable(
                table_name=table["table_name"],
                schema_name=table["schema_name"],
                geometry_column=table["geometry_column"],
                geometry_type=table["geometry_type"],
                srid=table["srid"],
                row_count=count or 0,
            ))

        await conn.close()
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.get("/tables/{table_name}/columns", response_model=List[PostGISColumn])
async def get_table_columns(
    table_name: str,
    schema_name: str = "public",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Récupère les colonnes d'une table PostGIS.
    """
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    config = await get_postgis_config(db)
    if not config:
        raise HTTPException(status_code=400, detail="Connexion PostGIS non configurée")

    try:
        conn = await get_postgis_connection(config)

        # Récupérer les colonnes
        columns = await conn.fetch("""
            SELECT
                column_name,
                data_type,
                is_nullable = 'YES' as is_nullable,
                udt_name
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """, schema_name, table_name)

        await conn.close()

        return [
            PostGISColumn(
                column_name=col["column_name"],
                data_type=col["data_type"],
                is_nullable=col["is_nullable"],
                is_geometry=col["udt_name"] == "geometry",
            )
            for col in columns
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.get("/tables/{table_name}/preview")
async def preview_table_data(
    table_name: str,
    schema_name: str = "public",
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Aperçu des données d'une table PostGIS (10 premières lignes).
    """
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    config = await get_postgis_config(db)
    if not config:
        raise HTTPException(status_code=400, detail="Connexion PostGIS non configurée")

    # Valider les identifiants SQL pour empêcher les injections
    schema_name = validate_sql_identifier(schema_name, "Nom de schéma")
    table_name = validate_sql_identifier(table_name, "Nom de table")

    # Limiter le nombre de lignes pour éviter les abus
    limit = max(1, min(limit, 100))

    try:
        conn = await get_postgis_connection(config)

        # Récupérer le nom de la colonne géométrie (via requête paramétrée)
        geom_col = await conn.fetchval("""
            SELECT f_geometry_column FROM geometry_columns
            WHERE f_table_schema = $1 AND f_table_name = $2
            LIMIT 1
        """, schema_name, table_name)

        # Valider le nom de colonne géométrie s'il existe
        if geom_col:
            geom_col = validate_sql_identifier(geom_col, "Colonne géométrie")

        # Construire la requête avec conversion de la géométrie en lat/lng
        # Les identifiants sont validés ci-dessus, le limit est un int contrôlé
        if geom_col:
            query = f"""
                SELECT *,
                    ST_X(ST_Centroid("{geom_col}")) as _longitude,
                    ST_Y(ST_Centroid("{geom_col}")) as _latitude
                FROM "{schema_name}"."{table_name}"
                LIMIT {limit}
            """
        else:
            query = f'SELECT * FROM "{schema_name}"."{table_name}" LIMIT {limit}'

        rows = await conn.fetch(query)
        await conn.close()

        # Convertir en dict et exclure la colonne géométrie binaire
        result = []
        for row in rows:
            row_dict = dict(row)
            if geom_col and geom_col in row_dict:
                del row_dict[geom_col]  # Exclure la géométrie brute
            result.append(row_dict)

        return {
            "columns": list(result[0].keys()) if result else [],
            "data": result,
            "geometry_column": geom_col,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


# ============================================================================
# ENDPOINTS - IMPORT
# ============================================================================

@router.post("/import", response_model=PostGISImportResult)
async def import_from_postgis(
    request: PostGISImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Importe des données depuis une table PostGIS externe vers GéoClic.
    """
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    config = await get_postgis_config(db)
    if not config:
        raise HTTPException(status_code=400, detail="Connexion PostGIS non configurée")

    # Vérifier que le mapping contient latitude/longitude ou une colonne géométrie
    lat_col = None
    lng_col = None
    geom_col = None

    for src, tgt in request.mapping.items():
        if tgt == "latitude":
            lat_col = src
        elif tgt == "longitude":
            lng_col = src
        elif tgt == "geometry":
            geom_col = src

    if not geom_col and (not lat_col or not lng_col):
        raise HTTPException(
            status_code=400,
            detail="Le mapping doit inclure soit une colonne géométrie, soit latitude et longitude"
        )

    try:
        conn = await get_postgis_connection(config)

        # Valider les identifiants SQL
        safe_schema = validate_sql_identifier(request.schema_name, "Nom de schéma")
        safe_table = validate_sql_identifier(request.table_name, "Nom de table")

        # Construire la requête SELECT avec colonnes validées
        select_cols = list(request.mapping.keys())
        for col in select_cols:
            validate_sql_identifier(col, "Nom de colonne source")

        # Si on utilise une colonne géométrie, extraire lat/lng
        if geom_col:
            validate_sql_identifier(geom_col, "Colonne géométrie")
            select_clause = ", ".join([
                f'"{col}"' if col != geom_col else
                f'ST_X(ST_Centroid("{geom_col}")) as _longitude, ST_Y(ST_Centroid("{geom_col}")) as _latitude'
                for col in select_cols
            ])
        else:
            select_clause = ", ".join([f'"{col}"' for col in select_cols])

        query = f'SELECT {select_clause} FROM "{safe_schema}"."{safe_table}"'

        # Construire les filtres sécurisés (remplace where_clause brut)
        ALLOWED_OPERATORS = {"=", "!=", ">", "<", ">=", "<=", "LIKE", "IS NULL", "IS NOT NULL"}
        query_params = []
        if request.filters:
            where_parts = []
            for i, f in enumerate(request.filters):
                validate_sql_identifier(f.column, "Colonne de filtre")
                op = f.operator.upper().strip()
                if op not in ALLOWED_OPERATORS:
                    raise HTTPException(400, f"Opérateur non autorisé: {f.operator}")
                if op in ("IS NULL", "IS NOT NULL"):
                    where_parts.append(f'"{f.column}" {op}')
                else:
                    where_parts.append(f'"{f.column}" {op} ${len(query_params) + 1}')
                    query_params.append(f.value)
            if where_parts:
                query += " WHERE " + " AND ".join(where_parts)

        if request.limit:
            safe_limit = max(1, min(request.limit, 10000))
            query += f" LIMIT {safe_limit}"

        rows = await conn.fetch(query, *query_params)
        await conn.close()

        # Importer les données
        import uuid

        imported = 0
        skipped = 0
        errors = 0
        error_details = []

        # Helper pour extraire une valeur mappée
        def get_mapped(target: str, row_dict: dict, default=None):
            col = next((s for s, t in request.mapping.items() if t == target), None)
            return row_dict.get(col, default) if col else default

        for i, row in enumerate(rows):
            try:
                row_dict = dict(row)

                # Extraire les coordonnées
                if geom_col:
                    lat = row_dict.get("_latitude")
                    lng = row_dict.get("_longitude")
                else:
                    lat = float(row_dict.get(lat_col, 0))
                    lng = float(row_dict.get(lng_col, 0))

                if not lat or not lng:
                    errors += 1
                    error_details.append(f"Ligne {i+1}: Coordonnées invalides")
                    continue

                # Extraire tous les champs mappés
                original_id = get_mapped("id", row_dict)
                name = get_mapped("nom", row_dict, f"Import PostGIS {i+1}")
                point_type = get_mapped("type", row_dict)
                subtype = get_mapped("subtype", row_dict)
                mapped_lexique = get_mapped("lexique_code", row_dict)
                condition_state = get_mapped("condition_state", row_dict)
                point_status = get_mapped("point_status", row_dict)
                materiau = get_mapped("materiau", row_dict)
                hauteur = get_mapped("hauteur", row_dict)
                largeur = get_mapped("largeur", row_dict)
                date_installation = get_mapped("date_installation", row_dict)
                priorite = get_mapped("priorite", row_dict)
                cout_remplacement = get_mapped("cout_remplacement", row_dict)
                zone_name = get_mapped("zone_name", row_dict)
                altitude = get_mapped("altitude", row_dict)
                gps_precision = get_mapped("gps_precision", row_dict)
                gps_source = get_mapped("gps_source", row_dict)
                comment = get_mapped("comment", row_dict, "")
                color_value = get_mapped("color_value", row_dict)
                icon_name = get_mapped("icon_name", row_dict)

                # Convertir les valeurs numériques
                try:
                    hauteur = float(hauteur) if hauteur else None
                except (ValueError, TypeError):
                    hauteur = None
                try:
                    largeur = float(largeur) if largeur else None
                except (ValueError, TypeError):
                    largeur = None
                try:
                    altitude = float(altitude) if altitude else None
                except (ValueError, TypeError):
                    altitude = None
                try:
                    gps_precision = float(gps_precision) if gps_precision else None
                except (ValueError, TypeError):
                    gps_precision = None
                try:
                    cout_remplacement = float(cout_remplacement) if cout_remplacement else None
                except (ValueError, TypeError):
                    cout_remplacement = None

                # Collecter les propriétés custom
                custom_props = {}
                for src, tgt in request.mapping.items():
                    if tgt.startswith("custom_"):
                        field_name = tgt.replace("custom_", "")
                        val = row_dict.get(src)
                        if val is not None:
                            custom_props[field_name] = val

                # Utiliser le lexique_code mappé ou celui fourni
                final_lexique = mapped_lexique if mapped_lexique else request.lexique_code

                # Utiliser l'ID original si fourni, sinon générer un UUID
                point_id = str(original_id) if original_id else str(uuid.uuid4())
                await db.execute(
                    text("""
                        INSERT INTO geoclic_staging (
                            id, name, type, subtype, lexique_code, project_id,
                            geom, condition_state, point_status,
                            materiau, hauteur, largeur,
                            date_installation, priorite, cout_remplacement,
                            zone_name, altitude, gps_precision, gps_source,
                            comment, color_value, icon_name,
                            custom_properties, sync_status, created_by, created_at
                        ) VALUES (
                            :id, :name, :type, :subtype, :lexique_code, :project_id,
                            ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
                            :condition_state, :point_status,
                            :materiau, :hauteur, :largeur,
                            :date_installation, :priorite, :cout_remplacement,
                            :zone_name, :altitude, :gps_precision, :gps_source,
                            :comment, :color_value, :icon_name,
                            CAST(:custom_props AS jsonb), 'pending', :user_id, NOW()
                        )
                    """),
                    {
                        "id": point_id,
                        "name": str(name) if name else f"Import PostGIS {i+1}",
                        "type": str(point_type) if point_type else None,
                        "subtype": str(subtype) if subtype else None,
                        "lexique_code": final_lexique,
                        "project_id": request.project_id,
                        "lat": lat,
                        "lng": lng,
                        "condition_state": str(condition_state) if condition_state else None,
                        "point_status": str(point_status) if point_status else None,
                        "materiau": str(materiau) if materiau else None,
                        "hauteur": hauteur,
                        "largeur": largeur,
                        "date_installation": str(date_installation) if date_installation else None,
                        "priorite": str(priorite) if priorite else None,
                        "cout_remplacement": cout_remplacement,
                        "zone_name": str(zone_name) if zone_name else None,
                        "altitude": altitude,
                        "gps_precision": gps_precision,
                        "gps_source": str(gps_source) if gps_source else None,
                        "comment": str(comment) if comment else "",
                        "color_value": str(color_value) if color_value else None,
                        "icon_name": str(icon_name) if icon_name else None,
                        "custom_props": json.dumps(custom_props) if custom_props else None,
                        "user_id": current_user["id"],
                    }
                )
                imported += 1

            except Exception as e:
                errors += 1
                error_details.append(f"Ligne {i+1}: {str(e)}")

        await db.commit()

        return PostGISImportResult(
            success=errors == 0,
            imported=imported,
            skipped=skipped,
            errors=errors,
            error_details=error_details[:20],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'import: {str(e)}")


# ============================================================================
# SUGGESTION DE MAPPING
# ============================================================================

@router.get("/tables/{table_name}/suggest-mapping")
async def suggest_mapping(
    table_name: str,
    schema_name: str = "public",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Suggère un mapping automatique pour une table PostGIS.
    """
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    config = await get_postgis_config(db)
    if not config:
        raise HTTPException(status_code=400, detail="Connexion PostGIS non configurée")

    try:
        conn = await get_postgis_connection(config)

        # Récupérer les colonnes
        columns = await conn.fetch("""
            SELECT column_name, udt_name
            FROM information_schema.columns
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
        """, schema_name, table_name)

        await conn.close()

        # Patterns de détection
        patterns = {
            # Champs principaux
            "id": ["id", "uuid", "point_id", "identifiant", "gid", "fid", "objectid"],
            "nom": ["nom", "name", "libelle", "label", "titre", "title", "designation"],
            "latitude": ["latitude", "lat", "y"],
            "longitude": ["longitude", "lng", "lon", "long", "x"],
            "geometry": [],  # Détecté par type
            # Classification
            "type": ["type", "type_point", "categorie_principale"],
            "subtype": ["subtype", "sous_type", "sous-type", "soustype", "subcategory"],
            "lexique_code": ["lexique_code", "code_lexique", "code", "category_code"],
            # Etat et statut
            "condition_state": ["etat", "state", "condition", "condition_state", "etat_condition"],
            "point_status": ["statut", "status", "point_status"],
            # Proprietes physiques
            "materiau": ["materiau", "material", "matiere"],
            "hauteur": ["hauteur", "height", "h", "haut"],
            "largeur": ["largeur", "width", "w", "larg"],
            # Dates et priorite
            "date_installation": ["date_installation", "date_pose", "install_date", "date"],
            "priorite": ["priorite", "priority", "prio"],
            "cout_remplacement": ["cout_remplacement", "cout", "cost", "prix"],
            # Localisation
            "zone_name": ["zone", "zone_name", "secteur", "quartier", "area"],
            "altitude": ["altitude", "alt", "z", "elevation"],
            "gps_precision": ["precision", "gps_precision", "accuracy"],
            "gps_source": ["source", "gps_source", "provider"],
            # Autres
            "comment": ["commentaire", "comment", "description", "desc", "note", "remarque", "observation"],
            "color_value": ["couleur", "color", "color_value"],
            "icon_name": ["icone", "icon", "icon_name", "symbole"],
        }

        mapping = {}

        for col in columns:
            col_name = col["column_name"]
            col_lower = col_name.lower()
            udt_name = col["udt_name"]

            # Détecter la colonne géométrie
            if udt_name == "geometry":
                mapping[col_name] = "geometry"
                continue

            # Chercher dans les patterns
            for target, sources in patterns.items():
                if col_lower in sources:
                    mapping[col_name] = target
                    break

        return {
            "columns": [col["column_name"] for col in columns],
            "suggested_mapping": mapping,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
