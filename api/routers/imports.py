"""
Router pour l'import de données.
Supporte: GeoJSON, CSV, Shapefile (ZIP)
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import json
import csv
import zipfile
import tempfile
import os
import io
import uuid

from database import get_db
from routers.auth import get_current_user

router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class ColumnMapping(BaseModel):
    """Mapping d'une colonne source vers un champ GéoClic."""
    source_column: str
    target_field: str  # nom, latitude, longitude, lexique_code, comment, custom_*


class ImportPreviewResponse(BaseModel):
    """Aperçu des données à importer."""
    format: str
    total_rows: int
    columns: List[str]
    sample_data: List[Dict[str, Any]]
    suggested_mapping: Dict[str, str]
    geometry_column: Optional[str] = None


class ImportRequest(BaseModel):
    """Requête d'import avec mapping."""
    project_id: str
    lexique_code: str
    mapping: Dict[str, str]  # source_column -> target_field
    skip_duplicates: bool = True
    update_existing: bool = False
    duplicate_radius: float = 5.0  # mètres


class ImportResult(BaseModel):
    """Résultat de l'import."""
    success: bool
    imported: int
    updated: int
    skipped: int
    errors: int
    error_details: List[str] = []


# ============================================================================
# HELPERS
# ============================================================================

def detect_delimiter(content: str) -> str:
    """Détecte le délimiteur CSV (virgule ou point-virgule)."""
    first_line = content.split('\n')[0]
    if first_line.count(';') > first_line.count(','):
        return ';'
    return ','


def parse_csv_content(content: str) -> tuple[List[str], List[Dict[str, Any]]]:
    """Parse le contenu CSV et retourne headers + rows."""
    delimiter = detect_delimiter(content)
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    headers = reader.fieldnames or []
    rows = list(reader)
    return headers, rows


def parse_geojson_content(content: str) -> tuple[List[str], List[Dict[str, Any]]]:
    """Parse le contenu GeoJSON et retourne propriétés + features."""
    data = json.loads(content)

    if data.get("type") == "FeatureCollection":
        features = data.get("features", [])
    elif data.get("type") == "Feature":
        features = [data]
    else:
        raise ValueError("Format GeoJSON non supporté")

    if not features:
        return [], []

    # Extraire toutes les propriétés uniques
    all_props = set()
    for f in features:
        props = f.get("properties", {})
        if props:
            all_props.update(props.keys())

    # Convertir features en rows
    rows = []
    for f in features:
        geom = f.get("geometry", {})
        props = f.get("properties", {}) or {}

        row = dict(props)

        # Ajouter les coordonnées si c'est un Point
        if geom.get("type") == "Point":
            coords = geom.get("coordinates", [])
            if len(coords) >= 2:
                row["_longitude"] = coords[0]
                row["_latitude"] = coords[1]

        rows.append(row)

    headers = list(all_props)
    if "_latitude" in rows[0]:
        headers = ["_longitude", "_latitude"] + headers

    return headers, rows


def suggest_mapping(columns: List[str]) -> Dict[str, str]:
    """Suggère un mapping automatique basé sur les noms de colonnes."""
    mapping = {}

    # Patterns pour la détection automatique
    patterns = {
        # Champs principaux
        "id": ["id", "uuid", "point_id", "identifiant", "gid", "fid", "objectid"],
        "nom": ["nom", "name", "libelle", "label", "titre", "title", "designation"],
        "latitude": ["latitude", "lat", "y", "_latitude"],
        "longitude": ["longitude", "lng", "lon", "long", "x", "_longitude"],
        "wkt": ["wkt", "geom", "geometry", "the_geom", "shape"],
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
        "photo_path": ["photo", "image", "photo_path", "image_path", "fichier_photo"],
        "color_value": ["couleur", "color", "color_value"],
        "icon_name": ["icone", "icon", "icon_name", "symbole"],
    }

    for col in columns:
        col_lower = col.lower().strip()
        for target, sources in patterns.items():
            if col_lower in sources:
                mapping[col] = target
                break

    return mapping


