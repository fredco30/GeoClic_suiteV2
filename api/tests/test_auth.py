"""
═══════════════════════════════════════════════════════════════════════════════
Tests d'authentification - GéoClic Suite
═══════════════════════════════════════════════════════════════════════════════
Ces tests vérifient le bon fonctionnement de l'authentification JWT.

Endpoints testés:
- POST /api/auth/login - Obtenir un token (auth unifiée)
- GET /api/auth/me - Infos utilisateur courant
- Protection des routes sensibles
"""

import pytest
from httpx import AsyncClient


class TestAuthTokenEndpoints:
    """Tests d'obtention de token."""

    async def test_login_with_valid_credentials(
        self,
        client: AsyncClient,
        db_session
    ):
        """
        Test: POST /api/auth/login avec identifiants valides retourne un token.
        """
        # Créer un utilisateur dans geoclic_users (auth unifiée)
        from sqlalchemy import text
        from passlib.context import CryptContext
        import uuid

        user_id = str(uuid.uuid4())
        email = f"auth_test_{user_id[:8]}@geoclic.test"
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash("MotDePasse123!")

        await db_session.execute(
            text("""
                INSERT INTO geoclic_users (id, email, password_hash, nom, prenom, actif,
                    is_super_admin, role_data, role_demandes, role_sig, role_terrain)
                VALUES (CAST(:id AS uuid), :email, :password, 'Test', 'Auth', true,
                    false, 'admin', 'aucun', 'aucun', 'aucun')
            """),
            {"id": user_id, "email": email, "password": hashed}
        )
        await db_session.commit()

        # Tenter la connexion via le nouvel endpoint unifié
        response = await client.post(
            "/api/auth/login",
            data={"username": email, "password": "MotDePasse123!"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_with_invalid_password(self, client: AsyncClient, db_session):
        """
        Test: POST /api/auth/login avec mauvais mot de passe échoue.
        """
        from sqlalchemy import text
        from passlib.context import CryptContext
        import uuid

        user_id = str(uuid.uuid4())
        email = f"auth_test_bad_{user_id[:8]}@geoclic.test"
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash("BonMotDePasse!")

        await db_session.execute(
            text("""
                INSERT INTO geoclic_users (id, email, password_hash, nom, prenom, actif,
                    is_super_admin, role_data, role_demandes, role_sig, role_terrain)
                VALUES (CAST(:id AS uuid), :email, :password, 'Test', 'Auth', true,
                    false, 'admin', 'aucun', 'aucun', 'aucun')
            """),
            {"id": user_id, "email": email, "password": hashed}
        )
        await db_session.commit()

        # Tenter avec mauvais mot de passe
        response = await client.post(
            "/api/auth/login",
            data={"username": email, "password": "MauvaisMotDePasse!"}
        )

        assert response.status_code in [401, 400]

    async def test_login_with_nonexistent_user(self, client: AsyncClient):
        """
        Test: POST /api/auth/login avec utilisateur inexistant échoue.
        """
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "utilisateur.inexistant@test.fr",
                "password": "MotDePasse123!"
            }
        )

        assert response.status_code in [401, 400, 429]

    async def test_login_without_credentials(self, client: AsyncClient):
        """
        Test: POST /api/auth/login sans identifiants échoue.
        """
        response = await client.post("/api/auth/login")

        assert response.status_code == 422


class TestAuthMeEndpoints:
    """Tests de l'endpoint /me."""

    async def test_get_current_user(self, client: AsyncClient, auth_headers: dict):
        """
        Test: GET /api/auth/me retourne les infos de l'utilisateur connecté.
        """
        response = await client.get(
            "/api/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "email" in data or "id" in data

    async def test_get_current_user_without_token(self, client: AsyncClient):
        """
        Test: GET /api/auth/me sans token échoue.
        """
        response = await client.get("/api/auth/me")

        assert response.status_code in [401, 403]

    async def test_get_current_user_with_invalid_token(self, client: AsyncClient):
        """
        Test: GET /api/auth/me avec token invalide échoue.
        """
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer token_invalide_12345"}
        )

        assert response.status_code in [401, 403]

    async def test_get_current_user_with_expired_token(self, client: AsyncClient):
        """
        Test: GET /api/auth/me avec token expiré échoue.

        Note: On génère un token avec une date d'expiration passée.
        """
        from jose import jwt
        from datetime import datetime, timedelta
        from config import settings

        # Token expiré depuis 1 heure
        expired_token = jwt.encode(
            {
                "sub": "fake-user-id",
                "exp": datetime.utcnow() - timedelta(hours=1)
            },
            settings.secret_key,
            algorithm=settings.algorithm
        )

        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code in [401, 403]


class TestProtectedRoutes:
    """Tests de protection des routes sensibles."""

    async def test_protected_route_requires_auth(self, client: AsyncClient):
        """
        Test: Les routes protégées refusent les requêtes sans auth.
        """
        protected_routes = [
            "/api/demandes",
            "/api/demandes/categories",
            "/api/demandes/services",
            "/api/users",
        ]

        for route in protected_routes:
            response = await client.get(route)
            assert response.status_code in [401, 403], f"Route {route} n'est pas protégée"

    async def test_protected_route_accepts_valid_auth(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """
        Test: Les routes protégées acceptent les requêtes avec auth valide.
        """
        response = await client.get(
            "/api/demandes/categories",
            headers=auth_headers
        )

        assert response.status_code == 200


class TestServiceAuthEndpoints:
    """Tests d'authentification spécifique GeoClic Services (agents terrain)."""

    async def test_service_login_endpoint_exists(self, client: AsyncClient):
        """
        Test: L'endpoint de login services existe.
        """
        response = await client.post(
            "/api/services/auth/login",
            json={"email": "test@test.fr", "password": "test"}
        )

        # 401 = endpoint existe mais identifiants invalides
        # 422 = endpoint existe mais format invalide
        assert response.status_code in [401, 422, 400]

    async def test_service_login_with_invalid_credentials(self, client: AsyncClient):
        """
        Test: Login services avec identifiants invalides échoue.
        """
        response = await client.post(
            "/api/services/auth/login",
            json={
                "email": "agent.inexistant@test.fr",
                "password": "mauvais_mdp"
            }
        )

        assert response.status_code in [401, 400]
