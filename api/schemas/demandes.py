"""
Schemas Pydantic pour les demandes citoyennes.
GéoClic Suite V14 - Phase 3 Portail Citoyen
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class DemandeStatut(str, Enum):
    nouveau = "nouveau"
    en_moderation = "en_moderation"
    envoye = "envoye"
    accepte = "accepte"
    en_cours = "en_cours"
    planifie = "planifie"
    traite = "traite"
    rejete = "rejete"
    cloture = "cloture"


class DemandePriorite(str, Enum):
    basse = "basse"
    normale = "normale"
    haute = "haute"
    urgente = "urgente"


class DemandeSource(str, Enum):
    app_citoyen = "app_citoyen"
    qr_code = "qr_code"
    web = "web"
    email = "email"
    telephone = "telephone"
    backoffice = "backoffice"


class HistoriqueAction(str, Enum):
    creation = "creation"
    changement_statut = "changement_statut"
    assignation = "assignation"
    commentaire = "commentaire"
    reponse_citoyen = "reponse_citoyen"
    planification = "planification"
    resolution = "resolution"
    rejet = "rejet"
    cloture = "cloture"
    reouverture = "reouverture"


class ChampType(str, Enum):
    text = "text"
    textarea = "textarea"
    number = "number"
    select = "select"
    multiselect = "multiselect"
    checkbox = "checkbox"
    date = "date"
    email = "email"
    phone = "phone"


# ═══════════════════════════════════════════════════════════════════════════════
# CATÉGORIES
# ═══════════════════════════════════════════════════════════════════════════════

class ChampConfig(BaseModel):
    """Configuration d'un champ personnalisé du formulaire."""
    nom: str = Field(..., min_length=1, max_length=50)
    label: str = Field(..., min_length=1, max_length=100)
    type: ChampType = ChampType.text
    requis: bool = False
    options: Optional[List[str]] = None  # Pour select/multiselect
    placeholder: Optional[str] = None
    aide: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    ordre: int = 0


class CategorieBase(BaseModel):
    """Base pour les catégories de demandes."""
    nom: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icone: str = Field(default="report_problem", max_length=50)
    couleur: int = Field(default=4288585374)  # Orange
    actif: bool = True
    ordre_affichage: int = 0
    moderation_requise: bool = False
    delai_traitement_jours: int = Field(default=7, ge=1, le=365)
    photo_obligatoire: bool = False
    photo_max_count: int = Field(default=3, ge=0, le=10)
    champs_config: List[ChampConfig] = Field(default_factory=list)


class CategorieCreate(CategorieBase):
    """Création d'une catégorie."""
    parent_id: Optional[str] = None
    service_defaut_id: Optional[str] = None


class CategorieUpdate(BaseModel):
    """Mise à jour d'une catégorie."""
    nom: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icone: Optional[str] = None
    couleur: Optional[int] = None
    actif: Optional[bool] = None
    ordre_affichage: Optional[int] = None
    moderation_requise: Optional[bool] = None
    delai_traitement_jours: Optional[int] = None
    photo_obligatoire: Optional[bool] = None
    photo_max_count: Optional[int] = None
    champs_config: Optional[List[ChampConfig]] = None
    service_defaut_id: Optional[str] = None


class CategorieResponse(CategorieBase):
    """Réponse catégorie."""
    id: str
    project_id: str
    parent_id: Optional[str] = None
    service_defaut_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategorieArbre(CategorieResponse):
    """Catégorie avec enfants (arborescence)."""
    children: List["CategorieArbre"] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# DEMANDES CITOYENNES
# ═══════════════════════════════════════════════════════════════════════════════

class Coordonnees(BaseModel):
    """Coordonnées GPS."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class DemandeCreatePublic(BaseModel):
    """Création d'une demande par un citoyen (API publique)."""
    categorie_id: str

    # Déclarant
    declarant_email: EmailStr
    declarant_telephone: Optional[str] = Field(None, max_length=20)
    declarant_nom: Optional[str] = Field(None, max_length=100)
    declarant_langue: str = Field(default="fr", max_length=5)

    # Contenu
    description: str = Field(..., min_length=10, max_length=2000)
    champs_supplementaires: Dict[str, Any] = Field(default_factory=dict)

    # Photos (URLs ou base64)
    photos: List[str] = Field(default_factory=list, max_items=5)

    # Localisation
    coordonnees: Optional[Coordonnees] = None
    adresse_approximative: Optional[str] = Field(None, max_length=255)

    # Lien équipement existant (QR code)
    equipement_id: Optional[str] = None

    # Source
    source: DemandeSource = DemandeSource.app_citoyen

    # Anti-spam
    captcha_token: Optional[str] = None

    @validator('declarant_telephone')
    def validate_phone(cls, v):
        if v:
            # Nettoyer le numéro
            cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
            if len(cleaned) < 10:
                raise ValueError('Numéro de téléphone invalide')
            return cleaned
        return v


