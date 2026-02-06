"""
Router pour la gestion des photos.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
import uuid
import os
import json
import csv
import zipfile
import tempfile
from PIL import Image
import io

from database import get_db
from routers.auth import get_current_user
from config import settings
from schemas.photo import PhotoMetadata, PhotoUploadResponse


# === Schémas pour l'export ===

class PhotoExportRequest(BaseModel):
    """Requête d'export de photos."""
    point_ids: Optional[List[str]] = None  # Sélection manuelle
    project_id: Optional[str] = None        # Tout le projet
    lexique_code: Optional[str] = None      # Filtre par catégorie


class PhotoExportInfo(BaseModel):
    """Info sur l'export disponible."""
    total_photos: int
    total_points: int
    can_export: bool
    message: Optional[str] = None

router = APIRouter()


def get_storage_path(date: datetime = None) -> Path:
    """Génère le chemin de stockage organisé par date."""
    if date is None:
        date = datetime.now()
    path = Path(settings.photo_storage_path) / str(date.year) / f"{date.month:02d}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_thumbnail(image_data: bytes, size: int = 300) -> bytes:
    """Crée une miniature d'une image."""
    img = Image.open(io.BytesIO(image_data))
    img.thumbnail((size, size), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue()


def extract_exif(image_data: bytes) -> dict:
    """Extrait les métadonnées EXIF d'une image."""
    try:
        img = Image.open(io.BytesIO(image_data))
        exif = img._getexif()
        if not exif:
            return {}

        # Tags EXIF courants
        TAGS = {
            271: "device_make",
            272: "device_model",
            306: "datetime",
            36867: "datetime_original",
        }

        result = {}
        for tag_id, value in exif.items():
            tag_name = TAGS.get(tag_id)
            if tag_name:
                result[tag_name] = value

        return result
    except:
        return {}


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".odt", ".xls", ".xlsx", ".txt", ".csv"}
ALLOWED_DEMANDES_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS


