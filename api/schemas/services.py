"""
Schémas Pydantic pour GeoClic Services.
API dédiée aux équipes terrain des services municipaux.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# ÉNUMÉRATIONS
# ═══════════════════════════════════════════════════════════════════════════════

class AgentRole(str, Enum):
    """Rôles des agents dans un service."""
    responsable = "responsable"  # Peut gérer les agents
    agent = "agent"              # Agent terrain


class SenderType(str, Enum):
    """Type d'expéditeur d'un message."""
    service = "service"    # Agent du service terrain (desktop)
    demandes = "demandes"  # Agent du back-office demandes
    terrain = "terrain"    # Agent terrain via PWA mobile


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

class ServiceLoginRequest(BaseModel):
    """Requête de connexion agent service."""
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)


class ServiceAgentResponse(BaseModel):
    """Réponse avec informations agent."""
    id: str
    service_id: Optional[str] = None  # None pour super_admin sans service
    email: str
    nom: Optional[str] = None
    prenom: Optional[str] = None
    nom_complet: str
    telephone: Optional[str] = None
    role: AgentRole
    peut_assigner: bool = False
    actif: bool = True
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None  # None pour utilisateurs unifiés
    # Infos service (optionnelles pour super_admin)
    service_nom: Optional[str] = None
    service_code: Optional[str] = None
    service_couleur: str = "#3b82f6"
    project_id: Optional[str] = None
    # Flag super_admin
    is_super_admin: bool = False


class ServiceToken(BaseModel):
    """Token JWT pour agent service."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # En secondes
    agent: ServiceAgentResponse


class PasswordChangeRequest(BaseModel):
    """Requête de changement de mot de passe."""
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


# ═══════════════════════════════════════════════════════════════════════════════
# DEMANDES (VUE SERVICE)
# ═══════════════════════════════════════════════════════════════════════════════

class ServiceDemandeListItem(BaseModel):
    """Demande dans la liste (vue service)."""
    id: str
    numero: Optional[str] = None
    description: str
    statut: str
    priorite: str = "normale"
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Catégorie
    categorie_id: Optional[str] = None
    categorie_nom: Optional[str] = None
    categorie_icone: Optional[str] = None
    categorie_couleur: Optional[str] = None
    # Localisation
    adresse: Optional[str] = None
    quartier_nom: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Agent terrain assigné
    agent_service_id: Optional[str] = None
    agent_service_nom: Optional[str] = None
    # Photos
    has_photos: bool = False
    photo_count: int = 0
    # Messages non lus
    unread_messages: int = 0


class ServiceDemandeDetail(ServiceDemandeListItem):
    """Détail complet d'une demande (vue service)."""
    # Citoyen (anonymisé)
    declarant_prenom: Optional[str] = None
    declarant_initial_nom: Optional[str] = None  # Première lettre seulement
    declarant_email_masque: Optional[str] = None  # a***@domain.com
    # Dates
    date_prise_en_charge: Optional[datetime] = None
    date_planification: Optional[datetime] = None
    date_resolution: Optional[datetime] = None
    # Détails
    commentaire_interne: Optional[str] = None
    # Photos et documents
    photos: List[str] = []
    documents: List[str] = []
    photos_intervention: List[str] = []


class ServiceDemandeStatutUpdate(BaseModel):
    """Mise à jour du statut d'une demande."""
    statut: str = Field(..., pattern="^(en_cours|planifie|traite)$")
    commentaire: Optional[str] = None
    date_planification: Optional[datetime] = None  # Date/heure de l'intervention planifiée


class ServiceDemandeAgentUpdate(BaseModel):
    """Assignation d'un agent terrain à une demande."""
    agent_service_id: Optional[str] = None  # None = désassigner


# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGES (TCHAT)
# ═══════════════════════════════════════════════════════════════════════════════

class MessageCreate(BaseModel):
    """Création d'un message."""
    message: str = Field(..., min_length=1, max_length=2000)


class MessageResponse(BaseModel):
    """Message dans le tchat."""
    id: str
    demande_id: str
    sender_type: SenderType
    sender_id: Optional[str] = None
    sender_nom: Optional[str] = None
    message: str
    lu_par_service: bool = False
    lu_par_demandes: bool = False
    created_at: datetime


class UnreadCountItem(BaseModel):
    """Compteur de messages non lus par demande."""
    demande_id: str
    unread_count: int


# ═══════════════════════════════════════════════════════════════════════════════
# GESTION AGENTS (RESPONSABLE UNIQUEMENT)
# ═══════════════════════════════════════════════════════════════════════════════

class AgentCreate(BaseModel):
    """Création d'un agent (par responsable)."""
    email: EmailStr
    password: str = Field(..., min_length=6)
    nom: str = Field(..., min_length=1, max_length=100)
    prenom: str = Field(..., min_length=1, max_length=100)
    telephone: Optional[str] = Field(None, max_length=20)
    role: AgentRole = AgentRole.agent
    peut_assigner: bool = False
    recoit_notifications: bool = True


class AgentUpdate(BaseModel):
    """Modification d'un agent."""
    nom: Optional[str] = Field(None, min_length=1, max_length=100)
    prenom: Optional[str] = Field(None, min_length=1, max_length=100)
    telephone: Optional[str] = Field(None, max_length=20)
    role: Optional[AgentRole] = None
    peut_assigner: Optional[bool] = None
    recoit_notifications: Optional[bool] = None
    actif: Optional[bool] = None


class AgentResetPassword(BaseModel):
    """Reset mot de passe par responsable."""
    new_password: str = Field(..., min_length=6)


class AgentListItem(BaseModel):
    """Agent dans la liste."""
    id: str
    email: str
    nom: Optional[str] = None
    prenom: Optional[str] = None
    nom_complet: str
    telephone: Optional[str] = None
    role: AgentRole
    peut_assigner: bool
    actif: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    # Stats
    demandes_assignees: int = 0
    demandes_traitees: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTIQUES
# ═══════════════════════════════════════════════════════════════════════════════

class ServiceStats(BaseModel):
    """Statistiques du service."""
    # Compteurs
    total_demandes: int = 0
    en_attente: int = 0  # Nouvelles assignées au service
    en_cours: int = 0    # En cours + planifiées
    traitees: int = 0    # Résolues
    # Période
    traitees_jour: int = 0
    traitees_semaine: int = 0
    traitees_mois: int = 0
    # Performance
    delai_moyen_heures: Optional[float] = None
    # Alertes
    urgentes: int = 0
    en_retard: int = 0  # > 7 jours sans action


class ServiceStatsAgent(BaseModel):
    """Stats par agent."""
    agent_id: str
    agent_nom: str
    assignees: int = 0
    en_cours: int = 0
    traitees: int = 0
    delai_moyen_heures: Optional[float] = None
