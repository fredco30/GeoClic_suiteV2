"""
Router pour les Projets.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List

from database import get_db
from routers.auth import get_current_user
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter()


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    include_system: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Liste tous les projets. Par défaut exclut les projets système."""
    # Exclure les projets système par défaut (pour geoclic_data)
    system_filter = "" if include_system else "AND COALESCE(p.is_system, FALSE) = FALSE"

    result = await db.execute(
        text(f"""
            SELECT p.*,
                   (SELECT COUNT(*) FROM geoclic_staging WHERE project_id = p.id) as point_count
            FROM projects p
            WHERE p.is_active = TRUE
            {system_filter}
            ORDER BY p.created_at DESC
        """)
    )
    rows = result.mappings().all()

    return [
        ProjectResponse(
            id=str(row["id"]),
            name=row["name"],
            description=row["description"],
            status=row["status"],
            is_active=row["is_active"],
            is_system=row.get("is_system", False) or False,
            collectivite_name=row["collectivite_name"],
            collectivite_address=row["collectivite_address"],
            responsable_name=row["responsable_name"],
            responsable_email=row["responsable_email"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            metadata=row["metadata"],
            point_count=row["point_count"],
            min_lat=row["min_lat"],
            max_lat=row["max_lat"],
            min_lng=row["min_lng"],
            max_lng=row["max_lng"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Récupère un projet par son ID."""
    result = await db.execute(
        text("""
            SELECT p.*,
                   (SELECT COUNT(*) FROM geoclic_staging WHERE project_id = p.id) as point_count
            FROM projects p
            WHERE p.id = :id
        """),
        {"id": project_id},
    )
    row = result.mappings().first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé",
        )

    return ProjectResponse(
        id=str(row["id"]),
        name=row["name"],
        description=row["description"],
        status=row["status"],
        is_active=row["is_active"],
        is_system=row.get("is_system", False) or False,
        collectivite_name=row["collectivite_name"],
        collectivite_address=row["collectivite_address"],
        responsable_name=row["responsable_name"],
        responsable_email=row["responsable_email"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        metadata=row["metadata"],
        point_count=row["point_count"],
        min_lat=row["min_lat"],
        max_lat=row["max_lat"],
        min_lng=row["min_lng"],
        max_lng=row["max_lng"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Crée un nouveau projet (admin data uniquement)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    result = await db.execute(
        text("""
            INSERT INTO projects (
                name, description, status, is_active,
                collectivite_name, collectivite_address,
                responsable_name, responsable_email,
                start_date, end_date, metadata
            ) VALUES (
                :name, :description, :status, :is_active,
                :collectivite_name, :collectivite_address,
                :responsable_name, :responsable_email,
                :start_date, :end_date, CAST(:metadata AS jsonb)
            )
            RETURNING *
        """),
        {
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "is_active": project.is_active,
            "collectivite_name": project.collectivite_name,
            "collectivite_address": project.collectivite_address,
            "responsable_name": project.responsable_name,
            "responsable_email": project.responsable_email,
            "start_date": project.start_date,
            "end_date": project.end_date,
            "metadata": str(project.metadata) if project.metadata else None,
        },
    )
    await db.commit()
    row = result.mappings().first()

    return ProjectResponse(
        id=str(row["id"]),
        name=row["name"],
        description=row["description"],
        status=row["status"],
        is_active=row["is_active"],
        is_system=row.get("is_system", False) or False,
        collectivite_name=row["collectivite_name"],
        collectivite_address=row["collectivite_address"],
        responsable_name=row["responsable_name"],
        responsable_email=row["responsable_email"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        metadata=row["metadata"],
        point_count=0,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    updates: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Met à jour un projet (admin data uniquement)."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")

    # Vérifier si c'est un projet système
    check_result = await db.execute(
        text("SELECT is_system FROM projects WHERE id = :id"),
        {"id": project_id}
    )
    project_row = check_result.mappings().first()
    if project_row and project_row.get("is_system"):
        # Autoriser uniquement les modifications non-critiques (nom, description, collectivite)
        allowed_fields = {"name", "description", "collectivite_name", "collectivite_address",
                         "responsable_name", "responsable_email"}
        update_data = updates.model_dump(exclude_unset=True)
        critical_fields = set(update_data.keys()) - allowed_fields
        if critical_fields:
            raise HTTPException(
                status_code=403,
                detail=f"Ce projet système ne peut pas être modifié. Champs protégés: {', '.join(critical_fields)}"
            )
    else:
        update_data = updates.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune modification")

    set_clauses = []
    params = {"id": project_id}
    for key, value in update_data.items():
        set_clauses.append(f"{key} = :{key}")
        params[key] = value

    result = await db.execute(
        text(f"""
            UPDATE projects
            SET {', '.join(set_clauses)}
            WHERE id = :id
            RETURNING *
        """),
        params,
    )
    await db.commit()
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    return ProjectResponse(
        id=str(row["id"]),
        name=row["name"],
        description=row["description"],
        status=row["status"],
        is_active=row["is_active"],
        is_system=row.get("is_system", False) or False,
        collectivite_name=row["collectivite_name"],
        collectivite_address=row["collectivite_address"],
        responsable_name=row["responsable_name"],
        responsable_email=row["responsable_email"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        metadata=row["metadata"],
        point_count=0,
        min_lat=row["min_lat"],
        max_lat=row["max_lat"],
        min_lng=row["min_lng"],
        max_lng=row["max_lng"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Supprime un projet (admin data uniquement). Les projets système ne peuvent pas être supprimés."""
    if not current_user.get("is_super_admin") and current_user.get("role_data") != "admin":
        raise HTTPException(status_code=403, detail="Seuls les administrateurs peuvent supprimer des projets")

    # Vérifier si c'est un projet système
    check_result = await db.execute(
        text("SELECT is_system, name FROM projects WHERE id = :id"),
        {"id": project_id}
    )
    project_row = check_result.mappings().first()

    if not project_row:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    if project_row.get("is_system"):
        raise HTTPException(
            status_code=403,
            detail=f"Le projet '{project_row['name']}' est un projet système et ne peut pas être supprimé. "
                   "Il contient les données des demandes citoyennes."
        )

    # Supprimer le projet (CASCADE supprimera les données liées)
    await db.execute(
        text("DELETE FROM projects WHERE id = :id"),
        {"id": project_id}
    )
    await db.commit()

    return None
