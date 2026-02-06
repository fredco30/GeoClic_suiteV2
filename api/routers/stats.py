"""
Router pour les statistiques du dashboard.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import List

from database import get_db
from routers.auth import get_current_user

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Statistiques globales pour le dashboard."""
    # Total des points
    total_result = await db.execute(
        text("SELECT COUNT(*) FROM geoclic_staging")
    )
    total_points = total_result.scalar() or 0

    # Points ce mois-ci
    month_result = await db.execute(
        text("""
            SELECT COUNT(*) FROM geoclic_staging
            WHERE created_at >= date_trunc('month', CURRENT_DATE)
        """)
    )
    points_this_month = month_result.scalar() or 0

    # Utilisateurs actifs
    users_result = await db.execute(
        text("SELECT COUNT(*) FROM geoclic_users WHERE actif = TRUE")
    )
    active_users = users_result.scalar() or 0

    # Nombre de projets
    projects_result = await db.execute(
        text("SELECT COUNT(*) FROM projects WHERE is_active = TRUE")
    )
    projects = projects_result.scalar() or 0

    return {
        "totalPoints": total_points,
        "pointsThisMonth": points_this_month,
        "activeUsers": active_users,
        "projects": projects,
    }


@router.get("/points-by-category")
async def get_points_by_category(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Répartition des points par catégorie."""
    result = await db.execute(
        text("""
            SELECT
                COALESCE(l.label, gs.type, 'Inconnu') as label,
                l.color_value as color_int,
                COUNT(*) as count
            FROM geoclic_staging gs
            LEFT JOIN lexique l ON gs.lexique_code = l.code
            GROUP BY l.label, l.color_value, gs.type
            ORDER BY count DESC
            LIMIT 10
        """)
    )
    rows = result.mappings().all()

    def int_to_hex_color(color_int):
        """Convertit un entier en couleur hex, ou retourne la couleur par défaut."""
        if color_int is None:
            return '#1976D2'
        # S'assurer que c'est un entier positif
        if isinstance(color_int, int) and color_int >= 0:
            return f'#{color_int:06x}'
        return '#1976D2'

    return [
        {
            "label": row["label"],
            "color": int_to_hex_color(row["color_int"]),
            "count": row["count"],
        }
        for row in rows
    ]


@router.get("/points-by-date")
async def get_points_by_date(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Évolution des points sur les N derniers jours."""
    result = await db.execute(
        text("""
            SELECT
                DATE(created_at) as date,
                COUNT(*) as count
            FROM geoclic_staging
            WHERE created_at >= CURRENT_DATE - INTERVAL ':days days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """.replace(':days', str(days)))
    )
    rows = result.mappings().all()

    # Remplir les jours manquants
    date_counts = {row["date"]: row["count"] for row in rows}
    timeline = []
    for i in range(days - 1, -1, -1):
        date = (datetime.now() - timedelta(days=i)).date()
        timeline.append({
            "date": date.strftime("%d/%m"),
            "count": date_counts.get(date, 0),
        })

    return timeline


@router.get("/activity-by-user")
async def get_activity_by_user(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Activité récente par utilisateur (admin seulement)."""
    # Vérifier les permissions avec le nouveau système
    is_admin = current_user.get("is_super_admin") or current_user.get("role_data") == "admin"
    if not is_admin:
        return []

    result = await db.execute(
        text("""
            SELECT
                u.id,
                CONCAT(u.prenom, ' ', u.nom) as user,
                'A créé un point' as action,
                gs.created_at as date
            FROM geoclic_staging gs
            JOIN geoclic_users u ON gs.created_by = u.id
            ORDER BY gs.created_at DESC
            LIMIT 10
        """)
    )
    rows = result.mappings().all()

    return [
        {
            "id": str(row["id"]),
            "user": row["user"],
            "action": row["action"],
            "date": row["date"].isoformat() if row["date"] else None,
            "avatar": None,
        }
        for row in rows
    ]


@router.get("/project/{project_id}")
async def get_project_stats(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Statistiques d'un projet spécifique."""
    # Total points du projet
    total_result = await db.execute(
        text("SELECT COUNT(*) FROM geoclic_staging WHERE project_id = :id"),
        {"id": project_id},
    )
    total = total_result.scalar() or 0

    # Par statut
    status_result = await db.execute(
        text("""
            SELECT sync_status, COUNT(*) as count
            FROM geoclic_staging
            WHERE project_id = :id
            GROUP BY sync_status
        """),
        {"id": project_id},
    )
    status_rows = status_result.mappings().all()

    # Par type
    type_result = await db.execute(
        text("""
            SELECT type, COUNT(*) as count
            FROM geoclic_staging
            WHERE project_id = :id
            GROUP BY type
        """),
        {"id": project_id},
    )
    type_rows = type_result.mappings().all()

    return {
        "total": total,
        "by_status": {row["sync_status"]: row["count"] for row in status_rows},
        "by_type": {row["type"]: row["count"] for row in type_rows},
    }