class DemandeCreateBackoffice(BaseModel):
    """Création d'une demande par un agent backoffice (mail, téléphone, etc.)."""
    categorie_id: str

    # Déclarant (optionnel - appel anonyme possible)
    declarant_email: Optional[EmailStr] = None
    declarant_telephone: Optional[str] = Field(None, max_length=20)
    declarant_nom: Optional[str] = Field(None, max_length=100)

    # Contenu
    description: str = Field(..., min_length=3, max_length=5000)

    # Fichiers (photos + documents)
    photos: List[str] = Field(default_factory=list, max_length=20)
    documents: List[str] = Field(default_factory=list, max_length=10)

    # Localisation
    coordonnees: Optional[Coordonnees] = None
    adresse_approximative: Optional[str] = Field(None, max_length=255)

    # Source et priorité
    source: DemandeSource = DemandeSource.backoffice
    priorite: Optional[DemandePriorite] = None

    # Note interne agent
    note_interne: Optional[str] = Field(None, max_length=2000)

    @validator('declarant_telephone')
    def validate_phone(cls, v):
        if v:
            cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
            if len(cleaned) < 10:
                raise ValueError('Numéro de téléphone invalide')
            return cleaned
        return v


class DemandeUpdateBackoffice(BaseModel):
    """Modification complète d'une demande depuis le backoffice."""
    categorie_id: Optional[str] = None
    declarant_email: Optional[EmailStr] = None
    declarant_telephone: Optional[str] = Field(None, max_length=20)
    declarant_nom: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, min_length=3, max_length=5000)
    photos: Optional[List[str]] = None
    documents: Optional[List[str]] = None
    coordonnees: Optional[Coordonnees] = None
    adresse_approximative: Optional[str] = Field(None, max_length=255)
    source: Optional[DemandeSource] = None
    priorite: Optional[DemandePriorite] = None

    @validator('declarant_telephone')
    def validate_phone(cls, v):
        if v:
            cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
            if len(cleaned) < 10:
                raise ValueError('Numéro de téléphone invalide')
            return cleaned
        return v


class DemandeUpdateAgent(BaseModel):
    """Mise à jour d'une demande par un agent."""
    statut: Optional[DemandeStatut] = None
    priorite: Optional[DemandePriorite] = None
    service_assigne_id: Optional[str] = None
    agent_assigne_id: Optional[str] = None
    date_planification: Optional[datetime] = None

    # Commentaire/réponse
    commentaire: Optional[str] = Field(None, max_length=2000)
    commentaire_interne: bool = False
    envoyer_email: bool = False


class DemandeResponse(BaseModel):
    """Réponse demande complète."""
    id: str
    project_id: str
    numero_suivi: str

    # Catégorie
    categorie_id: str
    categorie_nom: Optional[str] = None
    categorie_icone: Optional[str] = None
    categorie_couleur: Optional[int] = None
    categorie_parent_nom: Optional[str] = None

    # Déclarant
    declarant_email: str
    declarant_telephone: Optional[str] = None
    declarant_nom: Optional[str] = None
    declarant_langue: str = "fr"

    # Contenu
    description: str
    champs_supplementaires: Dict[str, Any] = Field(default_factory=dict)
    photos: List[str] = Field(default_factory=list)
    documents: List[str] = Field(default_factory=list)
    photos_intervention: List[str] = Field(default_factory=list)

    # Localisation
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    adresse_approximative: Optional[str] = None
    quartier_id: Optional[str] = None
    quartier_nom: Optional[str] = None

    # Lien équipement
    equipement_id: Optional[str] = None

    # Workflow
    statut: DemandeStatut
    priorite: DemandePriorite
    service_assigne_id: Optional[str] = None
    service_assigne_nom: Optional[str] = None
    service_assigne_couleur: Optional[str] = None
    agent_assigne_id: Optional[str] = None
    agent_assigne_nom: Optional[str] = None
    agent_service_id: Optional[str] = None
    agent_service_nom: Optional[str] = None

    # Dates
    created_at: datetime
    updated_at: datetime
    date_prise_en_charge: Optional[datetime] = None
    date_planification: Optional[datetime] = None
    date_resolution: Optional[datetime] = None
    date_cloture: Optional[datetime] = None

    # Métadonnées
    source: DemandeSource
    heures_depuis_creation: Optional[float] = None

    # Messages tchat
    messages_non_lus: int = 0

    class Config:
        from_attributes = True


