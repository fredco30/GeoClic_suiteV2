"""
Router pour le Lexique (menus en cascade).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List

from database import get_db
from routers.auth import get_current_user
from schemas.lexique import (
    LexiqueCreate,
    LexiqueUpdate,
    LexiqueResponse,
    LexiqueChildResponse,
    LexiqueTreeResponse,
)

router = APIRouter()


@router.get("", response_model=List[LexiqueResponse])
async def list_lexique(
    project_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Liste toutes les entrées du Lexique pour un projet."""
    if project_id:
        result = await db.execute(
            text("""
                SELECT l.*, get_lexique_path(l.code) as full_path
                FROM lexique l
                WHERE l.is_active = TRUE AND l.project_id = :project_id
                ORDER BY l.level, l.display_order, l.label
            """),
            {"project_id": project_id}
        )
    else:
        result = await db.execute(
            text("""
                SELECT l.*, get_lexique_path(l.code) as full_path
                FROM lexique l
                WHERE l.is_active = TRUE
                ORDER BY l.level, l.display_order, l.label
            """)
        )
    rows = result.mappings().all()

    return [
        LexiqueResponse(
            id=row["id"],
            code=row["code"],
            label=row["label"],
            parent_code=row["parent_code"],
            project_id=str(row["project_id"]) if row.get("project_id") else None,
            level=row["level"],
            display_order=row["display_order"],
            triggers_form=row["triggers_form"],
            form_type_ref=row["form_type_ref"],
            icon_name=row["icon_name"],
            color_value=row["color_value"],
            is_active=row["is_active"],
            metadata=row["metadata"],
            created_at=row["created_at"],
            full_path=row["full_path"],
        )
        for row in rows
    ]


