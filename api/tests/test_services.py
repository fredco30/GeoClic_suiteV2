"""
═══════════════════════════════════════════════════════════════════════════════
Tests du module Services Municipaux - GéoClic Suite
═══════════════════════════════════════════════════════════════════════════════
Ces tests vérifient le bon fonctionnement des endpoints de gestion des
services municipaux et des agents terrain.

Endpoints testés:
- GET /api/demandes/services - Liste des services
- POST /api/demandes/services - Créer un service
- GET /api/demandes/services/{id} - Détail d'un service
- PUT /api/demandes/services/{id} - Modifier un service
- DELETE /api/demandes/services/{id} - Supprimer un service
- GET /api/demandes/services/{id}/agents - Agents d'un service
"""

import pytest
from httpx import AsyncClient
from faker import Faker

# Générateur de données de test
fake = Faker('fr_FR')


def generate_service_data() -> dict:
    """Génère des données valides pour créer un service."""
    return {
        "nom": f"Service {fake.word()}",
        "description": fake.sentence(),
        "couleur": fake.hex_color(),
        "email": fake.company_email(),
        "actif": True
    }


class TestServicesListEndpoints:
    """Tests de la liste des services."""

    async def test_list_services(self, client: AsyncClient, auth_headers: dict):
        """
        Test: GET /api/demandes/services retourne la liste des services.

        Vérifie que:
        - L'endpoint répond avec un code 200
        - La réponse est une liste
        """
        response = await client.get(
            "/api/demandes/services",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_services_without_auth_fails(self, client: AsyncClient):
        """
        Test: Lister les services sans authentification échoue.
        """
        response = await client.get("/api/demandes/services")

        assert response.status_code in [401, 403]


class TestServicesCRUDEndpoints:
    """Tests CRUD des services."""

    async def test_create_service(self, client: AsyncClient, auth_headers: dict):
        """
        Test: POST /api/demandes/services crée un nouveau service.

        Vérifie que:
        - Le service est créé avec un code 200/201
        - Les données retournées correspondent à ce qui a été envoyé
        """
        service_data = generate_service_data()

        response = await client.post(
            "/api/demandes/services",
            headers=auth_headers,
            json=service_data
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["nom"] == service_data["nom"]
        assert "id" in data

    async def test_create_service_with_invalid_data(self, client: AsyncClient, auth_headers: dict):
        """
        Test: Créer un service avec des données invalides échoue.
        """
        invalid_data = {
            "nom": "",  # Nom vide = invalide
        }

        response = await client.post(
            "/api/demandes/services",
            headers=auth_headers,
            json=invalid_data
        )

        assert response.status_code == 422

    async def test_get_service_by_id(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_service: dict
    ):
        """
        Test: GET /api/demandes/services/{id} retourne le détail d'un service.
        """
        service_id = test_service["id"]

        response = await client.get(
            f"/api/demandes/services/{service_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nom"] == test_service["nom"]

    async def test_get_service_not_found(self, client: AsyncClient, auth_headers: dict):
        """
        Test: GET /api/demandes/services/{id} avec un ID inexistant retourne 404.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(
            f"/api/demandes/services/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_update_service(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_service: dict
    ):
        """
        Test: PUT /api/demandes/services/{id} modifie un service.
        """
        service_id = test_service["id"]
        updated_data = {
            "nom": "Service Modifié",
            "description": "Description modifiée",
            "couleur": "#FF0000",
            "actif": True
        }

        response = await client.put(
            f"/api/demandes/services/{service_id}",
            headers=auth_headers,
            json=updated_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nom"] == "Service Modifié"

    async def test_delete_service(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session
    ):
        """
        Test: DELETE /api/demandes/services/{id} supprime un service.

        Note: On crée un service spécifique pour ce test car le fixture
        test_service est utilisé par d'autres tests.
        """
        # Créer un service à supprimer
        from sqlalchemy import text
        import uuid

        service_id = str(uuid.uuid4())
        await db_session.execute(
            text("""
                INSERT INTO demandes_services (id, nom, actif)
                VALUES (CAST(:id AS uuid), 'Service à supprimer', true)
            """),
            {"id": service_id}
        )
        await db_session.commit()

        # Supprimer
        response = await client.delete(
            f"/api/demandes/services/{service_id}",
            headers=auth_headers
        )

        assert response.status_code == 200

        # Vérifier que le service n'existe plus
        response = await client.get(
            f"/api/demandes/services/{service_id}",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestServicesAgentsEndpoints:
    """Tests des agents des services."""

    async def test_list_service_agents(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_service: dict
    ):
        """
        Test: GET /api/demandes/services/{id}/agents retourne les agents.
        """
        service_id = test_service["id"]

        response = await client.get(
            f"/api/demandes/services/{service_id}/agents",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_create_service_agent(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_service: dict
    ):
        """
        Test: POST /api/demandes/services/{id}/agents crée un agent.
        """
        service_id = test_service["id"]
        agent_data = {
            "nom": "Dupont",
            "prenom": "Jean",
            "email": f"jean.dupont.{service_id[:8]}@test.fr",
            "role": "agent",
            "actif": True
        }

        response = await client.post(
            f"/api/demandes/services/{service_id}/agents",
            headers=auth_headers,
            json=agent_data
        )

        # 200 ou 201 selon l'implémentation
        assert response.status_code in [200, 201]


class TestServicesStatsEndpoints:
    """Tests des statistiques des services."""

    async def test_get_services_stats(self, client: AsyncClient, auth_headers: dict):
        """
        Test: GET /api/demandes/services/stats/all retourne les statistiques.
        """
        response = await client.get(
            "/api/demandes/services/stats/all",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))


class TestServicesAssignmentEndpoints:
    """Tests d'assignation des demandes aux services."""

    async def test_assign_demande_to_service(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_service: dict,
        test_demande: dict
    ):
        """
        Test: POST /api/demandes/services/{id}/assign-demande/{demande_id}
        assigne une demande à un service.
        """
        service_id = test_service["id"]
        demande_id = test_demande["id"]

        response = await client.post(
            f"/api/demandes/services/{service_id}/assign-demande/{demande_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
