"""
Router pour les paramètres système.
GéoClic Suite V14 - Paramètres généraux et email.

Endpoints:
- /api/settings/general - Paramètres généraux
- /api/settings/email - Configuration email
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
import json
import os
import uuid
from pathlib import Path

from database import get_db
from routers.auth import get_current_user
from pydantic import BaseModel, EmailStr

# Répertoire de stockage des logos
LOGO_DIR = Path("/app/photos/logos")
LOGO_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif"}


router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# SCHÉMAS
# ═══════════════════════════════════════════════════════════════════════════════

class GeneralSettings(BaseModel):
    """Paramètres généraux de l'application."""
    nom_collectivite: Optional[str] = None
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    email_contact: Optional[str] = None
    site_web: Optional[str] = None
    logo_url: Optional[str] = None
    fuseau_horaire: str = "Europe/Paris"
    langue_defaut: str = "fr"
    moderation_active: bool = True
    notification_nouvelle_demande: bool = True
    # Branding / White-label
    primary_color: str = "#2563eb"
    secondary_color: str = "#1f2937"
    accent_color: str = "#10b981"
    sidebar_color: str = "#1f2937"
    favicon_url: Optional[str] = None


class EmailSettings(BaseModel):
    """Configuration SMTP pour l'envoi d'emails."""
    # Configuration SMTP
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_tls: bool = True
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    enabled: bool = False

    # Notifications citoyen
    notify_citizen_creation: bool = True
    notify_citizen_status_change: bool = True

    # Notifications service/agents
    notify_service_new_demande: bool = True
    notify_agent_new_message: bool = True
    notify_agent_reminder: bool = True

    # Délai rappel (en heures avant intervention planifiée)
    reminder_hours_before: int = 24


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

async def get_setting(db: AsyncSession, key: str) -> Optional[dict]:
    """Récupère un paramètre par sa clé."""
    result = await db.execute(
        text("SELECT config_value FROM system_settings WHERE config_key = :key"),
        {"key": key}
    )
    row = result.fetchone()
    if row and row.config_value:
        try:
            return json.loads(row.config_value)
        except json.JSONDecodeError:
            return None
    return None


