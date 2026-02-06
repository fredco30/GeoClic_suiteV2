"""
Router pour les champs dynamiques.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
from enum import Enum
import json

from database import get_db
from routers.auth import get_current_user

router = APIRouter()


class ChampType(str, Enum):
    text = "text"
    number = "number"
    date = "date"
    select = "select"
    multiselect = "multiselect"
    photo = "photo"
    file = "file"
    geometry = "geometry"
    slider = "slider"
    color = "color"
    signature = "signature"
    qrcode = "qrcode"
    calculated = "calculated"


class ChampCreate(BaseModel):
    lexique_id: str
    nom: str
    type: ChampType
    obligatoire: bool = False
    ordre: int = 0
    options: Optional[List[str]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    formule: Optional[str] = None
    actif: bool = True
    project_id: Optional[str] = None  # ID du projet pour isolation
    # Options avancées
    default_value: Optional[str] = None
    display_mode: Optional[str] = "auto"  # auto, dropdown, search_select
    search_threshold: Optional[int] = 10
    condition_field: Optional[str] = None
    condition_operator: Optional[str] = "="  # =, !=, in
    condition_value: Optional[List[str]] = None


class ChampUpdate(BaseModel):
    nom: Optional[str] = None
    type: Optional[ChampType] = None
    obligatoire: Optional[bool] = None
    ordre: Optional[int] = None
    options: Optional[List[str]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    formule: Optional[str] = None
    actif: Optional[bool] = None
    # Options avancées
    default_value: Optional[str] = None
    display_mode: Optional[str] = None
    search_threshold: Optional[int] = None
    condition_field: Optional[str] = None
    condition_operator: Optional[str] = None
    condition_value: Optional[List[str]] = None


class ChampResponse(BaseModel):
    id: str
    lexique_id: str
    nom: str
    type: str
    obligatoire: bool
    ordre: int
    options: Optional[List[str]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    formule: Optional[str] = None
    actif: bool
    project_id: Optional[str] = None  # ID du projet
    # Options avancées
    default_value: Optional[str] = None
    display_mode: Optional[str] = "auto"
    search_threshold: Optional[int] = 10
    condition_field: Optional[str] = None
    condition_operator: Optional[str] = "="
    condition_value: Optional[List[str]] = None


@router.get("/lexique/{lexique_code}", response_model=List[ChampResponse])
async def get_champs_by_lexique(
    lexique_code: str,
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère les champs dynamiques pour une entrée lexique (filtrés par projet si spécifié)."""
    if project_id:
        result = await db.execute(
            text("""
                SELECT id, type_name, field_name, field_label, field_type, is_required,
                       display_order, dropdown_options, min_value, max_value,
                       default_value, help_text, project_id
                FROM type_field_configs
                WHERE type_name = :code AND (project_id = :project_id OR project_id IS NULL)
                ORDER BY display_order
            """),
            {"code": lexique_code, "project_id": project_id},
        )
    else:
        result = await db.execute(
            text("""
                SELECT id, type_name, field_name, field_label, field_type, is_required,
                       display_order, dropdown_options, min_value, max_value,
                       default_value, help_text, project_id
                FROM type_field_configs
                WHERE type_name = :code
                ORDER BY display_order
            """),
            {"code": lexique_code},
        )
    rows = result.mappings().all()

    responses = []
    for row in rows:
        # Extraire les options avancées du help_text (JSON)
        advanced_opts = {}
        help_text = row.get("help_text")
        if help_text:
            try:
                advanced_opts = json.loads(help_text) if isinstance(help_text, str) else help_text
            except:
                advanced_opts = {}

        responses.append(ChampResponse(
            id=str(row["id"]),
            lexique_id=row["type_name"],
            nom=row["field_name"],
            type=row["field_type"],
            obligatoire=row["is_required"] or False,
            ordre=row["display_order"] or 0,
            options=row.get("dropdown_options"),
            min=row.get("min_value"),
            max=row.get("max_value"),
            formule=advanced_opts.get("formule"),
            actif=advanced_opts.get("actif", True),
            project_id=str(row["project_id"]) if row.get("project_id") else None,
            # Options avancées
            default_value=row.get("default_value") or advanced_opts.get("default_value"),
            display_mode=advanced_opts.get("display_mode", "auto"),
            search_threshold=advanced_opts.get("search_threshold", 10),
            condition_field=advanced_opts.get("condition_field"),
            condition_operator=advanced_opts.get("condition_operator", "="),
            condition_value=advanced_opts.get("condition_value"),
        ))

    return responses


