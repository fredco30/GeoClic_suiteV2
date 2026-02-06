"""
Service de notifications email - GéoClic Suite
Gère l'envoi des notifications aux citoyens et agents.
"""

import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from services.email_service import EmailService

logger = logging.getLogger(__name__)

# Chemin de base pour les photos
PHOTOS_BASE_PATH = "/app/photos"


async def get_intervention_photo_paths(db: AsyncSession, demande_id: Optional[str]) -> Optional[List[str]]:
    """
    Récupère les chemins des fichiers photos d'intervention pour une demande.

    Args:
        db: Session de base de données
        demande_id: ID de la demande

    Returns:
        Liste des chemins absolus vers les fichiers photos, ou None si aucune photo
    """
    if not demande_id:
        return None

    try:
        result = await db.execute(
            text("SELECT photos_intervention FROM demandes_citoyens WHERE id = CAST(:id AS uuid)"),
            {"id": demande_id}
        )
        row = result.fetchone()

        if not row or not row.photos_intervention:
            return None

        photos = row.photos_intervention
        if not photos:
            return None

        # Convertir les URLs en chemins de fichiers
        # Les URLs sont du type: /api/services/photos/interventions/2026/02/filename.jpg
        # Le chemin réel est: /app/photos/interventions/2026/02/filename.jpg
        file_paths = []
        for photo_url in photos:
            # Extraire le chemin relatif après /api/services/photos/
            if "/api/services/photos/" in photo_url:
                relative_path = photo_url.split("/api/services/photos/")[1]
                full_path = f"{PHOTOS_BASE_PATH}/{relative_path}"
                if os.path.exists(full_path):
                    file_paths.append(full_path)
                else:
                    logger.warning(f"Photo d'intervention non trouvée: {full_path}")

        return file_paths if file_paths else None

    except Exception as e:
        logger.error(f"Erreur récupération photos d'intervention: {e}")
        return None


async def get_email_service_from_settings(db: AsyncSession) -> Optional[EmailService]:
    """Crée un EmailService à partir de la configuration en base."""
    result = await db.execute(
        text("SELECT config_value FROM system_settings WHERE config_key = 'email'")
    )
    row = result.fetchone()

    if not row or not row.config_value:
        return None

    import json
    try:
        config = json.loads(row.config_value)
    except json.JSONDecodeError:
        return None

    if not config.get("enabled"):
        return None

    # Récupérer le nom de la collectivité
    result = await db.execute(
        text("SELECT config_value FROM system_settings WHERE config_key = 'general'")
    )
    general_row = result.fetchone()
    nom_collectivite = "Votre collectivité"
    if general_row and general_row.config_value:
        try:
            general = json.loads(general_row.config_value)
            nom_collectivite = general.get("nom_collectivite", nom_collectivite)
        except json.JSONDecodeError:
            pass

    return EmailService(
        provider="smtp",
        smtp_host=config.get("smtp_host", ""),
        smtp_port=config.get("smtp_port", 587),
        smtp_user=config.get("smtp_user", ""),
        smtp_password=config.get("smtp_password", ""),
        smtp_use_tls=config.get("smtp_tls", True),
        email_from=config.get("sender_email", ""),
        email_from_name=config.get("sender_name", ""),
        nom_collectivite=nom_collectivite,
    )


async def get_email_settings(db: AsyncSession) -> Dict[str, Any]:
    """Récupère les paramètres de notification email."""
    result = await db.execute(
        text("SELECT config_value FROM system_settings WHERE config_key = 'email'")
    )
    row = result.fetchone()

    defaults = {
        "enabled": False,
        "notify_citizen_creation": True,
        "notify_citizen_status_change": True,
        "notify_service_new_demande": True,
        "notify_agent_new_message": True,
        "notify_agent_reminder": True,
        "reminder_hours_before": 24,
    }

    if not row or not row.config_value:
        return defaults

    import json
    try:
        config = json.loads(row.config_value)
        return {**defaults, **config}
    except json.JSONDecodeError:
        return defaults