@router.get("/tree", response_model=LexiqueTreeResponse)
async def get_lexique_tree(
    project_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère l'arbre complet du Lexique pour un projet."""
    if project_id:
        # Récupérer les racines du projet
        roots_result = await db.execute(
            text("""
                SELECT l.*, get_lexique_path(l.code) as full_path
                FROM lexique l
                WHERE l.parent_code IS NULL AND l.is_active = TRUE AND l.project_id = :project_id
                ORDER BY l.display_order, l.label
            """),
            {"project_id": project_id}
        )
        roots = roots_result.mappings().all()

        # Compter les entrées du projet
        count_result = await db.execute(
            text("SELECT COUNT(*) FROM lexique WHERE is_active = TRUE AND project_id = :project_id"),
            {"project_id": project_id}
        )
        total = count_result.scalar()

        # Profondeur max du projet
        depth_result = await db.execute(
            text("SELECT MAX(level) FROM lexique WHERE is_active = TRUE AND project_id = :project_id"),
            {"project_id": project_id}
        )
        max_depth = depth_result.scalar() or 0
    else:
        roots_result = await db.execute(
            text("""
                SELECT l.*, get_lexique_path(l.code) as full_path
                FROM lexique l
                WHERE l.parent_code IS NULL AND l.is_active = TRUE
                ORDER BY l.display_order, l.label
            """)
        )
        roots = roots_result.mappings().all()
        count_result = await db.execute(
            text("SELECT COUNT(*) FROM lexique WHERE is_active = TRUE")
        )
        total = count_result.scalar()
        depth_result = await db.execute(
            text("SELECT MAX(level) FROM lexique WHERE is_active = TRUE")
        )
        max_depth = depth_result.scalar() or 0

    return LexiqueTreeResponse(
        roots=[
            LexiqueResponse(
                id=row["id"],
                code=row["code"],
                label=row["label"],
                parent_code=row["parent_code"],
                project_id=str(row["project_id"]) if row.get("project_id") else None,
                level=row["level"],
                display_order=row["display_order"],
                triggers_form=row["triggers_form"],
                form_type_ref=row["form_type_ref"],
                icon_name=row["icon_name"],
                color_value=row["color_value"],
                is_active=row["is_active"],
                metadata=row["metadata"],
                created_at=row["created_at"],
                full_path=row["full_path"],
            )
            for row in roots
        ],
        total_entries=total,
        max_depth=max_depth,
    )


@router.get("/{code}/children", response_model=List[LexiqueChildResponse])
async def get_children(
    code: str,
    project_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère les enfants d'une entrée Lexique."""
    if project_id:
        result = await db.execute(
            text("""
                SELECT
                    l.code,
                    l.label,
                    l.level,
                    l.triggers_form,
                    l.icon_name,
                    l.color_value,
                    EXISTS(SELECT 1 FROM lexique c WHERE c.parent_code = l.code AND c.project_id = l.project_id AND c.is_active = TRUE) as has_children
                FROM lexique l
                WHERE l.parent_code = :code AND l.project_id = :project_id AND l.is_active = TRUE
                ORDER BY l.display_order, l.label
            """),
            {"code": code, "project_id": project_id},
        )
    else:
        result = await db.execute(
            text("""
                SELECT
                    l.code,
                    l.label,
                    l.level,
                    l.triggers_form,
                    l.icon_name,
                    l.color_value,
                    EXISTS(SELECT 1 FROM lexique c WHERE c.parent_code = l.code AND c.is_active = TRUE) as has_children
                FROM lexique l
                WHERE l.parent_code = :code AND l.is_active = TRUE
                ORDER BY l.display_order, l.label
            """),
            {"code": code},
        )
    rows = result.mappings().all()

    return [
        LexiqueChildResponse(
            code=row["code"],
            label=row["label"],
            level=row["level"],
            triggers_form=row["triggers_form"],
            icon_name=row["icon_name"],
            color_value=row["color_value"],
            has_children=row["has_children"],
        )
        for row in rows
    ]


@router.get("/{code}/can-delete")
async def can_delete_lexique_entry(
    code: str,
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Vérifie si une entrée Lexique peut être supprimée.
    Retourne les informations sur les dépendances (points, enfants, champs).
    """
    # Vérifier que l'entrée existe
    entry_result = await db.execute(
        text("SELECT id, code, label FROM lexique WHERE code = :code AND project_id = :project_id"),
        {"code": code, "project_id": project_id},
    )
    entry = entry_result.mappings().first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entrée Lexique non trouvée")

    # Récupérer tous les codes descendants
    descendants_result = await db.execute(
        text("""
            WITH RECURSIVE descendants AS (
                SELECT code, label, level FROM lexique WHERE code = :code AND project_id = :project_id
                UNION ALL
                SELECT l.code, l.label, l.level FROM lexique l
                INNER JOIN descendants d ON l.parent_code = d.code
                WHERE l.project_id = :project_id
            )
            SELECT code, label, level FROM descendants
        """),
        {"code": code, "project_id": project_id},
    )
    descendants = descendants_result.mappings().all()
    all_codes = [d["code"] for d in descendants]

    # Compter les points associés (table peut ne pas exister)
    points_count = 0
    try:
        points_result = await db.execute(
            text("""
                SELECT COUNT(*) as count
                FROM points
                WHERE project_id = :project_id AND lexique_code = ANY(:codes)
            """),
            {"project_id": project_id, "codes": all_codes},
        )
        points_count = points_result.scalar() or 0
    except Exception as e:
        # Table points n'existe pas encore - pas de points associés
        error_str = str(e).lower()
        if "points" in error_str and ("not exist" in error_str or "undefined" in error_str):
            points_count = 0
        else:
            raise

    # Compter les champs associés
    fields_count = 0
    try:
        fields_result = await db.execute(
            text("""
                SELECT COUNT(*) FROM type_field_configs
                WHERE type_name = ANY(:codes)
                AND (project_id = :project_id OR project_id IS NULL)
            """),
            {"codes": all_codes, "project_id": project_id},
        )
        fields_count = fields_result.scalar() or 0
    except Exception:
        # Fallback sans project_id
        try:
            fields_result = await db.execute(
                text("SELECT COUNT(*) FROM type_field_configs WHERE type_name = ANY(:codes)"),
                {"codes": all_codes},
            )
            fields_count = fields_result.scalar() or 0
        except Exception:
            fields_count = 0

    can_delete = points_count == 0

    return {
        "can_delete": can_delete,
        "entry": {
            "code": entry["code"],
            "label": entry["label"]
        },
        "descendants_count": len(descendants) - 1,  # -1 pour exclure l'entrée elle-même
        "points_count": points_count,
        "fields_count": fields_count,
        "reason": None if can_delete else f"{points_count} point(s) associé(s)"
    }


@router.get("/{code}", response_model=LexiqueResponse)
async def get_lexique_entry(
    code: str,
    project_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère une entrée Lexique par son code."""
    if project_id:
        result = await db.execute(
            text("""
                SELECT l.*, get_lexique_path(l.code) as full_path
                FROM lexique l
                WHERE l.code = :code AND l.project_id = :project_id
            """),
            {"code": code, "project_id": project_id},
        )
    else:
        result = await db.execute(
            text("""
                SELECT l.*, get_lexique_path(l.code) as full_path
                FROM lexique l
                WHERE l.code = :code
            """),
            {"code": code},
        )
    row = result.mappings().first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entrée Lexique non trouvée",
        )

    return LexiqueResponse(
        id=row["id"],
        code=row["code"],
        label=row["label"],
        parent_code=row["parent_code"],
        project_id=str(row["project_id"]) if row.get("project_id") else None,
        level=row["level"],
        display_order=row["display_order"],
        triggers_form=row["triggers_form"],
        form_type_ref=row["form_type_ref"],
        icon_name=row["icon_name"],
        color_value=row["color_value"],
        is_active=row["is_active"],
        metadata=row["metadata"],
        created_at=row["created_at"],
        full_path=row["full_path"],
    )


@router.post("", response_model=LexiqueResponse, status_code=status.HTTP_201_CREATED)
async def create_lexique_entry(
    entry: LexiqueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Crée une nouvelle entrée Lexique (admin)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    # Vérifier que le code n'existe pas pour ce projet
    existing = await db.execute(
        text("SELECT id FROM lexique WHERE code = :code AND project_id = :project_id"),
        {"code": entry.code, "project_id": entry.project_id},
    )
    if existing.first():
        raise HTTPException(
            status_code=400,
            detail="Ce code existe déjà dans ce projet",
        )

    # Vérifier le parent si spécifié
    if entry.parent_code:
        parent = await db.execute(
            text("SELECT level FROM lexique WHERE code = :code AND project_id = :project_id"),
            {"code": entry.parent_code, "project_id": entry.project_id},
        )
        parent_row = parent.first()
        if not parent_row:
            raise HTTPException(
                status_code=400,
                detail="Parent non trouvé dans ce projet",
            )
        entry.level = parent_row[0] + 1

    result = await db.execute(
        text("""
            INSERT INTO lexique (
                code, label, parent_code, project_id, level, display_order,
                triggers_form, form_type_ref, icon_name, color_value,
                is_active, metadata
            ) VALUES (
                :code, :label, :parent_code, :project_id, :level, :display_order,
                :triggers_form, :form_type_ref, :icon_name, :color_value,
                :is_active, CAST(:metadata AS jsonb)
            )
            RETURNING *, get_lexique_path(code) as full_path
        """),
        {
            "code": entry.code,
            "label": entry.label,
            "parent_code": entry.parent_code,
            "project_id": entry.project_id,
            "level": entry.level,
            "display_order": entry.display_order,
            "triggers_form": entry.triggers_form,
            "form_type_ref": entry.form_type_ref,
            "icon_name": entry.icon_name,
            "color_value": entry.color_value,
            "is_active": entry.is_active,
            "metadata": str(entry.metadata) if entry.metadata else None,
        },
    )
    await db.commit()
    row = result.mappings().first()

    return LexiqueResponse(
        id=row["id"],
        code=row["code"],
        label=row["label"],
        parent_code=row["parent_code"],
        project_id=str(row["project_id"]) if row.get("project_id") else None,
        level=row["level"],
        display_order=row["display_order"],
        triggers_form=row["triggers_form"],
        form_type_ref=row["form_type_ref"],
        icon_name=row["icon_name"],
        color_value=row["color_value"],
        is_active=row["is_active"],
        metadata=row["metadata"],
        created_at=row["created_at"],
        full_path=row["full_path"],
    )


@router.patch("/{code}", response_model=LexiqueResponse)
async def update_lexique_entry(
    code: str,
    updates: LexiqueUpdate,
    project_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Met à jour une entrée Lexique (admin)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    update_data = updates.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune modification")

    # Construire la requête
    set_clauses = []
    params = {"code": code}
    if project_id:
        params["project_id"] = project_id
    for key, value in update_data.items():
        set_clauses.append(f"{key} = :{key}")
        params[key] = value

    where_clause = "code = :code"
    if project_id:
        where_clause += " AND project_id = :project_id"

    result = await db.execute(
        text(f"""
            UPDATE lexique
            SET {', '.join(set_clauses)}
            WHERE {where_clause}
            RETURNING *, get_lexique_path(code) as full_path
        """),
        params,
    )
    await db.commit()
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Entrée non trouvée")

    return LexiqueResponse(
        id=row["id"],
        code=row["code"],
        label=row["label"],
        parent_code=row["parent_code"],
        project_id=str(row["project_id"]) if row.get("project_id") else None,
        level=row["level"],
        display_order=row["display_order"],
        triggers_form=row["triggers_form"],
        form_type_ref=row["form_type_ref"],
        icon_name=row["icon_name"],
        color_value=row["color_value"],
        is_active=row["is_active"],
        metadata=row["metadata"],
        created_at=row["created_at"],
        full_path=row["full_path"],
    )


@router.delete("/{code}", status_code=status.HTTP_200_OK)
async def delete_lexique_entry(
    code: str,
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Supprime une entrée Lexique et tous ses enfants (admin).

    La suppression est interdite si des points sont associés à l'entrée ou ses enfants.
    La suppression inclut :
    - Tous les enfants récursifs (types, sous-types, etc.)
    - Tous les champs dynamiques associés (type_field_configs)
    """
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    # Vérifier que l'entrée existe
    entry_result = await db.execute(
        text("SELECT id, code, label FROM lexique WHERE code = :code AND project_id = :project_id"),
        {"code": code, "project_id": project_id},
    )
    entry = entry_result.mappings().first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entrée Lexique non trouvée")

    # Récupérer tous les codes descendants (récursif via CTE)
    descendants_result = await db.execute(
        text("""
            WITH RECURSIVE descendants AS (
                -- Base: l'entrée elle-même
                SELECT code FROM lexique WHERE code = :code AND project_id = :project_id
                UNION ALL
                -- Récursion: tous les enfants
                SELECT l.code FROM lexique l
                INNER JOIN descendants d ON l.parent_code = d.code
                WHERE l.project_id = :project_id
            )
            SELECT code FROM descendants
        """),
        {"code": code, "project_id": project_id},
    )
    all_codes = [row["code"] for row in descendants_result.mappings().all()]

    if not all_codes:
        raise HTTPException(status_code=404, detail="Entrée Lexique non trouvée")

    # Vérifier qu'aucun point n'est associé à ces codes (table peut ne pas exister)
    try:
        points_check = await db.execute(
            text("""
                SELECT COUNT(*) as count, MIN(name) as first_point
                FROM points
                WHERE project_id = :project_id
                AND lexique_code = ANY(:codes)
            """),
            {"project_id": project_id, "codes": all_codes},
        )
        points_result = points_check.mappings().first()

        if points_result and points_result["count"] > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de supprimer : {points_result['count']} point(s) associé(s). "
                       f"Supprimez d'abord les points (ex: '{points_result['first_point']}')."
            )
    except HTTPException:
        raise  # Re-raise HTTPException (points exist)
    except Exception as e:
        # Table points n'existe pas encore - pas de points associés, continuer
        error_str = str(e).lower()
        if not ("points" in error_str and ("not exist" in error_str or "undefined" in error_str)):
            raise  # Re-raise si ce n'est pas une erreur de table manquante

    # Supprimer les champs dynamiques associés (type_field_configs)
    # Utilise un try/except au cas où la colonne project_id n'existe pas encore
    deleted_fields = 0
    try:
        fields_result = await db.execute(
            text("""
                DELETE FROM type_field_configs
                WHERE type_name = ANY(:codes)
                AND (project_id = :project_id OR project_id IS NULL)
                RETURNING id
            """),
            {"codes": all_codes, "project_id": project_id},
        )
        deleted_fields = len(fields_result.fetchall())
    except Exception as e:
        # Colonne project_id n'existe pas - fallback sans filtre projet
        error_str = str(e).lower()
        if "project_id" in error_str or "column" in error_str:
            await db.rollback()
            fields_result = await db.execute(
                text("DELETE FROM type_field_configs WHERE type_name = ANY(:codes) RETURNING id"),
                {"codes": all_codes},
            )
            deleted_fields = len(fields_result.fetchall())
        else:
            raise

    # Supprimer les entrées lexique (enfants d'abord grâce à l'ordre inversé des niveaux)
    lexique_result = await db.execute(
        text("""
            DELETE FROM lexique
            WHERE code = ANY(:codes) AND project_id = :project_id
            RETURNING id, code
        """),
        {"codes": all_codes, "project_id": project_id},
    )
    deleted_entries = lexique_result.fetchall()

    await db.commit()

    return {
        "success": True,
        "message": f"Famille '{entry['label']}' supprimée avec succès",
        "deleted": {
            "lexique_entries": len(deleted_entries),
            "codes": all_codes,
            "fields": deleted_fields
        }
    }


@router.post("/reorder")
async def reorder_lexique(
    items: List[dict],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Réordonne les entrées Lexique."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    for item in items:
        await db.execute(
            text("UPDATE lexique SET display_order = :ordre WHERE id = :id"),
            {"id": item["id"], "ordre": item["ordre"]},
        )
    await db.commit()

    return {"success": True}