@router.post("/upload", response_model=PhotoUploadResponse)
async def upload_photo(
    file: UploadFile = File(...),
    point_id: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    accuracy: float = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Upload une photo."""
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

    # Vérifier la taille
    max_size = settings.max_photo_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"Image trop volumineuse (max {settings.max_photo_size_mb} Mo)",
        )

    # Valider que c'est une vraie image (protection contre content-type spoofé)
    try:
        img = Image.open(io.BytesIO(content))
        img.verify()  # Vérifie l'intégrité sans charger entièrement
    except Exception:
        raise HTTPException(status_code=400, detail="Le fichier n'est pas une image valide")

    # Générer les chemins - toujours UUID, extension sûre
    photo_id = str(uuid.uuid4())
    now = datetime.now()
    storage_path = get_storage_path(now)
    extension = original_ext.lstrip(".")
    filename = f"{photo_id}.{extension}"

    file_path = storage_path / filename

    # Sauvegarder l'image
    with open(file_path, "wb") as f:
        f.write(content)

    # Thumbnail désactivée - les photos sont assez légères (30-40 Ko)
    # pour être affichées directement sans miniature

    # Extraire EXIF
    exif_data = extract_exif(content)

    # Construire les URLs
    base_url = f"/api/photos/{now.year}/{now.month:02d}"
    photo_url = f"{base_url}/{filename}"
    thumb_url = None  # Plus de thumbnail

    # Créer les métadonnées
    metadata = PhotoMetadata(
        id=photo_id,
        url=photo_url,
        thumbnail_url=thumb_url,
        filename=file.filename,
        size_bytes=file_size,
        taken_at=now,
        gps_lat=latitude,
        gps_lng=longitude,
        gps_accuracy=accuracy,
        device_model=exif_data.get("device_model"),
    )

    # Si un point_id est fourni, mettre à jour le point
    if point_id:
        import logging
        logger = logging.getLogger(__name__)
        try:
            # Récupérer les photos existantes
            result = await db.execute(
                text("SELECT photos FROM geoclic_staging WHERE id = CAST(:id AS uuid)"),
                {"id": point_id},
            )
            row = result.first()
            if row:
                # JSONB peut retourner un objet Python natif (list/dict) ou une string JSON
                raw_photos = row[0]
                if raw_photos is None:
                    existing_photos = []
                elif isinstance(raw_photos, list):
                    existing_photos = raw_photos
                elif isinstance(raw_photos, str):
                    existing_photos = json.loads(raw_photos)
                else:
                    existing_photos = []

                existing_photos.append(metadata.model_dump())

                await db.execute(
                    text("""
                        UPDATE geoclic_staging
                        SET photos = CAST(:photos AS jsonb)
                        WHERE id = CAST(:id AS uuid)
                    """),
                    {"id": point_id, "photos": json.dumps(existing_photos, default=str)},
                )
                await db.commit()
                logger.info(f"Photo {photo_id} ajoutée au point {point_id} (total: {len(existing_photos)})")
            else:
                logger.warning(f"Point {point_id} non trouvé dans geoclic_staging")
        except Exception as e:
            logger.error(f"Erreur mise à jour point {point_id} avec photo: {e}")
            await db.rollback()

    return PhotoUploadResponse(
        success=True,
        photo=metadata,
    )


def _validate_photo_filename(filename: str) -> str:
    """Valide un nom de fichier photo pour éviter le path traversal."""
    if not filename or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Format de fichier non autorisé")
    return filename


@router.get("/{year}/{month}/{filename}")
async def get_photo(
    year: int,
    month: int,
    filename: str,
):
    """Récupère une photo par son chemin."""
    filename = _validate_photo_filename(filename)
    file_path = Path(settings.photo_storage_path) / str(year) / f"{month:02d}" / filename

    # Vérifier que le chemin résolu reste dans le storage
    if not file_path.resolve().is_relative_to(Path(settings.photo_storage_path).resolve()):
        raise HTTPException(status_code=400, detail="Chemin invalide")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Photo non trouvée")

    # Déterminer le type MIME
    extension = Path(filename).suffix.lower().lstrip(".")
    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    media_type = media_types.get(extension, "application/octet-stream")

    return FileResponse(file_path, media_type=media_type)


@router.get("/demandes/{year}/{month}/{filename}")
async def get_demandes_file(
    year: int,
    month: int,
    filename: str,
):
    """Récupère un fichier de demande citoyenne (photo ou document)."""
    # Validation: path traversal + extensions autorisées (images + documents)
    if not filename or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_DEMANDES_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Format de fichier non autorisé")

    file_path = Path(settings.photo_storage_path) / "demandes" / str(year) / f"{month:02d}" / filename

    if not file_path.resolve().is_relative_to(Path(settings.photo_storage_path).resolve()):
        raise HTTPException(status_code=400, detail="Chemin invalide")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")

    extension = ext.lstrip(".")
    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "odt": "application/vnd.oasis.opendocument.text",
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "txt": "text/plain",
        "csv": "text/csv",
    }
    media_type = media_types.get(extension, "application/octet-stream")

    return FileResponse(file_path, media_type=media_type)


@router.get("/interventions/{year}/{month}/{filename}")
async def get_intervention_photo(
    year: int,
    month: int,
    filename: str,
):
    """Récupère une photo d'intervention par son chemin."""
    filename = _validate_photo_filename(filename)
    file_path = Path(settings.photo_storage_path) / "interventions" / str(year) / f"{month:02d}" / filename

    if not file_path.resolve().is_relative_to(Path(settings.photo_storage_path).resolve()):
        raise HTTPException(status_code=400, detail="Chemin invalide")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Photo non trouvée")

    extension = Path(filename).suffix.lower().lstrip(".")
    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    media_type = media_types.get(extension, "application/octet-stream")

    return FileResponse(file_path, media_type=media_type)


@router.delete("/{photo_id}")
async def delete_photo(
    photo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Supprime une photo."""
    # Rechercher la photo dans les points
    result = await db.execute(
        text("""
            SELECT id, photos
            FROM geoclic_staging
            WHERE photos::text LIKE :photo_id
        """),
        {"photo_id": f"%{photo_id}%"},
    )
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Photo non trouvée")

    # Retirer la photo du point
    import json
    photos = json.loads(row["photos"]) if row["photos"] else []
    photos = [p for p in photos if p.get("id") != photo_id]

    await db.execute(
        text("""
            UPDATE geoclic_staging
            SET photos = CAST(:photos AS jsonb)
            WHERE id = :id
        """),
        {"id": str(row["id"]), "photos": json.dumps(photos, default=str)},
    )
    await db.commit()

    # TODO: Supprimer le fichier physique

    return {"success": True, "message": "Photo supprimée"}


# === Export de photos ===

MAX_PHOTOS_EXPORT = 500


async def get_photos_for_export(
    db: AsyncSession,
    point_ids: Optional[List[str]] = None,
    project_id: Optional[str] = None,
    lexique_code: Optional[str] = None,
) -> List[dict]:
    """Récupère les photos et leurs métadonnées pour l'export."""

    # Construire la requête dynamiquement
    conditions = ["photos IS NOT NULL", "jsonb_array_length(photos) > 0"]
    params = {}

    if point_ids and len(point_ids) > 0:
        conditions.append("id::text = ANY(:point_ids)")
        params["point_ids"] = point_ids

    if project_id:
        conditions.append("project_id = :project_id")
        params["project_id"] = project_id

    if lexique_code:
        conditions.append("lexique_code = :lexique_code")
        params["lexique_code"] = lexique_code

    where_clause = " AND ".join(conditions)

    query = f"""
        SELECT
            id,
            name,
            lexique_code,
            project_id,
            ST_Y(geom::geometry) as latitude,
            ST_X(geom::geometry) as longitude,
            created_at,
            photos
        FROM geoclic_staging
        WHERE {where_clause}
        ORDER BY created_at DESC
    """

    result = await db.execute(text(query), params)
    rows = result.mappings().all()

    # Extraire toutes les photos avec leurs infos de point
    all_photos = []
    for row in rows:
        photos = row["photos"] if isinstance(row["photos"], list) else json.loads(row["photos"]) if row["photos"] else []
        for photo in photos:
            all_photos.append({
                "photo": photo,
                "point_id": str(row["id"]),
                "point_name": row["name"],
                "lexique_code": row["lexique_code"],
                "project_id": row["project_id"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "point_created_at": row["created_at"],
            })

    return all_photos


@router.post("/export/info", response_model=PhotoExportInfo)
async def get_export_info(
    request: PhotoExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère les informations sur l'export (nombre de photos, etc.)."""

    photos = await get_photos_for_export(
        db,
        point_ids=request.point_ids,
        project_id=request.project_id,
        lexique_code=request.lexique_code,
    )

    # Compter les points uniques
    unique_points = set(p["point_id"] for p in photos)

    total = len(photos)
    can_export = total > 0 and total <= MAX_PHOTOS_EXPORT

    message = None
    if total == 0:
        message = "Aucune photo trouvée avec ces critères"
    elif total > MAX_PHOTOS_EXPORT:
        message = f"Trop de photos ({total}). Maximum autorisé: {MAX_PHOTOS_EXPORT}. Affinez vos filtres."

    return PhotoExportInfo(
        total_photos=total,
        total_points=len(unique_points),
        can_export=can_export,
        message=message,
    )


@router.post("/export")
async def export_photos(
    request: PhotoExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Exporte les photos en archive ZIP avec métadonnées.

    Retourne un fichier ZIP contenant:
    - Les photos originales (noms conservés)
    - metadata.csv (Excel/QGIS friendly)
    - metadata.json (pour scripts/dev)
    """

    photos_data = await get_photos_for_export(
        db,
        point_ids=request.point_ids,
        project_id=request.project_id,
        lexique_code=request.lexique_code,
    )

    if len(photos_data) == 0:
        raise HTTPException(status_code=404, detail="Aucune photo trouvée avec ces critères")

    if len(photos_data) > MAX_PHOTOS_EXPORT:
        raise HTTPException(
            status_code=400,
            detail=f"Trop de photos ({len(photos_data)}). Maximum: {MAX_PHOTOS_EXPORT}. Affinez vos filtres."
        )

    # Créer le fichier ZIP en mémoire
    zip_buffer = io.BytesIO()

    # Tracking pour les doublons de noms
    filename_counts = {}

    # Préparer les métadonnées
    metadata_list = []

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for item in photos_data:
            photo = item["photo"]
            photo_url = photo.get("url", "")
            original_filename = photo.get("filename", "photo.jpg")

            # Gérer les doublons de noms
            if original_filename in filename_counts:
                filename_counts[original_filename] += 1
                name_parts = original_filename.rsplit(".", 1)
                if len(name_parts) == 2:
                    final_filename = f"{name_parts[0]}_{filename_counts[original_filename]}.{name_parts[1]}"
                else:
                    final_filename = f"{original_filename}_{filename_counts[original_filename]}"
            else:
                filename_counts[original_filename] = 1
                final_filename = original_filename

            # Extraire le chemin physique depuis l'URL
            # URL format: /api/photos/2025/01/uuid.jpg
            url_parts = photo_url.replace("/api/photos/", "").split("/")
            if len(url_parts) >= 3:
                year, month, stored_filename = url_parts[0], url_parts[1], "/".join(url_parts[2:])
                file_path = Path(settings.photo_storage_path) / year / month / stored_filename

                if file_path.exists():
                    # Ajouter la photo au ZIP
                    zip_file.write(file_path, final_filename)

                    # Ajouter aux métadonnées
                    metadata_list.append({
                        "filename": final_filename,
                        "original_filename": original_filename,
                        "point_id": item["point_id"],
                        "point_name": item["point_name"],
                        "lexique_code": item["lexique_code"] or "",
                        "project_id": item["project_id"] or "",
                        "latitude": item["latitude"],
                        "longitude": item["longitude"],
                        "date_photo": photo.get("taken_at", ""),
                        "date_point": str(item["point_created_at"]) if item["point_created_at"] else "",
                        "gps_lat_photo": photo.get("gps_lat"),
                        "gps_lng_photo": photo.get("gps_lng"),
                        "gps_accuracy": photo.get("gps_accuracy"),
                        "device_model": photo.get("device_model", ""),
                        "comment": photo.get("comment", ""),
                    })

        # Créer metadata.csv
        if metadata_list:
            csv_buffer = io.StringIO()
            fieldnames = [
                "filename", "original_filename", "point_id", "point_name",
                "lexique_code", "project_id", "latitude", "longitude",
                "date_photo", "date_point", "gps_lat_photo", "gps_lng_photo",
                "gps_accuracy", "device_model", "comment"
            ]
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            for row in metadata_list:
                writer.writerow(row)

            zip_file.writestr("metadata.csv", csv_buffer.getvalue())

        # Créer metadata.json
        export_date = datetime.now().isoformat()
        json_data = {
            "export_date": export_date,
            "total_photos": len(metadata_list),
            "total_points": len(set(m["point_id"] for m in metadata_list)),
            "filters": {
                "point_ids": request.point_ids,
                "project_id": request.project_id,
                "lexique_code": request.lexique_code,
            },
            "photos": metadata_list,
        }
        zip_file.writestr("metadata.json", json.dumps(json_data, indent=2, default=str))

    # Préparer la réponse
    zip_buffer.seek(0)

    # Nom du fichier ZIP
    date_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    zip_filename = f"export_photos_{date_str}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={zip_filename}"
        }
    )
