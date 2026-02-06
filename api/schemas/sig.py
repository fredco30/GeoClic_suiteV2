"""
Schémas Pydantic pour l'intégration SIG Desktop.
Format B compatible avec le SIG existant + extensions.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES ÉNUMÉRÉS
# ═══════════════════════════════════════════════════════════════════════════════

class GeomType(str, Enum):
    POINT = "POINT"
    LINESTRING = "LINESTRING"
    POLYGON = "POLYGON"


class PointStatus(str, Enum):
    PROJET = "Projet"
    EN_COURS = "En cours"
    REALISE = "Réalisé"
    A_FAIRE = "À faire"


class ConditionState(str, Enum):
    NEUF = "Neuf"
    TRES_BON = "Très bon"
    BON = "Bon"
    MOYEN = "Moyen"
    MAUVAIS = "Mauvais"
    HORS_SERVICE = "Hors service"


# ═══════════════════════════════════════════════════════════════════════════════
# FORMAT B - TYPES (Compatible SIG Desktop existant)
# ═══════════════════════════════════════════════════════════════════════════════

class TypeFormatB(BaseModel):
    """Format B utilisé par le SIG Desktop pour les types de points."""
    type: str = Field(..., description="Nom du type principal")
    subtypes: List[str] = Field(default_factory=list, description="Sous-types associés")
    colorValue: int = Field(default=4280391411, description="Couleur Flutter (ARGB)")
    iconName: str = Field(default="location_on", description="Nom de l'icône")


class TypeSyncRequest(BaseModel):
    """Requête de synchronisation des types depuis le SIG Desktop."""
    project_id: str = Field(..., description="UUID du projet")
    types: List[TypeFormatB] = Field(..., description="Liste des types à synchroniser")
    replace_all: bool = Field(default=False, description="Remplacer tous les types existants")


class TypeSyncResponse(BaseModel):
    """Réponse de synchronisation des types."""
    success: bool
    types_count: int
    subtypes_count: int
    version: int
    message: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# LEXIQUE - FORMAT COMPLET 6 NIVEAUX
# ═══════════════════════════════════════════════════════════════════════════════

class LexiqueEntry(BaseModel):
    """Entrée de lexique complète."""
    id: Optional[int] = None
    code: str
    label: str
    parent_code: Optional[str] = None
    project_id: Optional[str] = None
    level: int = 0
    display_order: int = 0
    icon_name: Optional[str] = None
    color_value: Optional[int] = None
    is_active: bool = True
    triggers_form: bool = False
    form_type_ref: Optional[str] = None
    children: List["LexiqueEntry"] = Field(default_factory=list)

    class Config:
        from_attributes = True


class LexiqueTreeResponse(BaseModel):
    """Arbre complet du lexique pour un projet."""
    project_id: str
    entries: List[LexiqueEntry]
    version: str
    last_updated: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# CHAMPS DYNAMIQUES
# ═══════════════════════════════════════════════════════════════════════════════

class FieldConfig(BaseModel):
    """Configuration d'un champ dynamique."""
    id: Optional[int] = None
    type_name: str
    field_name: str
    field_label: str
    field_type: str = "text"  # text, number, dropdown, date, checkbox, photo
    is_required: bool = False
    dropdown_options: Optional[List[str]] = None
    default_value: Optional[str] = None
    display_order: int = 0
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    help_text: Optional[str] = None
    project_id: Optional[str] = None

    class Config:
        from_attributes = True


class FieldConfigSyncRequest(BaseModel):
    """Requête de synchronisation des champs dynamiques."""
    project_id: str
    configs: List[FieldConfig]
    replace_all: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# PROJETS
# ═══════════════════════════════════════════════════════════════════════════════

class ProjectCreate(BaseModel):
    """Création d'un projet depuis le SIG."""
    name: str
    description: Optional[str] = None
    collectivite_name: Optional[str] = None
    min_lat: Optional[float] = None
    max_lat: Optional[float] = None
    min_lng: Optional[float] = None
    max_lng: Optional[float] = None


