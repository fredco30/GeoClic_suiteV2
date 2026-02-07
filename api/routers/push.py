"""
Router pour les notifications push (Web Push API / VAPID).
Permet aux agents terrain de recevoir des notifications sur leur téléphone.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
import logging
import json

from config import settings
from database import get_db
from routers.auth import get_current_user

logger = logging.getLogger("geoclic.push")

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class PushSubscription(BaseModel):
    endpoint: str
    keys: dict  # { p256dh: str, auth: str }


class PushNotificationRequest(BaseModel):
    user_id: Optional[str] = None  # Si vide, envoie à tous les agents du service
    service_id: Optional[str] = None
    title: str
    body: str
    url: Optional[str] = None  # URL à ouvrir au clic


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS PUBLICS (clé VAPID)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """Retourne la clé publique VAPID pour le frontend."""
    if not settings.vapid_public_key:
        raise HTTPException(503, "Notifications push non configurées (VAPID_PUBLIC_KEY manquante)")
    return {"public_key": settings.vapid_public_key}


# ═══════════════════════════════════════════════════════════════════════════════
# SOUSCRIPTION
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/subscribe")
async def subscribe(
    subscription: PushSubscription,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enregistre une souscription push pour l'utilisateur connecté."""
    if not settings.vapid_public_key or not settings.vapid_private_key:
        raise HTTPException(503, "Notifications push non configurées")

    user_id = current_user["id"]

    # Upsert : si l'endpoint existe déjà, on met à jour
    await db.execute(text("""
        INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth)
        VALUES (CAST(:user_id AS uuid), :endpoint, :p256dh, :auth)
        ON CONFLICT (endpoint)
        DO UPDATE SET
            user_id = CAST(:user_id AS uuid),
            p256dh = :p256dh,
            auth = :auth,
            last_used_at = NOW()
    """), {
        "user_id": user_id,
        "endpoint": subscription.endpoint,
        "p256dh": subscription.keys.get("p256dh", ""),
        "auth": subscription.keys.get("auth", ""),
    })
    await db.commit()

    logger.info(f"Push subscription enregistrée pour user {user_id}")
    return {"status": "ok"}


@router.delete("/unsubscribe")
async def unsubscribe(
    subscription: PushSubscription,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Supprime une souscription push."""
    await db.execute(text("""
        DELETE FROM push_subscriptions WHERE endpoint = :endpoint
    """), {"endpoint": subscription.endpoint})
    await db.commit()

    return {"status": "ok"}


# ═══════════════════════════════════════════════════════════════════════════════
# ENVOI DE NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def send_push_to_user(user_id: str, title: str, body: str, url: str | None, db: AsyncSession):
    """Envoie une notification push à un utilisateur spécifique."""
    if not settings.vapid_private_key or not settings.vapid_public_key:
        logger.warning("Push non configuré, notification ignorée")
        return 0

    result = await db.execute(text("""
        SELECT endpoint, p256dh, auth FROM push_subscriptions
        WHERE user_id = CAST(:user_id AS uuid)
    """), {"user_id": user_id})
    subscriptions = result.mappings().all()

    if not subscriptions:
        return 0

    from pywebpush import webpush, WebPushException

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url or "/terrain/",
        "icon": "/terrain/icon-192.png",
        "badge": "/terrain/icon-192.png",
    })

    sent = 0
    expired_endpoints = []

    for sub in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub["endpoint"],
                    "keys": {
                        "p256dh": sub["p256dh"],
                        "auth": sub["auth"],
                    }
                },
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_contact_email},
            )
            sent += 1
        except WebPushException as e:
            if e.response and e.response.status_code in (404, 410):
                # Souscription expirée, la supprimer
                expired_endpoints.append(sub["endpoint"])
                logger.info(f"Push subscription expirée, suppression: {sub['endpoint'][:50]}...")
            else:
                logger.error(f"Erreur push notification: {e}")
        except Exception as e:
            logger.error(f"Erreur push inattendue: {e}")

    # Nettoyer les souscriptions expirées
    for endpoint in expired_endpoints:
        await db.execute(text(
            "DELETE FROM push_subscriptions WHERE endpoint = :endpoint"
        ), {"endpoint": endpoint})

    if expired_endpoints:
        await db.commit()

    return sent


async def send_push_to_service(service_id: str, title: str, body: str, url: str | None, db: AsyncSession):
    """Envoie une notification push à tous les agents d'un service."""
    # Trouver les user_ids des agents du service
    result = await db.execute(text("""
        SELECT gu.id::text as user_id
        FROM geoclic_users gu
        JOIN demandes_services_agents dsa ON dsa.email = gu.email
        WHERE dsa.service_id = CAST(:service_id AS uuid)
        AND gu.actif = TRUE
    """), {"service_id": service_id})
    agents = result.mappings().all()

    total_sent = 0
    for agent in agents:
        total_sent += await send_push_to_user(agent["user_id"], title, body, url, db)

    return total_sent


@router.post("/send")
async def send_notification(
    notification: PushNotificationRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Envoie une notification push (admin ou responsable uniquement)."""
    # Vérifier les droits
    if not current_user.get("is_super_admin") and current_user.get("role_demandes") != "admin":
        raise HTTPException(403, "Accès réservé aux administrateurs")

    if notification.user_id:
        sent = await send_push_to_user(
            notification.user_id, notification.title, notification.body, notification.url, db
        )
    elif notification.service_id:
        sent = await send_push_to_service(
            notification.service_id, notification.title, notification.body, notification.url, db
        )
    else:
        raise HTTPException(400, "Spécifiez user_id ou service_id")

    return {"sent": sent}
