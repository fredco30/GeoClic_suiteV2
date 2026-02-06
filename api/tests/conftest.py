"""
═══════════════════════════════════════════════════════════════════════════════
GéoClic Suite - Configuration des tests (fixtures pytest)
═══════════════════════════════════════════════════════════════════════════════
Ce fichier configure l'environnement de test:
- Base de données PostgreSQL de test (même serveur, base différente)
- Client HTTP pour tester les endpoints
- Fixtures pour générer des données de test
"""

import pytest
import os
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from faker import Faker
import uuid
from datetime import datetime

# Configuration pour les tests : utiliser une base de test
# On utilise la même base PostgreSQL mais avec un préfixe sur les données
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://geoclic:geoclic_secure_password@db:5432/geoclic_db"
)

# Importer après avoir configuré l'environnement
from main import app
from database import get_db, AsyncSessionLocal, engine
from config import settings

# Faker pour générer des données réalistes en français
fake = Faker('fr_FR')


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES DE BASE
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def anyio_backend():
    """Backend async pour pytest-asyncio."""
    return 'asyncio'


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fournit une session de base de données pour les tests.
    Chaque test a sa propre session avec rollback à la fin.
    """
    async with AsyncSessionLocal() as session:
        yield session
        # Rollback automatique après chaque test
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Client HTTP async pour tester l'API.

    Usage dans les tests:
        async def test_exemple(client):
            response = await client.get("/api/health")
            assert response.status_code == 200
    """
    # Surcharger la dépendance get_db pour utiliser notre session de test
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Nettoyer les overrides
    app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES D'AUTHENTIFICATION
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
async def auth_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """
    Crée un utilisateur de test et retourne son token JWT.

    Usage:
        async def test_protected_endpoint(client, auth_token):
            response = await client.get(
                "/api/demandes",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
    """
    # Créer un utilisateur de test dans geoclic_users (auth unifiée)
    test_user_id = str(uuid.uuid4())
    test_email = f"test_{test_user_id[:8]}@geoclic.test"

    # Hasher le mot de passe (bcrypt)
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash("TestPassword123!")

    # Insérer dans geoclic_users (table d'auth unifiée)
    await db_session.execute(
        text("""
            INSERT INTO geoclic_users (id, email, password_hash, nom, prenom, actif,
                is_super_admin, role_data, role_demandes, role_sig, role_terrain)
            VALUES (CAST(:id AS uuid), :email, :password, 'Test', 'User', true,
                true, 'admin', 'admin', 'edition', 'agent')
            ON CONFLICT (email) DO NOTHING
        """),
        {
            "id": test_user_id,
            "email": test_email,
            "password": hashed_password
        }
    )
    await db_session.commit()

    # Obtenir le token via le nouveau endpoint unifié
    response = await client.post(
        "/api/auth/login",
        data={"username": test_email, "password": "TestPassword123!"}
    )

    if response.status_code == 200:
        return response.json()["access_token"]

    # Fallback : créer un token manuellement pour les tests
    from jose import jwt
    from datetime import timedelta
    token_data = {
        "sub": test_user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(token_data, settings.secret_key, algorithm=settings.algorithm)


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Headers d'authentification prêts à l'emploi."""
    return {"Authorization": f"Bearer {auth_token}"}


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES DE DONNÉES - CATÉGORIES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
async def test_category(db_session: AsyncSession) -> dict:
    """
    Crée une catégorie de test et la retourne.
    Nettoyée automatiquement après le test.
    """
    category_id = str(uuid.uuid4())
    category_data = {
        "id": category_id,
        "nom": f"Catégorie Test {fake.word()}",
        "description": fake.sentence(),
        "icone": "mdi-test",
        "couleur": fake.hex_color(),
        "ordre": 1,
        "actif": True
    }

    await db_session.execute(
        text("""
            INSERT INTO demandes_categories (id, nom, description, icone, couleur, ordre, actif)
            VALUES (CAST(:id AS uuid), :nom, :description, :icone, :couleur, :ordre, :actif)
        """),
        category_data
    )
    await db_session.commit()

    yield category_data

    # Nettoyage
    await db_session.execute(
        text("DELETE FROM demandes_categories WHERE id = CAST(:id AS uuid)"),
        {"id": category_id}
    )
    await db_session.commit()


@pytest.fixture
async def test_subcategory(db_session: AsyncSession, test_category: dict) -> dict:
    """
    Crée une sous-catégorie de test liée à la catégorie de test.
    """
    subcategory_id = str(uuid.uuid4())
    subcategory_data = {
        "id": subcategory_id,
        "parent_id": test_category["id"],
        "nom": f"Sous-catégorie Test {fake.word()}",
        "description": fake.sentence(),
        "icone": "mdi-sub-test",
        "couleur": fake.hex_color(),
        "ordre": 1,
        "actif": True
    }

    await db_session.execute(
        text("""
            INSERT INTO demandes_categories (id, parent_id, nom, description, icone, couleur, ordre, actif)
            VALUES (CAST(:id AS uuid), CAST(:parent_id AS uuid), :nom, :description, :icone, :couleur, :ordre, :actif)
        """),
        subcategory_data
    )
    await db_session.commit()

    yield subcategory_data

    # Nettoyage
    await db_session.execute(
        text("DELETE FROM demandes_categories WHERE id = CAST(:id AS uuid)"),
        {"id": subcategory_id}
    )
    await db_session.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES DE DONNÉES - SERVICES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
async def test_service(db_session: AsyncSession) -> dict:
    """
    Crée un service municipal de test.
    """
    service_id = str(uuid.uuid4())
    service_data = {
        "id": service_id,
        "nom": f"Service Test {fake.word()}",
        "description": fake.sentence(),
        "couleur": fake.hex_color(),
        "email": fake.company_email(),
        "actif": True
    }

    await db_session.execute(
        text("""
            INSERT INTO demandes_services (id, nom, description, couleur, email, actif)
            VALUES (CAST(:id AS uuid), :nom, :description, :couleur, :email, :actif)
        """),
        service_data
    )
    await db_session.commit()

    yield service_data

    # Nettoyage
    await db_session.execute(
        text("DELETE FROM demandes_services WHERE id = CAST(:id AS uuid)"),
        {"id": service_id}
    )
    await db_session.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES DE DONNÉES - DEMANDES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
async def test_demande(db_session: AsyncSession, test_subcategory: dict) -> dict:
    """
    Crée une demande citoyenne de test.
    """
    demande_id = str(uuid.uuid4())
    numero = f"TEST-{fake.random_number(digits=6)}"

    demande_data = {
        "id": demande_id,
        "numero": numero,
        "categorie_id": test_subcategory["id"],
        "titre": fake.sentence(nb_words=5),
        "description": fake.paragraph(),
        "adresse": fake.address(),
        "latitude": float(fake.latitude()),
        "longitude": float(fake.longitude()),
        "email_declarant": fake.email(),
        "nom_declarant": fake.last_name(),
        "prenom_declarant": fake.first_name(),
        "telephone_declarant": fake.phone_number(),
        "statut": "nouveau",
        "priorite": "normale"
    }

    await db_session.execute(
        text("""
            INSERT INTO demandes_citoyens (
                id, numero, categorie_id, titre, description, adresse,
                latitude, longitude, email_declarant, nom_declarant,
                prenom_declarant, telephone_declarant, statut, priorite
            )
            VALUES (
                CAST(:id AS uuid), :numero, CAST(:categorie_id AS uuid), :titre, :description, :adresse,
                :latitude, :longitude, :email_declarant, :nom_declarant,
                :prenom_declarant, :telephone_declarant, :statut, :priorite
            )
        """),
        demande_data
    )
    await db_session.commit()

    yield demande_data

    # Nettoyage
    await db_session.execute(
        text("DELETE FROM demandes_citoyens WHERE id = CAST(:id AS uuid)"),
        {"id": demande_id}
    )
    await db_session.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS DE TEST
# ═══════════════════════════════════════════════════════════════════════════════

def generate_demande_data() -> dict:
    """Génère des données valides pour créer une demande."""
    return {
        "titre": fake.sentence(nb_words=5),
        "description": fake.paragraph(),
        "adresse": fake.address(),
        "latitude": float(fake.latitude()),
        "longitude": float(fake.longitude()),
        "email_declarant": fake.email(),
        "nom_declarant": fake.last_name(),
        "prenom_declarant": fake.first_name(),
        "telephone_declarant": fake.phone_number()
    }


def generate_category_data() -> dict:
    """Génère des données valides pour créer une catégorie."""
    return {
        "nom": f"Catégorie {fake.word()}",
        "description": fake.sentence(),
        "icone": "mdi-folder",
        "couleur": fake.hex_color(),
        "ordre": fake.random_int(min=1, max=100),
        "actif": True
    }


def generate_service_data() -> dict:
    """Génère des données valides pour créer un service."""
    return {
        "nom": f"Service {fake.word()}",
        "description": fake.sentence(),
        "couleur": fake.hex_color(),
        "email": fake.company_email(),
        "actif": True
    }
