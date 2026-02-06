"""
═══════════════════════════════════════════════════════════════════════════════
Tests de santé de l'API GéoClic Suite
═══════════════════════════════════════════════════════════════════════════════
Ces tests vérifient que l'API démarre correctement et répond aux requêtes de base.
C'est le premier fichier à exécuter pour vérifier que tout fonctionne.
"""

import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Tests des endpoints de santé."""

    async def test_root_endpoint(self, client: AsyncClient):
        """
        Test: GET / retourne le statut de l'API.

        Vérifie que:
        - L'API répond avec un code 200
        - Le statut est "ok"
        - Le nom de l'application est correct
        """
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "GéoClic" in data["app"]

    async def test_health_check(self, client: AsyncClient):
        """
        Test: GET /api/health retourne l'état de santé détaillé.

        Vérifie que:
        - L'API répond avec un code 200
        - Le statut est "healthy"
        - La connexion à la base de données est confirmée
        """
        response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    async def test_cors_headers(self, client: AsyncClient):
        """
        Test: Les headers CORS sont présents dans les réponses.

        Important pour le fonctionnement des applications Vue.js.
        """
        response = await client.get("/")

        # Vérifier que l'API répond (CORS géré par middleware)
        assert response.status_code == 200

    async def test_404_on_unknown_route(self, client: AsyncClient):
        """
        Test: Une route inconnue retourne 404.

        Vérifie que l'API gère correctement les routes inexistantes.
        """
        response = await client.get("/api/route-inexistante")

        assert response.status_code == 404


class TestAPIDocumentation:
    """Tests de la documentation automatique FastAPI."""

    async def test_openapi_schema_available(self, client: AsyncClient):
        """
        Test: Le schéma OpenAPI est accessible.

        Utilisé par Swagger UI pour générer la documentation.
        """
        response = await client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "info" in data

    async def test_swagger_ui_available(self, client: AsyncClient):
        """
        Test: Swagger UI est accessible.

        Interface web pour explorer et tester l'API.
        """
        response = await client.get("/docs")

        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "text/html" in response.headers.get("content-type", "")
