"""
Cron job pour l'envoi des rappels d'intervention planifiées.
À exécuter périodiquement (ex: toutes les 15 minutes) via cron ou systemd timer.

Usage:
    python -m services.reminder_cron

Ou via cron:
    */15 * * * * cd /opt/geoclic/api && python -m services.reminder_cron
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_reminders(db_url: str):
    """Traite et envoie les rappels en attente."""
    from services.notifications import get_email_service_from_settings, get_email_settings, log_email

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Vérifier si les rappels sont activés
        settings = await get_email_settings(db)
        if not settings.get("enabled") or not settings.get("notify_agent_reminder"):
            logger.info("Rappels email désactivés")
            return

        email_service = await get_email_service_from_settings(db)
        if not email_service or not email_service.is_configured():
            logger.warning("Service email non configuré")
            return

        # Récupérer les rappels à envoyer (scheduled_at <= maintenant et non envoyés)
        result = await db.execute(text("""
            SELECT
                r.id, r.demande_id, r.agent_id, r.scheduled_at,
                d.numero_suivi, d.description, d.adresse_approximative AS adresse,
                d.date_planification, d.service_assigne_id,
                c.nom AS categorie_nom
            FROM email_reminders r
            JOIN demandes_citoyens d ON r.demande_id = d.id
            LEFT JOIN demandes_categories c ON d.categorie_id = c.id
            WHERE r.sent = FALSE
              AND r.scheduled_at <= CURRENT_TIMESTAMP
              AND d.statut IN ('planifie', 'en_cours')
            ORDER BY r.scheduled_at
            LIMIT 50
        """))
        reminders = result.fetchall()

        if not reminders:
            logger.info("Aucun rappel à envoyer")
            return

        logger.info(f"{len(reminders)} rappel(s) à traiter")

        for reminder in reminders:
            try:
                # Récupérer les agents du service
                if reminder.service_assigne_id:
                    agents_result = await db.execute(text("""
                        SELECT email, nom, prenom FROM demandes_services_agents
                        WHERE service_id = CAST(:service_id AS uuid)
                          AND actif = TRUE AND email IS NOT NULL
                    """), {"service_id": str(reminder.service_assigne_id)})
                    agents = agents_result.fetchall()
                else:
                    agents = []

                # Si agent spécifique assigné au rappel
                if reminder.agent_id:
                    agent_result = await db.execute(text("""
                        SELECT email, nom, prenom FROM demandes_services_agents
                        WHERE id = CAST(:id AS uuid) AND email IS NOT NULL
                    """), {"id": str(reminder.agent_id)})
                    specific_agent = agent_result.fetchone()
                    if specific_agent:
                        agents = [specific_agent]

                # Formater la date
                date_planif = reminder.date_planification
                if date_planif:
                    date_str = date_planif.strftime("%d/%m/%Y à %H:%M")
                else:
                    date_str = "Non définie"

                # Envoyer aux agents
                for agent in agents:
                    if not agent.email:
                        continue

                    success = await email_service.send_email(
                        to_email=agent.email,
                        subject=f"Rappel intervention - Demande {reminder.numero_suivi}",
                        body=f"""Bonjour {agent.prenom} {agent.nom},

Rappel : une intervention est planifiée pour la demande {reminder.numero_suivi}.

Catégorie : {reminder.categorie_nom or 'Non spécifiée'}
Adresse : {reminder.adresse or 'Non spécifiée'}
Date planifiée : {date_str}
Description : {reminder.description[:200] if reminder.description else ''}

Consultez GeoClic Services pour plus de détails.

Cordialement,
{email_service.nom_collectivite}
"""
                    )

                    await log_email(
                        db, agent.email,
                        f"Rappel intervention - {reminder.numero_suivi}",
                        "reminder", str(reminder.demande_id),
                        "sent" if success else "failed",
                        recipient_name=f"{agent.prenom} {agent.nom}"
                    )

                    if success:
                        logger.info(f"Rappel envoyé à {agent.email} pour demande {reminder.numero_suivi}")

                # Marquer le rappel comme envoyé
                await db.execute(text("""
                    UPDATE email_reminders
                    SET sent = TRUE, sent_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """), {"id": reminder.id})
                await db.commit()

            except Exception as e:
                logger.error(f"Erreur traitement rappel {reminder.id}: {e}")
                continue

    logger.info("Traitement des rappels terminé")


def main():
    """Point d'entrée du script."""
    import os
    import sys

    # Ajouter le répertoire parent au path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from config import settings
    db_url = settings.database_url

    asyncio.run(process_reminders(db_url))


if __name__ == "__main__":
    main()
