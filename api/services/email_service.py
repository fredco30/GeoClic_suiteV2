"""
═══════════════════════════════════════════════════════════════════════════════
Service d'envoi d'emails - GéoClic Suite V14
═══════════════════════════════════════════════════════════════════════════════
Gère l'envoi des notifications email aux citoyens pour le suivi des demandes.
"""

import smtplib
import ssl
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, Any, Literal, List
from datetime import datetime
import asyncio
from functools import lru_cache
import logging
import httpx

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENT MICROSOFT GRAPH POUR OUTLOOK / OFFICE 365
# ═══════════════════════════════════════════════════════════════════════════════


class MicrosoftGraphMailer:
    """
    Client pour envoyer des emails via Microsoft Graph API.

    Prérequis Azure AD :
    1. Créer une "App Registration" dans Azure Portal
    2. Ajouter la permission "Mail.Send" (Application ou Delegated)
    3. Générer un Client Secret
    4. (Si Application permission) Accorder le consentement admin

    Documentation : https://learn.microsoft.com/en-us/graph/api/user-sendmail
    """

    AUTHORITY_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        sender_email: str,
        sender_name: str = "",
    ):
        """
        Args:
            tenant_id: ID du tenant Azure AD (ou 'common' pour multi-tenant)
            client_id: Application (client) ID de l'app Azure
            client_secret: Secret client généré dans Azure
            sender_email: Email de l'expéditeur (doit avoir une boîte Outlook)
            sender_name: Nom affiché de l'expéditeur
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.sender_email = sender_email
        self.sender_name = sender_name or sender_email
        self._access_token: Optional[str] = None
        self._token_expires: float = 0

    async def _get_access_token(self) -> str:
        """Obtient un token d'accès OAuth2 (avec cache)."""
        import time

        # Utiliser le token en cache s'il est encore valide
        if self._access_token and time.time() < self._token_expires - 60:
            return self._access_token

        token_url = self.AUTHORITY_URL.format(tenant_id=self.tenant_id)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "https://graph.microsoft.com/.default",
                },
            )

            if response.status_code != 200:
                logger.error(f"Erreur OAuth Microsoft: {response.text}")
                raise Exception(f"Erreur authentification Microsoft: {response.status_code}")

            data = response.json()
            self._access_token = data["access_token"]
            self._token_expires = time.time() + data.get("expires_in", 3600)

            return self._access_token

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[list[str]] = None,
        importance: Literal["low", "normal", "high"] = "normal",
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """
        Envoie un email via Microsoft Graph API.

        Args:
            to_email: Destinataire
            subject: Sujet
            body: Corps texte
            html_body: Corps HTML (optionnel)
            cc: Liste des destinataires en copie
            importance: Importance du message
            attachments: Liste des chemins vers les fichiers à joindre

        Returns:
            True si l'envoi a réussi
        """
        try:
            token = await self._get_access_token()

            # Construire le message
            message = {
                "message": {
                    "subject": subject,
                    "importance": importance,
                    "body": {
                        "contentType": "HTML" if html_body else "Text",
                        "content": html_body or body,
                    },
                    "toRecipients": [
                        {"emailAddress": {"address": to_email}}
                    ],
                    "from": {
                        "emailAddress": {
                            "address": self.sender_email,
                            "name": self.sender_name,
                        }
                    },
                },
                "saveToSentItems": "true",
            }

            # Ajouter les CC si présents
            if cc:
                message["message"]["ccRecipients"] = [
                    {"emailAddress": {"address": email}} for email in cc
                ]

            # Ajouter les pièces jointes si présentes
            if attachments:
                import os
                import base64
                message["message"]["attachments"] = []
                for file_path in attachments:
                    if not os.path.exists(file_path):
                        logger.warning(f"Pièce jointe non trouvée: {file_path}")
                        continue

                    filename = os.path.basename(file_path)
                    with open(file_path, "rb") as f:
                        content = base64.b64encode(f.read()).decode("utf-8")

                    message["message"]["attachments"].append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": filename,
                        "contentBytes": content,
                    })
                    logger.info(f"Pièce jointe ajoutée (Graph): {filename}")

            # Envoyer via Graph API
            url = f"{self.GRAPH_API_URL}/users/{self.sender_email}/sendMail"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=message,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code == 202:
                    logger.info(f"Email envoyé via Graph API à {to_email}")
                    return True
                else:
                    logger.error(f"Erreur Graph API: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Erreur envoi email Graph API: {e}")
            return False

    def is_configured(self) -> bool:
        """Vérifie si le client est configuré."""
        return bool(
            self.tenant_id and
            self.client_id and
            self.client_secret and
            self.sender_email
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATES PAR DÉFAUT
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_TEMPLATES = {
    "nouveau": {
        "fr": {
            "subject": "Confirmation de votre signalement - {numero_suivi}",
            "body": """
Bonjour{nom_declarant},

Nous avons bien reçu votre signalement concernant :
{description}

Votre numéro de suivi est : {numero_suivi}

Vous pouvez suivre l'avancement de votre demande à tout moment sur notre portail citoyen.

Nous vous tiendrons informé(e) de l'évolution de votre demande.

Cordialement,
{nom_collectivite}
""",
        },
        "en": {
            "subject": "Confirmation of your report - {numero_suivi}",
            "body": """
Hello{nom_declarant},

We have received your report regarding:
{description}

Your tracking number is: {numero_suivi}

You can follow the progress of your request at any time on our citizen portal.

We will keep you informed of the progress of your request.

Best regards,
{nom_collectivite}
""",
        },
    },
    "en_cours": {
        "fr": {
            "subject": "Votre signalement {numero_suivi} est pris en charge",
            "body": """
Bonjour{nom_declarant},

Votre signalement (n° {numero_suivi}) a été pris en charge par nos services.

Catégorie : {categorie_nom}
Description : {description}

Nous mettons tout en oeuvre pour traiter votre demande dans les meilleurs délais.

Cordialement,
{nom_collectivite}
""",
        },
        "en": {
            "subject": "Your report {numero_suivi} is being processed",
            "body": """
Hello{nom_declarant},

Your report (n° {numero_suivi}) has been taken over by our services.

Category: {categorie_nom}
Description: {description}

We are doing everything possible to process your request as soon as possible.

Best regards,
{nom_collectivite}
""",
        },
    },
    "planifie": {
        "fr": {
            "subject": "Intervention planifiée - Signalement {numero_suivi}",
            "body": """
Bonjour{nom_declarant},

Une intervention a été planifiée concernant votre signalement (n° {numero_suivi}).

{commentaire}

Date prévue : {date_planification}

Nous vous tiendrons informé(e) une fois l'intervention réalisée.

Cordialement,
{nom_collectivite}
""",
        },
        "en": {
            "subject": "Scheduled intervention - Report {numero_suivi}",
            "body": """
Hello{nom_declarant},

An intervention has been scheduled for your report (n° {numero_suivi}).

{commentaire}

Scheduled date: {date_planification}

We will keep you informed once the intervention is completed.

Best regards,
{nom_collectivite}
""",
        },
    },
    "traite": {
        "fr": {
            "subject": "Votre signalement {numero_suivi} a été traité",
            "body": """
Bonjour{nom_declarant},

Nous avons le plaisir de vous informer que votre signalement (n° {numero_suivi}) a été traité.

{commentaire}

Nous vous remercions d'avoir contribué à l'amélioration de notre cadre de vie.

Cordialement,
{nom_collectivite}
""",
        },
        "en": {
            "subject": "Your report {numero_suivi} has been resolved",
            "body": """
Hello{nom_declarant},

We are pleased to inform you that your report (n° {numero_suivi}) has been resolved.

{commentaire}

Thank you for contributing to the improvement of our living environment.

Best regards,
{nom_collectivite}
""",
        },
    },
    "rejete": {
        "fr": {
            "subject": "Information sur votre signalement {numero_suivi}",
            "body": """
Bonjour{nom_declarant},

Après examen de votre signalement (n° {numero_suivi}), nous ne sommes malheureusement pas en mesure d'y donner suite.

Motif : {commentaire}

Si vous avez des questions, n'hésitez pas à nous contacter.

Cordialement,
{nom_collectivite}
""",
        },
        "en": {
            "subject": "Information about your report {numero_suivi}",
            "body": """
Hello{nom_declarant},

After reviewing your report (n° {numero_suivi}), we are unfortunately unable to follow up on it.

Reason: {commentaire}

If you have any questions, please do not hesitate to contact us.

Best regards,
{nom_collectivite}
""",
        },
    },
    "commentaire": {
        "fr": {
            "subject": "Mise à jour de votre signalement {numero_suivi}",
            "body": """
Bonjour{nom_declarant},

Une mise à jour a été apportée à votre signalement (n° {numero_suivi}) :

{commentaire}

Cordialement,
{nom_collectivite}
""",
        },
        "en": {
            "subject": "Update on your report {numero_suivi}",
            "body": """
Hello{nom_declarant},

An update has been made to your report (n° {numero_suivi}):

{commentaire}

Best regards,
{nom_collectivite}
""",
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE EMAIL
# ═══════════════════════════════════════════════════════════════════════════════


class EmailService:
    """
    Service d'envoi d'emails pour les notifications citoyens.

    Supporte deux modes :
    - "smtp" : SMTP classique (Gmail, OVH, Mailjet, etc.)
    - "microsoft" : Microsoft Graph API (Outlook / Office 365)
    """

    def __init__(
        self,
        # Paramètres communs
        provider: Literal["smtp", "microsoft"] = "smtp",
        email_from: str = "",
        email_from_name: str = "",
        email_reply_to: Optional[str] = None,
        nom_collectivite: str = "Votre collectivité",
        # Paramètres SMTP
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        smtp_use_tls: bool = True,
        # Paramètres Microsoft Graph
        ms_tenant_id: str = "",
        ms_client_id: str = "",
        ms_client_secret: str = "",
    ):
        self.provider = provider
        self.email_from = email_from
        self.email_from_name = email_from_name
        self.email_reply_to = email_reply_to or email_from
        self.nom_collectivite = nom_collectivite

        # Config SMTP
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_use_tls = smtp_use_tls

        # Config Microsoft Graph
        self.ms_tenant_id = ms_tenant_id
        self.ms_client_id = ms_client_id
        self.ms_client_secret = ms_client_secret

        # Client Microsoft Graph (lazy init)
        self._ms_client: Optional[MicrosoftGraphMailer] = None

        self._custom_templates: Dict[str, Dict[str, Dict[str, str]]] = {}

    def _get_ms_client(self) -> MicrosoftGraphMailer:
        """Retourne le client Microsoft Graph (lazy initialization)."""
        if self._ms_client is None:
            self._ms_client = MicrosoftGraphMailer(
                tenant_id=self.ms_tenant_id,
                client_id=self.ms_client_id,
                client_secret=self.ms_client_secret,
                sender_email=self.email_from,
                sender_name=self.email_from_name,
            )
        return self._ms_client

    def is_configured(self) -> bool:
        """Vérifie si le service email est configuré."""
        if self.provider == "microsoft":
            return bool(
                self.ms_tenant_id and
                self.ms_client_id and
                self.ms_client_secret and
                self.email_from
            )
        else:  # SMTP
            return bool(
                self.smtp_host and self.smtp_user and self.smtp_password and self.email_from
            )

    def set_custom_templates(
        self, templates: Dict[str, Dict[str, Dict[str, str]]]
    ) -> None:
        """Définit des templates personnalisés."""
        self._custom_templates = templates

    def get_template(
        self, template_type: str, langue: str = "fr"
    ) -> Dict[str, str]:
        """Récupère un template (personnalisé ou par défaut)."""
        # Chercher d'abord dans les templates personnalisés
        if template_type in self._custom_templates:
            if langue in self._custom_templates[template_type]:
                return self._custom_templates[template_type][langue]
            elif "fr" in self._custom_templates[template_type]:
                return self._custom_templates[template_type]["fr"]

        # Sinon utiliser les templates par défaut
        if template_type in DEFAULT_TEMPLATES:
            if langue in DEFAULT_TEMPLATES[template_type]:
                return DEFAULT_TEMPLATES[template_type][langue]
            elif "fr" in DEFAULT_TEMPLATES[template_type]:
                return DEFAULT_TEMPLATES[template_type]["fr"]

        # Template générique
        return {
            "subject": "Mise à jour de votre signalement {numero_suivi}",
            "body": "Votre signalement {numero_suivi} a été mis à jour.\n\n{commentaire}\n\nCordialement,\n{nom_collectivite}",
        }

    def format_template(
        self, template: Dict[str, str], variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """Formate un template avec les variables fournies."""
        # Ajouter les variables par défaut
        variables.setdefault("nom_collectivite", self.nom_collectivite)
        variables.setdefault("commentaire", "")
        variables.setdefault("date_planification", "")

        # Formater le nom du déclarant
        if variables.get("declarant_nom"):
            variables["nom_declarant"] = f" {variables['declarant_nom']}"
        else:
            variables["nom_declarant"] = ""

        # Tronquer la description si trop longue
        if variables.get("description"):
            desc = variables["description"]
            if len(desc) > 200:
                variables["description"] = desc[:200] + "..."

        # Formater la date
        if variables.get("date_planification"):
            date_val = variables["date_planification"]
            if isinstance(date_val, datetime):
                variables["date_planification"] = date_val.strftime("%d/%m/%Y à %H:%M")
            elif isinstance(date_val, str):
                try:
                    dt = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
                    variables["date_planification"] = dt.strftime("%d/%m/%Y à %H:%M")
                except ValueError:
                    pass

        # Appliquer les variables au template
        formatted = {}
        for key, value in template.items():
            try:
                formatted[key] = value.format(**variables)
            except KeyError as e:
                logger.warning(f"Variable manquante dans le template: {e}")
                formatted[key] = value

        return formatted

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """
        Envoie un email de manière asynchrone.

        Args:
            to_email: Destinataire
            subject: Sujet
            body: Corps texte
            html_body: Corps HTML (optionnel)
            attachments: Liste des chemins vers les fichiers à joindre (optionnel)
        """
        if not self.is_configured():
            logger.warning("Service email non configuré, email non envoyé")
            return False

        if self.provider == "microsoft":
            # Utiliser Microsoft Graph API
            return await self._get_ms_client().send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                html_body=html_body,
                attachments=attachments,
            )
        else:
            # Utiliser SMTP classique
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self._send_email_sync, to_email, subject, body, html_body, attachments
            )

    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> bool:
        """Envoi synchrone de l'email avec support des pièces jointes."""
        try:
            # Créer le message (mixed pour permettre les pièces jointes)
            msg = MIMEMultipart("mixed")
            msg["Subject"] = subject
            msg["From"] = (
                f"{self.email_from_name} <{self.email_from}>"
                if self.email_from_name
                else self.email_from
            )
            msg["To"] = to_email
            msg["Reply-To"] = self.email_reply_to

            # Créer un conteneur pour le corps (texte + HTML)
            body_container = MIMEMultipart("alternative")
            body_container.attach(MIMEText(body, "plain", "utf-8"))
            if html_body:
                body_container.attach(MIMEText(html_body, "html", "utf-8"))
            msg.attach(body_container)

            # Ajouter les pièces jointes
            if attachments:
                for file_path in attachments:
                    if not os.path.exists(file_path):
                        logger.warning(f"Pièce jointe non trouvée: {file_path}")
                        continue

                    filename = os.path.basename(file_path)
                    with open(file_path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename={filename}"
                        )
                        msg.attach(part)
                        logger.info(f"Pièce jointe ajoutée: {filename}")

            # Connexion SMTP
            if self.smtp_use_tls:
                context = ssl.create_default_context()
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP_SSL(
                    self.smtp_host, self.smtp_port, context=ssl.create_default_context()
                ) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

            logger.info(f"Email envoyé avec succès à {to_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("Erreur d'authentification SMTP")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Erreur SMTP: {e}")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email: {e}")
            return False

    async def send_notification(
        self,
        to_email: str,
        template_type: str,
        variables: Dict[str, Any],
        langue: str = "fr",
    ) -> bool:
        """Envoie une notification email basée sur un template."""
        template = self.get_template(template_type, langue)
        formatted = self.format_template(template, variables)

        return await self.send_email(
            to_email=to_email,
            subject=formatted["subject"],
            body=formatted["body"],
        )

    async def notify_demande_created(
        self,
        demande: Dict[str, Any],
    ) -> bool:
        """Notifie le citoyen de la création de sa demande."""
        return await self.send_notification(
            to_email=demande["declarant_email"],
            template_type="nouveau",
            variables={
                "numero_suivi": demande["numero_suivi"],
                "description": demande["description"],
                "declarant_nom": demande.get("declarant_nom"),
                "categorie_nom": demande.get("categorie_nom", ""),
            },
            langue=demande.get("declarant_langue", "fr"),
        )

    async def notify_demande_status_changed(
        self,
        demande: Dict[str, Any],
        nouveau_statut: str,
        commentaire: Optional[str] = None,
    ) -> bool:
        """Notifie le citoyen d'un changement de statut."""
        # Mapper le statut vers le type de template
        status_template_map = {
            "envoye": "en_cours",
            "en_cours": "en_cours",
            "accepte": "en_cours",
            "planifie": "planifie",
            "traite": "traite",
            "rejete": "rejete",
            "cloture": "traite",
        }

        template_type = status_template_map.get(nouveau_statut)
        if not template_type:
            return False

        return await self.send_notification(
            to_email=demande["declarant_email"],
            template_type=template_type,
            variables={
                "numero_suivi": demande["numero_suivi"],
                "description": demande["description"],
                "declarant_nom": demande.get("declarant_nom"),
                "categorie_nom": demande.get("categorie_nom", ""),
                "commentaire": commentaire or "",
                "date_planification": demande.get("date_planification"),
            },
            langue=demande.get("declarant_langue", "fr"),
        )

    async def notify_demande_comment(
        self,
        demande: Dict[str, Any],
        commentaire: str,
    ) -> bool:
        """Notifie le citoyen d'un nouveau commentaire."""
        return await self.send_notification(
            to_email=demande["declarant_email"],
            template_type="commentaire",
            variables={
                "numero_suivi": demande["numero_suivi"],
                "description": demande["description"],
                "declarant_nom": demande.get("declarant_nom"),
                "commentaire": commentaire,
            },
            langue=demande.get("declarant_langue", "fr"),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY DEPUIS CONFIG DB
# ═══════════════════════════════════════════════════════════════════════════════


async def get_email_service_for_project(
    db: AsyncSession, project_id: str
) -> EmailService:
    """Récupère le service email configuré pour un projet."""
    query = text("""
        SELECT
            provider,
            smtp_host,
            smtp_port,
            smtp_user,
            smtp_password,
            smtp_use_tls,
            email_from,
            email_from_name,
            email_reply_to,
            ms_tenant_id,
            ms_client_id,
            ms_client_secret,
            template_nouveau,
            template_pris_en_charge,
            template_planifie,
            template_traite,
            template_rejete
        FROM demandes_config_email
        WHERE project_id = :project_id
    """)

    result = await db.execute(query, {"project_id": project_id})
    config = result.fetchone()

    if not config:
        return EmailService()

    # Récupérer le nom de la collectivité depuis le projet
    project_query = text("SELECT nom FROM projects WHERE id = :project_id")
    project_result = await db.execute(project_query, {"project_id": project_id})
    project = project_result.fetchone()
    nom_collectivite = project[0] if project else "Votre collectivité"

    service = EmailService(
        # Provider (smtp ou microsoft)
        provider=config.provider or "smtp",
        # Commun
        email_from=config.email_from or "",
        email_from_name=config.email_from_name or "",
        email_reply_to=config.email_reply_to,
        nom_collectivite=nom_collectivite,
        # SMTP
        smtp_host=config.smtp_host or "",
        smtp_port=config.smtp_port or 587,
        smtp_user=config.smtp_user or "",
        smtp_password=config.smtp_password or "",
        smtp_use_tls=config.smtp_use_tls if config.smtp_use_tls is not None else True,
        # Microsoft Graph
        ms_tenant_id=config.ms_tenant_id or "",
        ms_client_id=config.ms_client_id or "",
        ms_client_secret=config.ms_client_secret or "",
    )

    # Charger les templates personnalisés si présents
    custom_templates = {}
    if config.template_nouveau:
        custom_templates["nouveau"] = {"fr": {"subject": "", "body": config.template_nouveau}}
    if config.template_pris_en_charge:
        custom_templates["en_cours"] = {"fr": {"subject": "", "body": config.template_pris_en_charge}}
    if config.template_planifie:
        custom_templates["planifie"] = {"fr": {"subject": "", "body": config.template_planifie}}
    if config.template_traite:
        custom_templates["traite"] = {"fr": {"subject": "", "body": config.template_traite}}
    if config.template_rejete:
        custom_templates["rejete"] = {"fr": {"subject": "", "body": config.template_rejete}}

    if custom_templates:
        service.set_custom_templates(custom_templates)

    return service


# Singleton pour usage simple (sans config DB)
_default_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Retourne le service email par défaut (singleton)."""
    global _default_email_service
    if _default_email_service is None:
        _default_email_service = EmailService()
    return _default_email_service


def configure_email_service(
    provider: Literal["smtp", "microsoft"] = "smtp",
    email_from: str = "",
    email_from_name: str = "",
    nom_collectivite: str = "Votre collectivité",
    # SMTP
    smtp_host: str = "",
    smtp_port: int = 587,
    smtp_user: str = "",
    smtp_password: str = "",
    smtp_use_tls: bool = True,
    # Microsoft Graph
    ms_tenant_id: str = "",
    ms_client_id: str = "",
    ms_client_secret: str = "",
) -> EmailService:
    """
    Configure le service email par défaut.

    Pour SMTP (Gmail, OVH, Mailjet, etc.):
        configure_email_service(
            provider="smtp",
            smtp_host="smtp.office365.com",  # ou smtp.gmail.com, etc.
            smtp_port=587,
            smtp_user="user@domain.com",
            smtp_password="password",
            email_from="noreply@mairie.fr",
        )

    Pour Microsoft 365 / Outlook (recommandé):
        configure_email_service(
            provider="microsoft",
            ms_tenant_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            ms_client_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            ms_client_secret="your-client-secret",
            email_from="noreply@mairie.fr",  # Doit être une boîte valide
        )
    """
    global _default_email_service
    _default_email_service = EmailService(
        provider=provider,
        email_from=email_from,
        email_from_name=email_from_name,
        nom_collectivite=nom_collectivite,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        smtp_use_tls=smtp_use_tls,
        ms_tenant_id=ms_tenant_id,
        ms_client_id=ms_client_id,
        ms_client_secret=ms_client_secret,
    )
    return _default_email_service
