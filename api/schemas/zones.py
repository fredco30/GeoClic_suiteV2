"""
Schémas Pydantic pour la gestion des zones géographiques hiérarchiques.

Structure hiérarchique:
- Level 1: Commune (racine)
- Level 2: Quartier / IRIS
- Level 3: Secteur

Note: On utilise 'zone_type' dans l'API pour compatibilité, mais 'perimetre_type' en DB.
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class ZoneBase(BaseModel):
    """Schéma de base pour une zone."""
    name: str = Field(..., min_length=1, max_length=255, description="Nom de la zone")
    code: Optional[str] = Field(None, max_length=50, description="Code unique de la zone")
    zone_type: Optional[str] = Field("quartier", description="Type de zone: commune, quartier, secteur, iris")
    metadata: Optional[dict] = Field(default_factory=dict, description="Métadonnées additionnelles")
    # Nouveaux champs hiérarchiques
    level: Optional[int] = Field(2, ge=1, le=3, description="Niveau: 1=Commune, 2=Quartier, 3=Secteur")
    parent_id: Optional[str] = Field(None, description="ID de la zone parente")
    is_global: Optional[bool] = Field(False, description="Zone partagée par tous les projets")
    project_id: Optional[str] = Field(None, description="ID du projet (NULL si globale)")


class ZoneCreate(ZoneBase):
    """Schéma pour créer une zone avec géométrie."""
    geojson: dict = Field(..., description="Géométrie au format GeoJSON (Polygon)")
    # Champs optionnels pour l'import
    population: Optional[int] = Field(None, description="Population de la zone")
    code_iris: Optional[str] = Field(None, max_length=20, description="Code IRIS INSEE")
    code_insee: Optional[str] = Field(None, max_length=10, description="Code INSEE commune")


class ZoneUpdate(BaseModel):
    """Schéma pour mettre à jour une zone."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    zone_type: Optional[str] = None
    metadata: Optional[dict] = None
    geojson: Optional[dict] = Field(None, description="Nouvelle géométrie au format GeoJSON")
    # Champs hiérarchiques modifiables
    level: Optional[int] = Field(None, ge=1, le=3)
    parent_id: Optional[str] = None
    is_global: Optional[bool] = None
    project_id: Optional[str] = None
    population: Optional[int] = None
    code_iris: Optional[str] = None
    code_insee: Optional[str] = None


class ZoneResponse(ZoneBase):
    """Réponse pour une zone (sans géométrie)."""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    point_count: int = Field(0, description="Nombre de points dans cette zone")
    # Infos parent
    parent_name: Optional[str] = Field(None, description="Nom de la zone parente")
    # Champs additionnels
    population: Optional[int] = None
    code_iris: Optional[str] = None
    code_insee: Optional[str] = None

    class Config:
        from_attributes = True


class ZoneWithGeometry(ZoneResponse):
    """Réponse pour une zone avec sa géométrie GeoJSON."""
    geojson: Optional[dict] = Field(None, description="Géométrie au format GeoJSON")
    bbox: Optional[List[float]] = Field(None, description="Bounding box [minLng, minLat, maxLng, maxLat]")


class ZoneHierarchyItem(BaseModel):
    """Élément dans une hiérarchie de zones."""
    id: str
    name: str
    code: Optional[str] = None
    zone_type: str
    level: int
    parent_id: Optional[str] = None
    parent_name: Optional[str] = None
    is_global: bool = False
    project_id: Optional[str] = None
    children: List["ZoneHierarchyItem"] = Field(default_factory=list)
    # Stats optionnelles
    total_demandes: Optional[int] = None
    children_count: Optional[int] = None


# Nécessaire pour la référence récursive
ZoneHierarchyItem.model_rebuild()


class ZoneHierarchyResponse(BaseModel):
    """Réponse pour la hiérarchie complète des zones."""
    zones: List[ZoneHierarchyItem]
    total_count: int


class ZoneChildrenResponse(BaseModel):
    """Réponse pour les enfants d'une zone."""
    parent_id: str
    parent_name: str
    children: List[ZoneResponse]


class ZoneStatsResponse(BaseModel):
    """Statistiques d'une zone."""
    zone_id: str
    zone_name: str
    level: int
    zone_type: str
    parent_id: Optional[str] = None
    parent_name: Optional[str] = None
    # Stats directes
    total_demandes: int = 0
    nouvelles: int = 0
    acceptees: int = 0
    en_cours: int = 0
    traitees: int = 0
    rejetees: int = 0
    temps_moyen_heures: Optional[float] = None
    # Stats avec enfants (optionnel)
    total_avec_enfants: Optional[int] = None


class ZoneGeoJSON(BaseModel):
    """Zone au format GeoJSON Feature."""
    type: str = "Feature"
    id: str
    properties: dict
    geometry: dict


class ZonesGeoJSONCollection(BaseModel):
    """Collection de zones au format GeoJSON FeatureCollection."""
    type: str = "FeatureCollection"
    features: List[ZoneGeoJSON]


class IRISImportRequest(BaseModel):
    """Requête pour importer des zones IRIS."""
    code_commune: str = Field(..., min_length=5, max_length=5, description="Code INSEE de la commune (5 chiffres)")
    remplacer_existants: bool = Field(False, description="Supprimer les zones existantes avec le même code INSEE")
    project_id: Optional[str] = Field(None, description="ID du projet (NULL = zones globales)")


class IRISImportResponse(BaseModel):
    """Réponse après import IRIS."""
    success: bool
    commune_id: Optional[str] = Field(None, description="ID de la commune créée")
    zones_importees: int = 0
    zones_ignorees: int = 0
    message: str = ""
    errors: List[str] = Field(default_factory=list)


class ZoneOverlapCheck(BaseModel):
    """Résultat de vérification de chevauchement."""
    has_overlap: bool
    overlapping_zones: List[str] = Field(default_factory=list, description="Noms des zones qui chevauchent")


class ZonePointHierarchy(BaseModel):
    """Hiérarchie de zones pour un point GPS."""
    zone_id: str
    zone_name: str
    zone_level: int
    zone_type: str
    zone_parent_id: Optional[str] = None