async def set_setting(db: AsyncSession, key: str, value: dict, user_id: str, description: str = None):
    """Enregistre ou met à jour un paramètre."""
    json_value = json.dumps(value)

    # Upsert - avec cast UUID explicite et fallback si FK échoue
    try:
        await db.execute(text("""
            INSERT INTO system_settings (config_key, config_value, description, updated_by, updated_at)
            VALUES (:key, :value, :description, CAST(:user_id AS uuid), CURRENT_TIMESTAMP)
            ON CONFLICT (config_key) DO UPDATE SET
                config_value = EXCLUDED.config_value,
                updated_by = EXCLUDED.updated_by,
                updated_at = CURRENT_TIMESTAMP
        """), {
            "key": key,
            "value": json_value,
            "description": description,
            "user_id": str(user_id) if user_id else None
        })
        await db.commit()
    except Exception:
        await db.rollback()
        # Fallback: sauvegarder sans updated_by si la FK échoue
        await db.execute(text("""
            INSERT INTO system_settings (config_key, config_value, description, updated_at)
            VALUES (:key, :value, :description, CURRENT_TIMESTAMP)
            ON CONFLICT (config_key) DO UPDATE SET
                config_value = EXCLUDED.config_value,
                updated_at = CURRENT_TIMESTAMP
        """), {
            "key": key,
            "value": json_value,
            "description": description
        })
        await db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# PARAMÈTRES GÉNÉRAUX
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/general", response_model=GeneralSettings)
async def get_general_settings(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère les paramètres généraux."""
    data = await get_setting(db, "general")
    if data:
        return GeneralSettings(**data)
    return GeneralSettings()


@router.put("/general", response_model=GeneralSettings)
async def update_general_settings(
    settings: GeneralSettings,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Met à jour les paramètres généraux."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin" and current_user.get("role_demandes") != "admin":
        raise HTTPException(status_code=403, detail="Droits admin requis")

    await set_setting(
        db,
        "general",
        settings.model_dump(),
        current_user.get("id"),
        "Paramètres généraux de la collectivité"
    )
    return settings


# ═══════════════════════════════════════════════════════════════════════════════
# PARAMÈTRES EMAIL
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/email", response_model=EmailSettings)
async def get_email_settings(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère la configuration email."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin" and current_user.get("role_demandes") != "admin":
        raise HTTPException(status_code=403, detail="Droits admin requis")

    data = await get_setting(db, "email")
    if data:
        # Masquer le mot de passe
        if data.get("smtp_password"):
            data["smtp_password"] = "********"
        return EmailSettings(**data)
    return EmailSettings()


@router.put("/email", response_model=EmailSettings)
async def update_email_settings(
    settings: EmailSettings,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Met à jour la configuration email."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin" and current_user.get("role_demandes") != "admin":
        raise HTTPException(status_code=403, detail="Droits admin requis")

    # Si le mot de passe est masqué, garder l'ancien
    if settings.smtp_password == "********":
        current = await get_setting(db, "email")
        if current:
            settings.smtp_password = current.get("smtp_password")

    await set_setting(
        db,
        "email",
        settings.model_dump(),
        current_user.get("id"),
        "Configuration SMTP pour l'envoi d'emails"
    )

    # Retourner avec mot de passe masqué
    result = settings.model_copy()
    if result.smtp_password:
        result.smtp_password = "********"
    return result


@router.post("/email/test")
async def test_email_settings(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Teste la configuration email en envoyant un email de test."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin" and current_user.get("role_demandes") != "admin":
        raise HTTPException(status_code=403, detail="Droits admin requis")

    data = await get_setting(db, "email")
    if not data or not data.get("enabled"):
        raise HTTPException(status_code=400, detail="Configuration email non activée")

    if not data.get("smtp_host") or not data.get("sender_email"):
        raise HTTPException(status_code=400, detail="Configuration email incomplète")

    # Tenter d'envoyer un email de test
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg['From'] = f"{data.get('sender_name', 'GéoClic')} <{data['sender_email']}>"
        msg['To'] = current_user.get("email")
        msg['Subject'] = "Test de configuration email - GéoClic"

        body = """
        Ceci est un email de test envoyé depuis GéoClic.

        Si vous recevez ce message, votre configuration SMTP est correcte !

        Cordialement,
        L'équipe GéoClic
        """
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Connexion SMTP
        if data.get("smtp_tls", True):
            server = smtplib.SMTP(data["smtp_host"], data.get("smtp_port", 587))
            server.starttls()
        else:
            server = smtplib.SMTP(data["smtp_host"], data.get("smtp_port", 25))

        if data.get("smtp_user") and data.get("smtp_password"):
            server.login(data["smtp_user"], data["smtp_password"])

        server.send_message(msg)
        server.quit()

        return {"success": True, "message": f"Email de test envoyé à {current_user.get('email')}"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'envoi: {str(e)}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER POUR RÉCUPÉRER LA CONFIG EMAIL
# ═══════════════════════════════════════════════════════════════════════════════

async def get_email_config(db: AsyncSession) -> Optional[dict]:
    """Récupère la configuration email depuis les settings."""
    return await get_setting(db, "email")


# ═══════════════════════════════════════════════════════════════════════════════
# UPLOAD LOGO
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Upload du logo de la collectivité."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin" and current_user.get("role_demandes") != "admin":
        raise HTTPException(status_code=403, detail="Droits admin requis")

    # Vérifier l'extension
    ext = Path(file.filename).suffix.lower() if file.filename else ""
    if ext not in ALLOWED_LOGO_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Extension non autorisée. Formats acceptés: {', '.join(ALLOWED_LOGO_EXTENSIONS)}")

    # Vérifier la taille (max 5 MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 5 MB)")

    # Supprimer l'ancien logo s'il existe
    current_settings = await get_setting(db, "general")
    if current_settings and current_settings.get("logo_url", "").startswith("/api/settings/logo/"):
        old_filename = current_settings["logo_url"].split("/")[-1]
        old_path = LOGO_DIR / old_filename
        if old_path.exists():
            old_path.unlink()

    # Sauvegarder le fichier avec un nom unique
    filename = f"logo_{uuid.uuid4().hex[:8]}{ext}"
    filepath = LOGO_DIR / filename
    with open(filepath, "wb") as f:
        f.write(content)

    # Mettre à jour logo_url dans les settings
    logo_url = f"/api/settings/logo/{filename}"
    if current_settings:
        current_settings["logo_url"] = logo_url
    else:
        current_settings = {"logo_url": logo_url}

    await set_setting(db, "general", current_settings, current_user.get("id"), "Logo uploadé")

    return {"logo_url": logo_url, "filename": filename}


@router.get("/logo/{filename}")
async def get_logo(filename: str):
    """Sert le fichier logo (endpoint public)."""
    from fastapi.responses import FileResponse

    # Sécurité: empêcher path traversal
    safe_filename = Path(filename).name
    filepath = LOGO_DIR / safe_filename

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Logo non trouvé")

    # Détecter le content type
    ext = filepath.suffix.lower()
    content_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    content_type = content_types.get(ext, "application/octet-stream")

    return FileResponse(filepath, media_type=content_type)


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT PUBLIC - BRANDING (sans authentification)
# ═══════════════════════════════════════════════════════════════════════════════

class BrandingConfig(BaseModel):
    """Configuration de branding publique pour les frontends."""
    nom_collectivite: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = "#2563eb"
    secondary_color: str = "#1f2937"
    accent_color: str = "#10b981"
    sidebar_color: str = "#1f2937"
    site_web: Optional[str] = None
    telephone: Optional[str] = None
    email_contact: Optional[str] = None


@router.get("/branding", response_model=BrandingConfig)
async def get_branding(
    db: AsyncSession = Depends(get_db),
):
    """Récupère la configuration de branding (endpoint public, pas d'auth requise)."""
    data = await get_setting(db, "general")
    if data:
        return BrandingConfig(
            nom_collectivite=data.get("nom_collectivite"),
            logo_url=data.get("logo_url"),
            favicon_url=data.get("favicon_url"),
            primary_color=data.get("primary_color", "#2563eb"),
            secondary_color=data.get("secondary_color", "#1f2937"),
            accent_color=data.get("accent_color", "#10b981"),
            sidebar_color=data.get("sidebar_color", "#1f2937"),
            site_web=data.get("site_web"),
            telephone=data.get("telephone"),
            email_contact=data.get("email_contact"),
        )
    return BrandingConfig()