class DemandeResponsePublic(BaseModel):
    """Réponse demande pour le citoyen (données limitées)."""
    numero_suivi: str
    statut: DemandeStatut
    categorie_nom: Optional[str] = None
    description: str
    created_at: datetime
    updated_at: datetime
    date_planification: Optional[datetime] = None
    date_resolution: Optional[datetime] = None

    class Config:
        from_attributes = True


class DemandeListResponse(BaseModel):
    """Liste paginée de demandes."""
    demandes: List[DemandeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ═══════════════════════════════════════════════════════════════════════════════
# HISTORIQUE
# ═══════════════════════════════════════════════════════════════════════════════

class HistoriqueCreate(BaseModel):
    """Création d'une entrée d'historique."""
    action: HistoriqueAction
    commentaire: Optional[str] = Field(None, max_length=2000)
    commentaire_interne: bool = False
    envoyer_email: bool = False


class HistoriqueResponse(BaseModel):
    """Réponse historique."""
    id: str
    demande_id: str
    agent_id: Optional[str] = None
    agent_nom: Optional[str] = None
    action: HistoriqueAction
    ancien_statut: Optional[str] = None
    nouveau_statut: Optional[str] = None
    commentaire: Optional[str] = None
    commentaire_interne: bool = False
    email_envoye: bool = False
    email_sujet: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPLATES DE RÉPONSES
# ═══════════════════════════════════════════════════════════════════════════════

class TemplateBase(BaseModel):
    """Base pour les templates de réponse."""
    titre: str = Field(..., min_length=1, max_length=100)
    contenu: str = Field(..., min_length=1, max_length=2000)
    categorie_id: Optional[str] = None
    statut_cible: Optional[DemandeStatut] = None
    actif: bool = True
    ordre_affichage: int = 0
    langue: str = Field(default="fr", max_length=5)


class TemplateCreate(TemplateBase):
    """Création d'un template."""
    pass


class TemplateUpdate(BaseModel):
    """Mise à jour d'un template."""
    titre: Optional[str] = Field(None, min_length=1, max_length=100)
    contenu: Optional[str] = Field(None, min_length=1, max_length=2000)
    categorie_id: Optional[str] = None
    statut_cible: Optional[DemandeStatut] = None
    actif: Optional[bool] = None
    ordre_affichage: Optional[int] = None
    langue: Optional[str] = None


class TemplateResponse(TemplateBase):
    """Réponse template."""
    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# QUARTIERS
# ═══════════════════════════════════════════════════════════════════════════════

class QuartierBase(BaseModel):
    """Base pour les quartiers."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: int = Field(default=4280391411)  # Teal
    population: Optional[int] = Field(None, ge=0)
    code_iris: Optional[str] = Field(None, max_length=20)
    code_insee: Optional[str] = Field(None, max_length=10)


class QuartierCreate(QuartierBase):
    """Création d'un quartier."""
    coordinates: List[Coordonnees] = Field(..., min_items=3)


class QuartierResponse(QuartierBase):
    """Réponse quartier."""
    id: str
    project_id: Optional[str] = None
    perimetre_type: str = "quartier"
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Statistiques
    total_demandes: Optional[int] = None
    demandes_en_cours: Optional[int] = None

    class Config:
        from_attributes = True


class QuartierWithGeometry(QuartierResponse):
    """Quartier avec géométrie complète."""
    coordinates: List[Coordonnees] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# STATISTIQUES
# ═══════════════════════════════════════════════════════════════════════════════

class StatsGlobales(BaseModel):
    """Statistiques globales des demandes."""
    total: int = 0
    nouvelles: int = 0
    en_cours: int = 0
    traitees: int = 0
    rejetees: int = 0
    temps_moyen_traitement_heures: Optional[float] = None


class StatsParCategorie(BaseModel):
    """Statistiques par catégorie."""
    categorie_id: str
    categorie_nom: str
    total: int = 0
    nouvelles: int = 0
    en_cours: int = 0
    traitees: int = 0
    temps_moyen_heures: Optional[float] = None


class StatsParQuartier(BaseModel):
    """Statistiques par quartier."""
    quartier_id: str
    quartier_nom: str
    total: int = 0
    nouvelles: int = 0
    en_cours: int = 0
    traitees: int = 0
    temps_moyen_heures: Optional[float] = None


class StatsParPeriode(BaseModel):
    """Statistiques par période."""
    date: date
    total: int = 0
    nouvelles: int = 0
    traitees: int = 0


class StatsResponse(BaseModel):
    """Réponse statistiques complètes."""
    globales: StatsGlobales
    par_categorie: List[StatsParCategorie] = Field(default_factory=list)
    par_quartier: List[StatsParQuartier] = Field(default_factory=list)
    evolution: List[StatsParPeriode] = Field(default_factory=list)
    periode_debut: date
    periode_fin: date


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD STATS
# ═══════════════════════════════════════════════════════════════════════════════

class StatsParService(BaseModel):
    """Statistiques par service."""
    service_id: str
    service_nom: str
    service_couleur: Optional[str] = None
    total: int = 0
    temps_moyen_jours: Optional[float] = None


class DemandePrioritaire(BaseModel):
    """Demande prioritaire pour le dashboard."""
    id: str
    numero_suivi: str
    categorie_nom: Optional[str] = None
    service_nom: Optional[str] = None
    description: str
    priorite: str
    statut: str
    created_at: datetime
    jours_attente: int
    est_urgente: bool
    est_en_retard: bool
    rappel_envoye: bool = False


class ComparaisonPeriode(BaseModel):
    """Comparaison entre deux périodes."""
    ce_mois: int = 0
    mois_precedent: int = 0
    variation_pct: Optional[float] = None  # % de variation


class DistributionStatuts(BaseModel):
    """Distribution des demandes par statut."""
    nouveau: int = 0
    en_moderation: int = 0
    envoye: int = 0
    accepte: int = 0
    en_cours: int = 0
    planifie: int = 0
    traite: int = 0
    cloture: int = 0
    rejete: int = 0


class DashboardStats(BaseModel):
    """Statistiques complètes pour le dashboard."""
    # KPIs
    total: int = 0
    nouvelles: int = 0
    urgentes: int = 0
    traitees_mois: int = 0
    delai_moyen_jours: Optional[float] = None

    # KPIs dirigeant
    taux_resolution_pct: Optional[float] = None
    en_cours: int = 0
    rejetees: int = 0
    delai_moyen_mois_precedent: Optional[float] = None
    comparaison_volume: Optional[ComparaisonPeriode] = None
    comparaison_traitees: Optional[ComparaisonPeriode] = None
    distribution_statuts: Optional[DistributionStatuts] = None

    # Données pour graphiques
    par_categorie: List[StatsParCategorie] = Field(default_factory=list)
    par_service: List[StatsParService] = Field(default_factory=list)
    evolution_30j: List[StatsParPeriode] = Field(default_factory=list)
    evolution_12m: List[StatsParPeriode] = Field(default_factory=list)

    # Demandes prioritaires
    prioritaires: List[DemandePrioritaire] = Field(default_factory=list)

    # Config
    delai_retard_jours: int = 5


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION EMAIL
# ═══════════════════════════════════════════════════════════════════════════════

class EmailConfigBase(BaseModel):
    """Configuration email."""
    smtp_host: Optional[str] = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_user: Optional[str] = None
    smtp_use_tls: bool = True
    email_from: Optional[EmailStr] = None
    email_from_name: Optional[str] = Field(None, max_length=100)
    email_reply_to: Optional[EmailStr] = None
    envoyer_notifications: bool = True


class EmailConfigCreate(EmailConfigBase):
    """Création config email."""
    smtp_password: Optional[str] = None
    template_nouveau: Optional[str] = None
    template_pris_en_charge: Optional[str] = None
    template_planifie: Optional[str] = None
    template_traite: Optional[str] = None
    template_rejete: Optional[str] = None


class EmailConfigResponse(EmailConfigBase):
    """Réponse config email (sans mot de passe)."""
    id: str
    project_id: str
    smtp_password_set: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# DOUBLONS
# ═══════════════════════════════════════════════════════════════════════════════

class DoublonCheck(BaseModel):
    """Requête de vérification de doublons."""
    categorie_id: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    rayon_metres: int = Field(default=50, ge=10, le=500)
    jours: int = Field(default=30, ge=1, le=365)


class DoublonPotentiel(BaseModel):
    """Doublon potentiel détecté."""
    id: str
    numero_suivi: str
    description: str
    statut: str
    distance_metres: float
    created_at: datetime
    declarant_email: str
    photos: List[str] = Field(default_factory=list)
    score_similarite: int = Field(default=0, ge=0, le=100)


class DoublonCheckResponse(BaseModel):
    """Réponse vérification de doublons."""
    doublons_trouves: int
    doublons: List[DoublonPotentiel] = Field(default_factory=list)
    message: str


class DoublonMarquer(BaseModel):
    """Marquer une demande comme doublon."""
    doublon_de_id: str
    commentaire: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# IMPORT IRIS
# ═══════════════════════════════════════════════════════════════════════════════

class IRISImportRequest(BaseModel):
    """Requête d'import IRIS."""
    code_commune: str = Field(..., min_length=5, max_length=5, pattern=r"^\d{5}$")
    remplacer_existants: bool = False


class IRISImportResponse(BaseModel):
    """Réponse import IRIS."""
    success: bool
    quartiers_importes: int = 0
    quartiers_ignores: int = 0
    errors: List[str] = Field(default_factory=list)
    message: str


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICES MUNICIPAUX
# ═══════════════════════════════════════════════════════════════════════════════

class ServiceBase(BaseModel):
    """Base pour les services municipaux."""
    nom: str = Field(..., min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone: Optional[str] = Field(None, max_length=20)
    responsable_nom: Optional[str] = Field(None, max_length=100)
    actif: bool = True
    ordre_affichage: int = 0
    couleur: str = Field(default="#3b82f6", pattern=r"^#[0-9a-fA-F]{6}$")
    icone: str = Field(default="business", max_length=50)
    notifier_nouvelle_demande: bool = True
    notifier_changement_statut: bool = False
    emails_notification: List[str] = Field(default_factory=list)


class ServiceCreate(ServiceBase):
    """Création d'un service."""
    pass


class ServiceUpdate(BaseModel):
    """Mise à jour d'un service."""
    nom: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    telephone: Optional[str] = Field(None, max_length=20)
    responsable_nom: Optional[str] = Field(None, max_length=100)
    actif: Optional[bool] = None
    ordre_affichage: Optional[int] = None
    couleur: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    icone: Optional[str] = Field(None, max_length=50)
    notifier_nouvelle_demande: Optional[bool] = None
    notifier_changement_statut: Optional[bool] = None
    emails_notification: Optional[List[str]] = None


class ServiceResponse(ServiceBase):
    """Réponse service."""
    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime
    # Stats optionnelles
    total_demandes: Optional[int] = None
    demandes_en_cours: Optional[int] = None

    class Config:
        from_attributes = True


class ServiceAgentRole(str, Enum):
    responsable = "responsable"
    agent = "agent"


class ServiceAgentBase(BaseModel):
    """Base agent de service."""
    role: ServiceAgentRole = ServiceAgentRole.agent
    peut_assigner: bool = False
    recoit_notifications: bool = True


class ServiceAgentCreate(BaseModel):
    """Création d'un agent de service avec authentification propre."""
    email: str
    password: str
    nom: str
    prenom: str
    telephone: Optional[str] = None
    role: ServiceAgentRole = ServiceAgentRole.agent
    peut_assigner: bool = False
    recoit_notifications: bool = True


class ServiceAgentUpdate(BaseModel):
    """Modification d'un agent."""
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    role: Optional[ServiceAgentRole] = None
    peut_assigner: Optional[bool] = None
    recoit_notifications: Optional[bool] = None
    actif: Optional[bool] = None


class ServiceAgentResponse(BaseModel):
    """Réponse agent de service."""
    id: str
    service_id: str
    email: Optional[str] = None
    nom: Optional[str] = None
    prenom: Optional[str] = None
    nom_complet: str
    telephone: Optional[str] = None
    role: ServiceAgentRole
    peut_assigner: bool = False
    recoit_notifications: bool = True
    actif: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ServiceAgentResetPassword(BaseModel):
    """Reset mot de passe par admin."""
    new_password: str


class ServiceStatsResponse(BaseModel):
    """Statistiques d'un service."""
    service_id: str
    service_nom: str
    service_code: Optional[str] = None
    service_couleur: str
    total_demandes: int = 0
    nouvelles: int = 0
    a_traiter: int = 0
    en_cours: int = 0
    traitees: int = 0
    cloturees: int = 0
    temps_moyen_heures: Optional[float] = None


# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGES TCHAT (DEMANDES ↔ SERVICE TERRAIN)
# ═══════════════════════════════════════════════════════════════════════════════

class MessageSenderType(str, Enum):
    service = "service"
    demandes = "demandes"
    terrain = "terrain"


class MessageCreate(BaseModel):
    """Création d'un message tchat."""
    message: str = Field(..., min_length=1, max_length=2000)


class MessageResponse(BaseModel):
    """Réponse message tchat."""
    id: str
    demande_id: str
    sender_type: MessageSenderType
    sender_id: Optional[str] = None
    sender_nom: str
    message: str
    lu_par_service: bool = False
    lu_par_demandes: bool = False
    created_at: datetime

    class Config:
        from_attributes = True



# Pour les références circulaires
CategorieArbre.model_rebuild()