def find_geometry_column(columns: List[str], sample_data: List[Dict]) -> Optional[str]:
    """Trouve la colonne contenant la géométrie (WKT, GeoJSON, etc.)."""
    geometry_patterns = ["geom", "geometry", "wkt", "the_geom", "shape"]

    for col in columns:
        if col.lower() in geometry_patterns:
            return col
        # Vérifier si la valeur ressemble à du WKT ou GeoJSON
        if sample_data:
            val = str(sample_data[0].get(col, ""))
            if val.startswith("POINT") or val.startswith("LINESTRING") or val.startswith('{"type":'):
                return col

    return None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/preview")
async def preview_import(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Analyse un fichier et retourne un aperçu pour le mapping.
    Supporte: CSV, GeoJSON, Shapefile (ZIP)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant")

    filename = file.filename.lower()
    content = await file.read()

    try:
        if filename.endswith('.csv'):
            text_content = content.decode('utf-8-sig')  # Gère le BOM Excel
            columns, rows = parse_csv_content(text_content)
            file_format = "csv"

        elif filename.endswith(('.geojson', '.json')):
            text_content = content.decode('utf-8')
            columns, rows = parse_geojson_content(text_content)
            file_format = "geojson"

        elif filename.endswith('.zip'):
            # Shapefile dans un ZIP
            columns, rows = await parse_shapefile_zip(content)
            file_format = "shapefile"

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Format non supporté: {filename}. Utilisez CSV, GeoJSON ou Shapefile (ZIP)"
            )

        if not rows:
            raise HTTPException(status_code=400, detail="Fichier vide ou sans données valides")

        # Suggérer le mapping
        suggested = suggest_mapping(columns)

        # Trouver la colonne géométrie si présente
        geom_col = find_geometry_column(columns, rows)

        return ImportPreviewResponse(
            format=file_format,
            total_rows=len(rows),
            columns=columns,
            sample_data=rows[:10],  # 10 premières lignes
            suggested_mapping=suggested,
            geometry_column=geom_col,
        )

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Fichier JSON/GeoJSON invalide")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Encodage de fichier non supporté. Utilisez UTF-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de l'analyse: {str(e)}")


async def parse_shapefile_zip(content: bytes) -> tuple[List[str], List[Dict[str, Any]]]:
    """Parse un Shapefile contenu dans un ZIP."""
    try:
        import shapefile  # pyshp
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Module shapefile non installé. Contactez l'administrateur."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        # Extraire le ZIP (avec protection path traversal)
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            for member in zf.namelist():
                if member.startswith('/') or '..' in member:
                    raise HTTPException(status_code=400, detail=f"Chemin invalide dans le ZIP: {member}")
            zf.extractall(tmpdir)

        # Trouver le fichier .shp
        shp_file = None
        for fname in os.listdir(tmpdir):
            if fname.lower().endswith('.shp'):
                shp_file = os.path.join(tmpdir, fname)
                break

        if not shp_file:
            raise HTTPException(status_code=400, detail="Aucun fichier .shp trouvé dans le ZIP")

        # Lire le shapefile
        sf = shapefile.Reader(shp_file)
        fields = [f[0] for f in sf.fields[1:]]  # Skip DeletionFlag

        rows = []
        for sr in sf.shapeRecords():
            row = dict(zip(fields, sr.record))

            # Ajouter les coordonnées du centroid
            if sr.shape.shapeType in [1, 11, 21]:  # Point types
                row["_longitude"] = sr.shape.points[0][0]
                row["_latitude"] = sr.shape.points[0][1]
            elif sr.shape.points:
                # Pour les autres types, prendre le centroid
                xs = [p[0] for p in sr.shape.points]
                ys = [p[1] for p in sr.shape.points]
                row["_longitude"] = sum(xs) / len(xs)
                row["_latitude"] = sum(ys) / len(ys)

            rows.append(row)

        columns = fields
        if rows and "_latitude" in rows[0]:
            columns = ["_longitude", "_latitude"] + fields

        return columns, rows