class ProjectResponse(BaseModel):
    """Réponse projet."""
    id: str
    name: str
    description: Optional[str] = None
    status: str = "En cours"
    is_active: bool = True
    is_system: bool = False
    collectivite_name: Optional[str] = None
    min_lat: Optional[float] = None
    max_lat: Optional[float] = None
    min_lng: Optional[float] = None
    max_lng: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Liste des projets."""
    projects: List[ProjectResponse]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# POINTS (Format SIG Desktop compatible)
# ═══════════════════════════════════════════════════════════════════════════════

class CoordinateSIG(BaseModel):
    """Coordonnée GPS."""
    latitude: float
    longitude: float
    altitude: Optional[float] = None


class PointSIG(BaseModel):
    """Point au format SIG Desktop."""
    id: Optional[str] = None
    name: str
    type: str
    subtype: Optional[str] = None
    condition: str = "Neuf"
    status: str = "Projet"
    comment: Optional[str] = None
    zone_name: Optional[str] = None
    geom_type: GeomType = GeomType.POINT
    coordinates: List[CoordinateSIG]
    gps_precision: Optional[float] = None
    gps_source: Optional[str] = "Desktop"
    image_path: Optional[str] = None
    # Champs techniques
    materiau: Optional[str] = None
    hauteur: Optional[float] = None
    largeur: Optional[float] = None
    date_installation: Optional[datetime] = None
    duree_vie_annees: Optional[int] = None
    marque_modele: Optional[str] = None
    # Maintenance
    date_derniere_intervention: Optional[datetime] = None
    date_prochaine_intervention: Optional[datetime] = None
    priorite: Optional[str] = None
    cout_remplacement: Optional[float] = None
    # Custom
    custom_properties: Optional[Dict[str, Any]] = None
    # Métadonnées
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    project_id: Optional[str] = None
    lexique_code: Optional[str] = None

    class Config:
        from_attributes = True


class PointSyncRequest(BaseModel):
    """Requête de synchronisation de points depuis le SIG."""
    project_id: str
    zone_name: Optional[str] = None
    points: List[PointSIG]


class PointSyncResponse(BaseModel):
    """Réponse de synchronisation de points."""
    success: bool
    uploaded: int
    updated: int
    failed: int
    errors: List[str] = Field(default_factory=list)
    server_ids: Dict[str, str] = Field(default_factory=dict, description="Mapping local_id -> server_id")


# ═══════════════════════════════════════════════════════════════════════════════
# QR CODES - SHORT CODES
# ═══════════════════════════════════════════════════════════════════════════════

class ShortCodeCreate(BaseModel):
    """Création d'un short code pour QR."""
    point_id: str


class ShortCodeResponse(BaseModel):
    """Réponse short code."""
    short_code: str
    point_id: str
    url: str
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# STATUT ET SYNCHRONISATION
# ═══════════════════════════════════════════════════════════════════════════════

class SyncStatusResponse(BaseModel):
    """Statut de synchronisation global."""
    current_version: int
    types_count: int
    points_count: int
    last_updated: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    last_sync_status: str = "unknown"


class OfflinePackage(BaseModel):
    """Package complet pour mode offline."""
    server_time: datetime
    project: ProjectResponse
    lexique_version: str
    lexique_entries: List[LexiqueEntry]
    field_configs: List[FieldConfig]
    points: List[PointSIG]
    total_points: int


# ═══════════════════════════════════════════════════════════════════════════════
# PÉRIMÈTRES
# ═══════════════════════════════════════════════════════════════════════════════

class PerimetreCreate(BaseModel):
    """Création d'un périmètre."""
    name: str
    description: Optional[str] = None
    coordinates: List[CoordinateSIG]
    color: Optional[int] = 4280391411
    zone_name: Optional[str] = None


class PerimetreResponse(BaseModel):
    """Réponse périmètre."""
    id: int
    name: str
    description: Optional[str] = None
    wkt: str
    color: int
    zone_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSION FORMAT B <-> LEXIQUE
# ═══════════════════════════════════════════════════════════════════════════════

def format_b_to_lexique(types: List[TypeFormatB], project_id: str) -> List[LexiqueEntry]:
    """
    Convertit une liste de types Format B en entrées de lexique.
    Le Format B a 2 niveaux (type + subtypes), on les mappe vers niveau 0 et 1.
    """
    entries = []

    for i, t in enumerate(types):
        # Niveau 0 : Type principal
        type_code = t.type.upper().replace(" ", "_").replace("'", "")
        parent_entry = LexiqueEntry(
            code=type_code,
            label=t.type,
            parent_code=None,
            project_id=project_id,
            level=0,
            display_order=i,
            icon_name=t.iconName,
            color_value=t.colorValue,
            triggers_form=len(t.subtypes) == 0,  # Si pas de sous-types, déclenche le form
        )
        entries.append(parent_entry)

        # Niveau 1 : Sous-types
        for j, subtype in enumerate(t.subtypes):
            subtype_code = f"{type_code}_{subtype.upper().replace(' ', '_').replace(chr(39), '')}"
            child_entry = LexiqueEntry(
                code=subtype_code,
                label=subtype,
                parent_code=type_code,
                project_id=project_id,
                level=1,
                display_order=j,
                icon_name=t.iconName,
                color_value=t.colorValue,
                triggers_form=True,  # Les sous-types déclenchent le form
            )
            entries.append(child_entry)

    return entries


def lexique_to_format_b(entries: List[LexiqueEntry]) -> List[TypeFormatB]:
    """
    Convertit des entrées de lexique en Format B.
    Regroupe les niveaux 0 avec leurs enfants niveau 1.
    """
    # Grouper par parent
    parents = [e for e in entries if e.level == 0]
    children_map = {}

    for e in entries:
        if e.parent_code:
            if e.parent_code not in children_map:
                children_map[e.parent_code] = []
            children_map[e.parent_code].append(e.label)

    types = []
    for p in parents:
        types.append(TypeFormatB(
            type=p.label,
            subtypes=children_map.get(p.code, []),
            colorValue=p.color_value or 4280391411,
            iconName=p.icon_name or "location_on",
        ))

    return types