@router.post("", response_model=ChampResponse, status_code=status.HTTP_201_CREATED)
async def create_champ(
    champ: ChampCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Crée un nouveau champ dynamique (admin seulement)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    options_json = json.dumps(champ.options) if champ.options else None

    # Note: id is SERIAL (auto-generated), field_label uses nom as label
    # The database doesn't have a metadata column, so we store advanced options in help_text as JSON
    advanced_options = {
        "formule": champ.formule,
        "actif": champ.actif,
        "display_mode": champ.display_mode or "auto",
        "search_threshold": champ.search_threshold or 10,
        "condition_field": champ.condition_field,
        "condition_operator": champ.condition_operator or "=",
        "condition_value": champ.condition_value,
    }
    help_text_json = json.dumps(advanced_options)

    params = {
        "type_name": champ.lexique_id,
        "field_name": champ.nom,
        "field_label": champ.nom,  # Use nom as the display label
        "field_type": champ.type.value,
        "is_required": champ.obligatoire,
        "display_order": champ.ordre,
        "dropdown_options": options_json,
        "min_value": champ.min,
        "max_value": champ.max,
        "default_value": champ.default_value,
        "help_text": help_text_json,
        "project_id": champ.project_id,
    }

    result = await db.execute(
        text("""
            INSERT INTO type_field_configs (
                type_name, field_name, field_label, field_type, is_required, display_order,
                dropdown_options, min_value, max_value, default_value, help_text, project_id
            ) VALUES (
                :type_name, :field_name, :field_label, :field_type, :is_required, :display_order,
                CAST(:dropdown_options AS jsonb), :min_value, :max_value, :default_value,
                :help_text, :project_id
            )
            RETURNING *
        """),
        params,
    )

    await db.commit()
    row = result.mappings().first()

    return ChampResponse(
        id=str(row["id"]),
        lexique_id=row["type_name"],
        nom=row["field_name"],
        type=row["field_type"],
        obligatoire=row["is_required"] or False,
        ordre=row["display_order"] or 0,
        options=row.get("dropdown_options"),
        min=row.get("min_value"),
        max=row.get("max_value"),
        formule=champ.formule,
        actif=champ.actif,
        project_id=str(row["project_id"]) if row.get("project_id") else None,
        default_value=champ.default_value,
        display_mode=champ.display_mode or "auto",
        search_threshold=champ.search_threshold or 10,
        condition_field=champ.condition_field,
        condition_operator=champ.condition_operator or "=",
        condition_value=champ.condition_value,
    )


@router.patch("/{champ_id}", response_model=ChampResponse)
async def update_champ(
    champ_id: int,
    updates: ChampUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Met à jour un champ dynamique (admin seulement)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    update_data = updates.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune modification")

    set_clauses = []
    params = {"id": champ_id}

    # Champs stockés dans help_text comme JSON (options avancées)
    advanced_fields = {"formule", "actif", "display_mode", "search_threshold",
                       "condition_field", "condition_operator", "condition_value"}

    # Mapping des noms de champs vers les colonnes DB
    field_mapping = {
        "nom": "field_name",
        "type": "field_type",
        "obligatoire": "is_required",
        "ordre": "display_order",
        "min": "min_value",
        "max": "max_value",
        "options": "dropdown_options",
        "default_value": "default_value",
    }

    # Collecter les champs avancés à mettre à jour
    advanced_updates = {}
    for key in advanced_fields:
        if key in update_data:
            advanced_updates[key] = update_data[key]

    # Traiter les champs normaux
    for key, value in update_data.items():
        if key in advanced_fields:
            continue
        db_field = field_mapping.get(key, key)
        if key == "type" and value:
            value = value.value
        if key == "options" and value:
            value = json.dumps(value)
            set_clauses.append(f"{db_field} = CAST(:{key} AS jsonb)")
        else:
            set_clauses.append(f"{db_field} = :{key}")
        params[key] = value
        # Also update field_label when updating nom
        if key == "nom":
            set_clauses.append("field_label = :nom")

    # Si des champs avancés ont été mis à jour, mettre à jour help_text
    if advanced_updates:
        # D'abord récupérer le help_text existant
        existing = await db.execute(
            text("SELECT help_text FROM type_field_configs WHERE id = :id"),
            {"id": champ_id},
        )
        existing_row = existing.mappings().first()
        existing_opts = {}
        if existing_row and existing_row.get("help_text"):
            try:
                existing_opts = json.loads(existing_row["help_text"])
            except:
                existing_opts = {}

        # Fusionner avec les nouvelles valeurs
        existing_opts.update(advanced_updates)
        help_text_json = json.dumps(existing_opts)
        set_clauses.append("help_text = :help_text")
        params["help_text"] = help_text_json

    if not set_clauses:
        raise HTTPException(status_code=400, detail="Aucune modification valide")

    result = await db.execute(
        text(f"""
            UPDATE type_field_configs
            SET {', '.join(set_clauses)}
            WHERE id = :id
            RETURNING *
        """),
        params,
    )
    await db.commit()
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Champ non trouvé")

    # Extraire options avancées de help_text
    advanced_opts = {}
    help_text = row.get("help_text")
    if help_text:
        try:
            advanced_opts = json.loads(help_text) if isinstance(help_text, str) else help_text
        except:
            advanced_opts = {}

    return ChampResponse(
        id=str(row["id"]),
        lexique_id=row["type_name"],
        nom=row["field_name"],
        type=row["field_type"],
        obligatoire=row["is_required"] or False,
        ordre=row["display_order"] or 0,
        options=row.get("dropdown_options"),
        min=row.get("min_value"),
        max=row.get("max_value"),
        formule=advanced_opts.get("formule"),
        actif=advanced_opts.get("actif", True),
        default_value=row.get("default_value") or advanced_opts.get("default_value"),
        display_mode=advanced_opts.get("display_mode", "auto"),
        search_threshold=advanced_opts.get("search_threshold", 10),
        condition_field=advanced_opts.get("condition_field"),
        condition_operator=advanced_opts.get("condition_operator", "="),
        condition_value=advanced_opts.get("condition_value"),
    )


@router.delete("/{champ_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_champ(
    champ_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Supprime un champ dynamique (admin seulement)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    result = await db.execute(
        text("DELETE FROM type_field_configs WHERE id = :id RETURNING id"),
        {"id": champ_id},
    )
    await db.commit()

    if not result.first():
        raise HTTPException(status_code=404, detail="Champ non trouvé")


@router.post("/reorder")
async def reorder_champs(
    items: List[dict],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Réordonne les champs dynamiques."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    for item in items:
        await db.execute(
            text("UPDATE type_field_configs SET display_order = :ordre WHERE id = :id"),
            {"id": int(item["id"]), "ordre": item["ordre"]},
        )
    await db.commit()

    return {"success": True}