@router.post("/execute", response_model=ImportResult)
async def execute_import(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    lexique_code: str = Form(...),
    mapping: str = Form(...),  # JSON string
    skip_duplicates: bool = Form(True),
    update_existing: bool = Form(False),
    duplicate_radius: float = Form(5.0),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Exécute l'import avec le mapping défini.
    """
    # Vérifier les permissions
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    # Parser le mapping
    try:
        mapping_dict = json.loads(mapping)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Mapping JSON invalide")

    # Lire et parser le fichier
    filename = file.filename.lower() if file.filename else ""
    content = await file.read()

    try:
        if filename.endswith('.csv'):
            text_content = content.decode('utf-8-sig')
            columns, rows = parse_csv_content(text_content)
        elif filename.endswith(('.geojson', '.json')):
            text_content = content.decode('utf-8')
            columns, rows = parse_geojson_content(text_content)
        elif filename.endswith('.zip'):
            columns, rows = await parse_shapefile_zip(content)
        else:
            raise HTTPException(status_code=400, detail="Format non supporté")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lecture fichier: {str(e)}")

    # Vérifier que le mapping contient latitude/longitude ou WKT
    lat_col = None
    lng_col = None
    wkt_col = None
    for src, tgt in mapping_dict.items():
        if tgt == "latitude":
            lat_col = src
        elif tgt == "longitude":
            lng_col = src
        elif tgt == "wkt":
            wkt_col = src

    has_lat_lng = lat_col and lng_col
    has_wkt = wkt_col

    if not has_lat_lng and not has_wkt:
        raise HTTPException(
            status_code=400,
            detail="Le mapping doit inclure soit latitude/longitude, soit une colonne WKT"
        )

    # Helper pour extraire une valeur mappée
    def get_mapped_value(target: str, default=None):
        col = next((s for s, t in mapping_dict.items() if t == target), None)
        return row.get(col, default) if col else default

    # Importer les points
    imported = 0
    updated = 0
    skipped = 0
    errors = 0
    error_details = []

    for i, row in enumerate(rows):
        try:
            # Extraire la géométrie (lat/lng ou WKT)
            lat = None
            lng = None
            geom_sql = None

            if has_wkt and row.get(wkt_col):
                wkt_value = str(row.get(wkt_col, "")).strip()
                if wkt_value.upper().startswith(("POINT", "LINESTRING", "POLYGON")):
                    geom_sql = f"ST_SetSRID(ST_GeomFromText('{wkt_value}'), 4326)"
                    # Extraire lat/lng du centroid pour la vérification doublons
                    if wkt_value.upper().startswith("POINT"):
                        # POINT(lng lat) -> extraire les coordonnées
                        coords = wkt_value.replace("POINT(", "").replace(")", "").strip()
                        parts = coords.split()
                        if len(parts) >= 2:
                            lng = float(parts[0])
                            lat = float(parts[1])
                else:
                    errors += 1
                    error_details.append(f"Ligne {i+1}: Format WKT invalide")
                    continue
            elif has_lat_lng:
                lat = float(row.get(lat_col, 0))
                lng = float(row.get(lng_col, 0))
                geom_sql = f"ST_SetSRID(ST_MakePoint({lng}, {lat}), 4326)"

            if not geom_sql or (lat == 0 and lng == 0 and not has_wkt):
                errors += 1
                error_details.append(f"Ligne {i+1}: Coordonnées invalides")
                continue

            # Extraire tous les champs mappés
            original_id = get_mapped_value("id")
            name = get_mapped_value("nom", f"Point importé {i+1}")
            point_type = get_mapped_value("type")
            subtype = get_mapped_value("subtype")
            mapped_lexique = get_mapped_value("lexique_code")
            condition_state = get_mapped_value("condition_state")
            point_status = get_mapped_value("point_status")
            materiau = get_mapped_value("materiau")
            hauteur = get_mapped_value("hauteur")
            largeur = get_mapped_value("largeur")
            date_installation = get_mapped_value("date_installation")
            priorite = get_mapped_value("priorite")
            cout_remplacement = get_mapped_value("cout_remplacement")
            zone_name = get_mapped_value("zone_name")
            altitude = get_mapped_value("altitude")
            gps_precision = get_mapped_value("gps_precision")
            gps_source = get_mapped_value("gps_source")
            comment = get_mapped_value("comment", "")
            photo_path = get_mapped_value("photo_path")
            color_value = get_mapped_value("color_value")
            icon_name = get_mapped_value("icon_name")

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

            # Construire les photos si chemin fourni
            photos_json = None
            if photo_path:
                photos_json = json.dumps([{"url": str(photo_path), "caption": "Import"}])

            # Collecter les propriétés custom
            custom_props = {}
            for src, tgt in mapping_dict.items():
                if tgt.startswith("custom_"):
                    field_name = tgt.replace("custom_", "")
                    val = row.get(src)
                    if val is not None:
                        custom_props[field_name] = val

            # Vérifier les doublons si on a des coordonnées
            if skip_duplicates and lat and lng:
                dup_result = await db.execute(
                    text("""
                        SELECT id FROM geoclic_staging
                        WHERE ST_DWithin(
                            geom::geography,
                            ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                            :radius
                        )
                        LIMIT 1
                    """),
                    {"lat": lat, "lng": lng, "radius": duplicate_radius}
                )
                if dup_result.first():
                    skipped += 1
                    continue

            # Utiliser le lexique_code mappé ou celui fourni en paramètre
            final_lexique = mapped_lexique if mapped_lexique else lexique_code

            # Utiliser l'ID original si fourni, sinon générer un UUID
            point_id = str(original_id) if original_id else str(uuid.uuid4())
            await db.execute(
                text(f"""
                    INSERT INTO geoclic_staging (
                        id, name, type, subtype, lexique_code, project_id,
                        geom, condition_state, point_status,
                        materiau, hauteur, largeur,
                        date_installation, priorite, cout_remplacement,
                        zone_name, altitude, gps_precision, gps_source,
                        comment, photos, color_value, icon_name,
                        custom_properties, sync_status, created_by, created_at
                    ) VALUES (
                        :id, :name, :type, :subtype, :lexique_code, :project_id,
                        {geom_sql}, :condition_state, :point_status,
                        :materiau, :hauteur, :largeur,
                        :date_installation, :priorite, :cout_remplacement,
                        :zone_name, :altitude, :gps_precision, :gps_source,
                        :comment, CAST(:photos AS jsonb), :color_value, :icon_name,
                        CAST(:custom_props AS jsonb), 'pending', :user_id, NOW()
                    )
                """),
                {
                    "id": point_id,
                    "name": str(name) if name else f"Point importé {i+1}",
                    "type": str(point_type) if point_type else None,
                    "subtype": str(subtype) if subtype else None,
                    "lexique_code": final_lexique,
                    "project_id": project_id,
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
                    "photos": photos_json,
                    "color_value": str(color_value) if color_value else None,
                    "icon_name": str(icon_name) if icon_name else None,
                    "custom_props": json.dumps(custom_props) if custom_props else None,
                    "user_id": current_user["id"],
                }
            )
            imported += 1

        except ValueError as e:
            errors += 1
            error_details.append(f"Ligne {i+1}: {str(e)}")
        except Exception as e:
            errors += 1
            error_details.append(f"Ligne {i+1}: Erreur inattendue - {str(e)}")

    await db.commit()

    return ImportResult(
        success=errors == 0,
        imported=imported,
        updated=updated,
        skipped=skipped,
        errors=errors,
        error_details=error_details[:20],  # Max 20 détails
    )


@router.get("/templates/{format}")
async def download_template(
    format: str,
    current_user: dict = Depends(get_current_user),
):
    """Télécharge un modèle de fichier pour l'import."""
    from fastapi.responses import StreamingResponse

    if format == "csv":
        content = """nom;latitude;longitude;categorie;commentaire;etat
"Point exemple 1";48.8566;2.3522;mobilier;"Commentaire exemple";"bon"
"Point exemple 2";48.8584;2.2945;voirie;"Autre commentaire";"moyen"
"""
        return StreamingResponse(
            iter([content]),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="modele_import.csv"'}
        )

    elif format == "geojson":
        content = json.dumps({
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [2.3522, 48.8566]},
                    "properties": {
                        "nom": "Point exemple 1",
                        "categorie": "mobilier",
                        "commentaire": "Commentaire exemple"
                    }
                }
            ]
        }, indent=2)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="modele_import.geojson"'}
        )

    raise HTTPException(status_code=400, detail=f"Format {format} non supporté")