async def log_email(
    db: AsyncSession,
    recipient_email: str,
    subject: str,
    template_type: str,
    demande_id: Optional[str] = None,
    status: str = "sent",
    error_message: Optional[str] = None,
    recipient_name: Optional[str] = None,
):
    """Enregistre un email dans les logs."""
    try:
        await db.execute(text("""
            INSERT INTO email_logs (recipient_email, recipient_name, subject, template_type, demande_id, status, error_message, sent_at)
            VALUES (:email, :name, :subject, :type, :demande_id, :status, :error, CASE WHEN :status = 'sent' THEN CURRENT_TIMESTAMP ELSE NULL END)
        """), {
            "email": recipient_email,
            "name": recipient_name,
            "subject": subject,
            "type": template_type,
            "demande_id": demande_id,
            "status": status,
            "error": error_message,
        })
        await db.commit()
    except Exception as e:
        logger.error(f"Erreur lors du log email: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS CITOYEN
# ═══════════════════════════════════════════════════════════════════════════════

async def notify_citizen_demande_created(db: AsyncSession, demande: Dict[str, Any]):
    """Notifie le citoyen de la création de sa demande."""
    settings = await get_email_settings(db)
    if not settings.get("enabled") or not settings.get("notify_citizen_creation"):
        return

    email_service = await get_email_service_from_settings(db)
    if not email_service or not email_service.is_configured():
        return

    email = demande.get("declarant_email")
    if not email:
        return

    try:
        success = await email_service.send_notification(
            to_email=email,
            template_type="nouveau",
            variables={
                "numero_suivi": demande.get("numero_suivi", ""),
                "description": demande.get("description", ""),
                "declarant_nom": demande.get("declarant_nom"),
                "categorie_nom": demande.get("categorie_nom", ""),
            },
        )
        await log_email(
            db, email, f"Confirmation signalement {demande.get('numero_suivi')}",
            "creation", demande.get("id"),
            "sent" if success else "failed"
        )
    except Exception as e:
        logger.error(f"Erreur envoi email création: {e}")
        await log_email(db, email, "Confirmation signalement", "creation", demande.get("id"), "failed", str(e))


async def notify_citizen_status_changed(
    db: AsyncSession,
    demande: Dict[str, Any],
    new_status: str,
    commentaire: Optional[str] = None,
    include_photos: bool = True
):
    """
    Notifie le citoyen d'un changement de statut.

    Args:
        db: Session de base de données
        demande: Dictionnaire contenant les infos de la demande
        new_status: Nouveau statut
        commentaire: Commentaire optionnel
        include_photos: Si True et statut="traite", joint les photos d'intervention
    """
    settings = await get_email_settings(db)
    if not settings.get("enabled") or not settings.get("notify_citizen_status_change"):
        return

    email_service = await get_email_service_from_settings(db)
    if not email_service or not email_service.is_configured():
        return

    email = demande.get("declarant_email")
    if not email:
        return

    # Ne pas notifier pour certains statuts internes
    if new_status in ["en_moderation"]:
        return

    # Récupérer les photos d'intervention si statut "traite"
    attachments = None
    if new_status == "traite" and include_photos:
        attachments = await get_intervention_photo_paths(db, demande.get("id"))
        if attachments:
            logger.info(f"Ajout de {len(attachments)} photo(s) d'intervention à l'email")

    try:
        # Utiliser send_email directement pour pouvoir passer les attachments
        template = email_service.get_template(new_status, demande.get("declarant_langue", "fr"))
        formatted = email_service.format_template(template, {
            "numero_suivi": demande.get("numero_suivi", ""),
            "description": demande.get("description", ""),
            "declarant_nom": demande.get("declarant_nom"),
            "categorie_nom": demande.get("categorie_nom", ""),
            "commentaire": commentaire or "",
            "date_planification": demande.get("date_planification"),
        })

        success = await email_service.send_email(
            to_email=email,
            subject=formatted["subject"],
            body=formatted["body"],
            attachments=attachments,
        )

        await log_email(
            db, email, f"Mise à jour signalement {demande.get('numero_suivi')}",
            "status_change", demande.get("id"),
            "sent" if success else "failed"
        )
    except Exception as e:
        logger.error(f"Erreur envoi email statut: {e}")
        await log_email(db, email, "Mise à jour signalement", "status_change", demande.get("id"), "failed", str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS AGENTS/SERVICES
# ═══════════════════════════════════════════════════════════════════════════════

async def notify_service_new_demande(db: AsyncSession, demande: Dict[str, Any], service_id: str):
    """Notifie le service qu'une nouvelle demande lui est assignée."""
    settings = await get_email_settings(db)
    if not settings.get("enabled") or not settings.get("notify_service_new_demande"):
        return

    email_service = await get_email_service_from_settings(db)
    if not email_service or not email_service.is_configured():
        return

    # Récupérer les emails des agents du service
    result = await db.execute(text("""
        SELECT email, nom, prenom FROM demandes_services_agents
        WHERE service_id = CAST(:service_id AS uuid) AND actif = TRUE AND email IS NOT NULL
    """), {"service_id": service_id})
    agents = result.fetchall()

    for agent in agents:
        if not agent.email:
            continue
        try:
            success = await email_service.send_email(
                to_email=agent.email,
                subject=f"Nouvelle demande assignée - {demande.get('numero_suivi')}",
                body=f"""Bonjour {agent.prenom} {agent.nom},

Une nouvelle demande a été assignée à votre service :

Numéro : {demande.get('numero_suivi')}
Catégorie : {demande.get('categorie_nom', 'Non spécifiée')}
Adresse : {demande.get('adresse', 'Non spécifiée')}
Description : {demande.get('description', '')[:200]}

Consultez-la sur GeoClic Services.

Cordialement,
{email_service.nom_collectivite}
"""
            )
            await log_email(
                db, agent.email, f"Nouvelle demande {demande.get('numero_suivi')}",
                "assignment", demande.get("id"),
                "sent" if success else "failed",
                recipient_name=f"{agent.prenom} {agent.nom}"
            )
        except Exception as e:
            logger.error(f"Erreur envoi email agent {agent.email}: {e}")


async def notify_agent_new_message(
    db: AsyncSession,
    demande: Dict[str, Any],
    message_content: str,
    sender_name: str
):
    """Notifie les agents d'un nouveau message du back-office."""
    settings = await get_email_settings(db)
    if not settings.get("enabled") or not settings.get("notify_agent_new_message"):
        return

    email_service = await get_email_service_from_settings(db)
    if not email_service or not email_service.is_configured():
        return

    service_id = demande.get("service_assigne_id")
    if not service_id:
        return

    # Récupérer les emails des agents du service
    result = await db.execute(text("""
        SELECT email, nom, prenom FROM demandes_services_agents
        WHERE service_id = CAST(:service_id AS uuid) AND actif = TRUE AND email IS NOT NULL
    """), {"service_id": service_id})
    agents = result.fetchall()

    for agent in agents:
        if not agent.email:
            continue
        try:
            success = await email_service.send_email(
                to_email=agent.email,
                subject=f"Nouveau message - Demande {demande.get('numero_suivi')}",
                body=f"""Bonjour {agent.prenom} {agent.nom},

Vous avez reçu un nouveau message concernant la demande {demande.get('numero_suivi')} :

De : {sender_name}
Message : "{message_content[:300]}"

Consultez GeoClic Services pour répondre.

Cordialement,
{email_service.nom_collectivite}
"""
            )
            await log_email(
                db, agent.email, f"Nouveau message - {demande.get('numero_suivi')}",
                "new_message", demande.get("id"),
                "sent" if success else "failed",
                recipient_name=f"{agent.prenom} {agent.nom}"
            )
        except Exception as e:
            logger.error(f"Erreur envoi email message agent {agent.email}: {e}")


async def schedule_intervention_reminder(
    db: AsyncSession,
    demande_id: str,
    scheduled_date: datetime,
    agent_id: Optional[str] = None
):
    """Planifie un rappel d'intervention."""
    settings = await get_email_settings(db)
    if not settings.get("enabled") or not settings.get("notify_agent_reminder"):
        return

    hours_before = settings.get("reminder_hours_before", 24)
    from datetime import timedelta
    reminder_time = scheduled_date - timedelta(hours=hours_before)

    # Ne pas planifier si c'est déjà passé
    if reminder_time < datetime.now():
        return

    try:
        await db.execute(text("""
            INSERT INTO email_reminders (demande_id, agent_id, scheduled_at)
            VALUES (CAST(:demande_id AS uuid), CAST(:agent_id AS uuid), :scheduled_at)
            ON CONFLICT DO NOTHING
        """), {
            "demande_id": demande_id,
            "agent_id": agent_id,
            "scheduled_at": reminder_time,
        })
        await db.commit()
    except Exception as e:
        logger.error(f"Erreur planification rappel: {e}")
