"""
Schémas Pydantic pour le portail citoyen public.
Endpoints sans authentification pour consultation et signalements.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES ÉNUMÉRÉS
# ═══════════════════════════════════════════════════════════════════════════════

class SignalementUrgence(str, Enum):
    FAIBLE = "faible"
    NORMAL = "normal"
    URGENT = "urgent"
    CRITIQUE = "critique"


class SignalementStatut(str, Enum):
    NOUVEAU = "nouveau"
    PRIS_EN_COMPTE = "pris_en_compte"
    EN_COURS = "en_cours"
    TRAITE = "traite"
    REJETE = "rejete"
    ARCHIVE = "archive"


class TypeProbleme(str, Enum):
    DEGRADATION = "Dégradation"
    PANNE = "Panne"
    DANGER = "Danger"
    PROPRETE = "Propreté"
    ACCESSIBILITE = "Accessibilité"
    AUTRE = "Autre"


# ═══════════════════════════════════════════════════════════════════════════════
# ÉQUIPEMENT PUBLIC (Vue simplifiée pour les citoyens)
# ═══════════════════════════════════════════════════════════════════════════════

class PhotoPublic(BaseModel):
    """Photo visible publiquement."""
    url: str
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None


class EquipmentPublic(BaseModel):
    """
    Vue publique d'un équipement.
    Champs limités selon la configuration de visibilité.
    """
    id: str
    short_code: Optional[str] = None
    name: str
    category: str  # Label du type (pas le code)
    subcategory: Optional[str] = None
    photos: List[PhotoPublic] = Field(default_factory=list)
    condition: Optional[str] = None  # Si visible
    location: Optional[str] = None  # Adresse ou zone
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Champs custom visibles (selon config)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    # Métadonnées
    last_updated: Optional[datetime] = None
    can_report: bool = True  # Peut-on signaler un problème ?


class EquipmentListResponse(BaseModel):
    """Liste d'équipements pour la carte publique."""
    equipments: List[EquipmentPublic]
    total: int
    page: int
    page_size: int


# ═══════════════════════════════════════════════════════════════════════════════
# SIGNALEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

class SignalementCreate(BaseModel):
    """
    Création d'un signalement par un citoyen.
    Email ou téléphone requis.
    """
    # Point concerné (optionnel si nouvelle localisation)
    point_id: Optional[str] = None
    short_code: Optional[str] = None  # Alternative au point_id

    # Informations du signalement
    type_probleme: TypeProbleme
    description: str = Field(..., min_length=10, max_length=2000)
    urgence: SignalementUrgence = SignalementUrgence.NORMAL

    # Contact (au moins un requis)
    email: Optional[EmailStr] = None
    telephone: Optional[str] = None
    nom_signalant: Optional[str] = None

    # Localisation (si pas de point_id)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    adresse: Optional[str] = None

    # Photos (base64 ou URLs)
    photos: List[str] = Field(default_factory=list, max_length=5)

    @validator('telephone')
    def validate_contact(cls, v, values):
        """Vérifie qu'au moins email ou téléphone est fourni."""
        email = values.get('email')
        if not email and not v:
            raise ValueError('Email ou téléphone requis')
        return v

    @validator('latitude')
    def validate_location(cls, v, values):
        """Vérifie la cohérence de la localisation."""
        point_id = values.get('point_id')
        short_code = values.get('short_code')
        if not point_id and not short_code and v is None:
            raise ValueError('Localisation requise si pas de point existant')
        return v


class SignalementResponse(BaseModel):
    """Réponse après création d'un signalement."""
    id: str
    numero_suivi: str  # Numéro lisible pour le citoyen (ex: SIG-2024-00123)
    statut: SignalementStatut
    message: str
    created_at: datetime


class SignalementStatusResponse(BaseModel):
    """Statut d'un signalement (consultation par le citoyen)."""
    id: str
    numero_suivi: str
    type_probleme: str
    description: str
    statut: SignalementStatut
    statut_label: str  # Label lisible
    commentaire_public: Optional[str] = None  # Réponse de la mairie
    created_at: datetime
    updated_at: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# CATÉGORIES PUBLIQUES
# ═══════════════════════════════════════════════════════════════════════════════

class CategoryPublic(BaseModel):
    """Catégorie visible publiquement."""
    code: str
    label: str
    icon: Optional[str] = None
    color: Optional[str] = None  # Format hex
    children: List["CategoryPublic"] = Field(default_factory=list)


class CategoriesResponse(BaseModel):
    """Liste des catégories pour filtrage."""
    categories: List[CategoryPublic]


# ═══════════════════════════════════════════════════════════════════════════════
# CARTE PUBLIQUE
# ═══════════════════════════════════════════════════════════════════════════════

class MapMarker(BaseModel):
    """Marqueur sur la carte publique."""
    id: str
    short_code: Optional[str] = None
    name: str
    category: str
    latitude: float
    longitude: float
    icon: Optional[str] = None
    color: Optional[str] = None


class MapBounds(BaseModel):
    """Limites de la carte."""
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float


class MapDataResponse(BaseModel):
    """Données pour affichage sur la carte."""
    markers: List[MapMarker]
    bounds: Optional[MapBounds] = None
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def generate_tracking_number() -> str:
    """Génère un numéro de suivi lisible pour les signalements."""
    from datetime import datetime
    import random
    year = datetime.now().year
    num = random.randint(10000, 99999)
    return f"SIG-{year}-{num}"


def int_to_hex_color(color_int: Optional[int]) -> Optional[str]:
    """Convertit une couleur entière en format hex."""
    if color_int is None:
        return None
    # Extraire RGB (ignorer alpha si présent)
    r = (color_int >> 16) & 0xFF
    g = (color_int >> 8) & 0xFF
    b = color_int & 0xFF
    return f"#{r:02x}{g:02x}{b:02x}"


STATUT_LABELS = {
    SignalementStatut.NOUVEAU: "En attente de traitement",
    SignalementStatut.PRIS_EN_COMPTE: "Pris en compte",
    SignalementStatut.EN_COURS: "Traitement en cours",
    SignalementStatut.TRAITE: "Traité",
    SignalementStatut.REJETE: "Rejeté",
    SignalementStatut.ARCHIVE: "Archivé",
}
