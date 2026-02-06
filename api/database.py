"""
Configuration de la base de données PostgreSQL/PostGIS.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config import settings

# Moteur async pour PostgreSQL
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# Session async
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base pour les modèles SQLAlchemy
Base = declarative_base()


async def get_db():
    """Dépendance FastAPI pour obtenir une session DB."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """Crée les tables si elles n'existent pas."""
    # Note: En production, utiliser Alembic pour les migrations
    async with engine.begin() as conn:
        # Les tables sont créées par le script SQL init
        pass
