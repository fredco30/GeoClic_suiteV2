"""
Router pour la génération de QR codes.
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from pydantic import BaseModel
import qrcode
from io import BytesIO

from database import get_db
from routers.auth import get_current_user
from config import settings

router = APIRouter()


class BatchQRRequest(BaseModel):
    point_ids: List[str]
    format: str = "pdf"  # pdf ou png


def generate_qr_image(data: str, size: int = 200) -> bytes:
    """Génère une image QR code."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Redimensionner
    img = img.resize((size, size))

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


@router.get("/point/{point_id}")
async def generate_qr_for_point(
    point_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Génère un QR code pour un point."""
    # Vérifier que le point existe
    result = await db.execute(
        text("SELECT id, name FROM geoclic_staging WHERE id = :id"),
        {"id": point_id},
    )
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Point non trouvé")

    # Générer l'URL du point
    base_url = getattr(settings, 'frontend_url', 'http://localhost:3000')
    point_url = f"{base_url}/point/{point_id}"

    # Générer le QR code
    qr_image = generate_qr_image(point_url)

    return Response(
        content=qr_image,
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="qr_{point_id}.png"'
        }
    )


@router.post("/batch")
async def generate_batch_qr(
    request: BatchQRRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Génère des QR codes pour plusieurs points."""
    if not request.point_ids:
        raise HTTPException(status_code=400, detail="Aucun point sélectionné")

    # Récupérer les infos des points
    # Sécurité : les placeholders sont des paramètres nommés (:id_0, :id_1, ...).
    # Les valeurs (point_ids) sont passées en paramètres, pas interpolées dans le SQL.
    placeholders = ", ".join([f":id_{i}" for i in range(len(request.point_ids))])
    params = {f"id_{i}": pid for i, pid in enumerate(request.point_ids)}

    result = await db.execute(
        text(f"SELECT id, name FROM geoclic_staging WHERE id IN ({placeholders})"),
        params,
    )
    rows = result.mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail="Aucun point trouvé")

    base_url = getattr(settings, 'frontend_url', 'http://localhost:3000')

    if request.format == "png":
        # Retourner un ZIP avec les images
        import zipfile

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for row in rows:
                point_url = f"{base_url}/point/{row['id']}"
                qr_image = generate_qr_image(point_url)

                # Nettoyer le nom pour le fichier
                safe_name = "".join(c for c in row['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"qr_{safe_name}_{row['id'][:8]}.png"

                zip_file.writestr(filename, qr_image)

        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="qrcodes.zip"'}
        )

    else:
        # Générer un PDF avec les QR codes
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import cm

            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=A4)
            width, height = A4

            # Configuration: 3 colonnes x 8 lignes
            cols = 3
            rows_per_page = 8
            qr_size = 4 * cm
            margin_x = 2 * cm
            margin_y = 1.5 * cm
            spacing_x = (width - 2 * margin_x - cols * qr_size) / (cols - 1) if cols > 1 else 0
            spacing_y = (height - 2 * margin_y - rows_per_page * (qr_size + 1 * cm)) / (rows_per_page - 1) if rows_per_page > 1 else 0

            for i, row in enumerate(rows):
                if i > 0 and i % (cols * rows_per_page) == 0:
                    c.showPage()

                page_index = i % (cols * rows_per_page)
                col = page_index % cols
                page_row = page_index // cols

                x = margin_x + col * (qr_size + spacing_x)
                y = height - margin_y - (page_row + 1) * (qr_size + 1 * cm)

                # Générer le QR
                point_url = f"{base_url}/point/{row['id']}"
                qr_image = generate_qr_image(point_url, size=300)

                # Ajouter l'image au PDF
                from reportlab.lib.utils import ImageReader
                img = ImageReader(BytesIO(qr_image))
                c.drawImage(img, x, y + 0.5 * cm, width=qr_size, height=qr_size)

                # Ajouter le nom sous le QR
                c.setFont("Helvetica", 8)
                name_text = row['name'][:30] + "..." if len(row['name']) > 30 else row['name']
                c.drawCentredString(x + qr_size / 2, y, name_text)

            c.save()
            pdf_buffer.seek(0)

            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={"Content-Disposition": 'attachment; filename="qrcodes.pdf"'}
            )

        except ImportError:
            # Si reportlab n'est pas installé, retourner un ZIP
            raise HTTPException(
                status_code=500,
                detail="reportlab non installé. Utilisez format=png"
            )
