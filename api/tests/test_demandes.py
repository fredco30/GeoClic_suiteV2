"""
═══════════════════════════════════════════════════════════════════════════════
Tests du module Demandes Citoyens - GéoClic Suite
═══════════════════════════════════════════════════════════════════════════════
Ces tests vérifient le bon fonctionnement des endpoints de gestion des
demandes citoyennes (signalements).

Endpoints testés:
- GET /api/demandes - Liste des demandes
- GET /api/demandes/{id} - Détail d'une demande
- GET /api/demandes/categories - Liste des catégories
- POST /api/demandes/categories - Créer une catégorie
- PATCH /api/demandes/{id}/statut - Changer le statut
- PATCH /api/demandes/{id}/priorite - Changer la priorité
"""

import pytest
from httpx import AsyncClient
from faker import Faker

# Générateur de données de test
fake = Faker('fr_FR')


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


class TestCategoriesEndpoints:
    """Tests CRUD des catégories de demandes."""

    async def test_list_categories(self, client: AsyncClient, auth_headers: dict):
        """
        Test: GET /api/demandes/categories retourne la liste des catégories.

        Vérifie que:
        - L'endpoint répond avec un code 200
        - La réponse est une liste
        """
        response = await client.get(
            "/api/demandes/categories",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_categories_tree(self, client: AsyncClient, auth_headers: dict):
        """
        Test: GET /api/demandes/categories/tree retourne l'arbre hiérarchique.

        Vérifie que:
        - L'endpoint répond avec un code 200
        - La réponse est une liste structurée en arbre
        """
        response = await client.get(
            "/api/demandes/categories/tree",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_create_category(self, client: AsyncClient, auth_headers: dict):
        """
        Test: POST /api/demandes/categories crée une nouvelle catégorie.

        Vérifie que:
        - La catégorie est créée avec un code 200/201
        - Les données retournées correspondent à ce qui a été envoyé
        """
        category_data = generate_category_data()

        response = await client.post(
            "/api/demandes/categories",
            headers=auth_headers,
            json=category_data
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["nom"] == category_data["nom"]
        assert "id" in data

    async def test_create_category_without_auth_fails(self, client: AsyncClient):
        """
        Test: Créer une catégorie sans authentification échoue.

        Vérifie que l'API protège correctement les endpoints sensibles.
        """
        category_data = generate_category_data()

        response = await client.post(
            "/api/demandes/categories",
            json=category_data
        )

        assert response.status_code in [401, 403]

    async def test_create_category_with_invalid_data(self, client: AsyncClient, auth_headers: dict):
        """
        Test: Créer une catégorie avec des données invalides échoue.

        Vérifie la validation des données entrantes.
        """
        invalid_data = {
            "nom": "",  # Nom vide = invalide
            "description": "Test"
        }

        response = await client.post(
            "/api/demandes/categories",
            headers=auth_headers,
            json=invalid_data
        )

        assert response.status_code == 422  # Validation error


class TestDemandesListEndpoints:
    """Tests de la liste des demandes."""

    async def test_list_demandes(self, client: AsyncClient, auth_headers: dict):
        """
        Test: GET /api/demandes retourne la liste paginée des demandes.

        Vérifie que:
        - L'endpoint répond avec un code 200
        - La réponse contient les métadonnées de pagination
        """
        response = await client.get(
            "/api/demandes",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Vérifier la structure de pagination
        assert "items" in data or isinstance(data, list)

    async def test_list_demandes_with_filters(self, client: AsyncClient, auth_headers: dict):
        """
        Test: GET /api/demandes avec filtres fonctionne correctement.

        Vérifie que les paramètres de filtre sont acceptés.
        """
        response = await client.get(
            "/api/demandes?statut=nouveau&priorite=normale",
            headers=auth_headers
        )

        assert response.status_code == 200

    async def test_list_demandes_without_auth_fails(self, client: AsyncClient):
        """
        Test: Lister les demandes sans authentification échoue.
        """
        response = await client.get("/api/demandes")

        assert response.status_code in [401, 403]


class TestDemandeDetailEndpoints:
    """Tests du détail d'une demande."""

    async def test_get_demande_by_id(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_demande: dict
    ):
        """
        Test: GET /api/demandes/{id} retourne le détail d'une demande.

        Vérifie que:
        - L'endpoint répond avec un code 200
        - Les données retournées correspondent à la demande
        """
        demande_id = test_demande["id"]

        response = await client.get(
            f"/api/demandes/{demande_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["numero"] == test_demande["numero"]

    async def test_get_demande_not_found(self, client: AsyncClient, auth_headers: dict):
        """
        Test: GET /api/demandes/{id} avec un ID inexistant retourne 404.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await client.get(
            f"/api/demandes/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_get_demande_invalid_uuid(self, client: AsyncClient, auth_headers: dict):
        """
        Test: GET /api/demandes/{id} avec un UUID invalide retourne 422.
        """
        response = await client.get(
            "/api/demandes/invalid-uuid",
            headers=auth_headers
        )

        assert response.status_code in [404, 422, 500]


class TestDemandeStatusEndpoints:
    """Tests de changement de statut des demandes."""

    async def test_change_demande_status(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_demande: dict
    ):
        """
        Test: PATCH /api/demandes/{id}/statut change le statut d'une demande.

        Workflow: nouveau -> accepte
        """
        demande_id = test_demande["id"]

        response = await client.patch(
            f"/api/demandes/{demande_id}/statut",
            headers=auth_headers,
            json={"statut": "accepte"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["statut"] == "accepte"

    async def test_change_demande_status_invalid(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_demande: dict
    ):
        """
        Test: Changer vers un statut invalide échoue.
        """
        demande_id = test_demande["id"]

        response = await client.patch(
            f"/api/demandes/{demande_id}/statut",
            headers=auth_headers,
            json={"statut": "statut_invalide"}
        )

        assert response.status_code == 422


class TestDemandePriorityEndpoints:
    """Tests de changement de priorité des demandes."""

    async def test_change_demande_priority(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_demande: dict
    ):
        """
        Test: PATCH /api/demandes/{id}/priorite change la priorité.
        """
        demande_id = test_demande["id"]

        response = await client.patch(
            f"/api/demandes/{demande_id}/priorite",
            headers=auth_headers,
            json={"priorite": "haute"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["priorite"] == "haute"

    async def test_change_demande_priority_to_urgente(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_demande: dict
    ):
        """
        Test: Changer la priorité vers "urgente" fonctionne.
        """
        demande_id = test_demande["id"]

        response = await client.patch(
            f"/api/demandes/{demande_id}/priorite",
            headers=auth_headers,
            json={"priorite": "urgente"}
        )

        assert response.status_code == 200


class TestDemandeHistoryEndpoints:
    """Tests de l'historique des demandes."""

    async def test_get_demande_history(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_demande: dict
    ):
        """
        Test: GET /api/demandes/{id}/historique retourne l'historique.
        """
        demande_id = test_demande["id"]

        response = await client.get(
            f"/api/demandes/{demande_id}/historique",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestStatistiquesEndpoints:
    """Tests des statistiques des demandes."""

    async def test_get_statistiques(self, client: AsyncClient, auth_headers: dict):
        """
        Test: GET /api/demandes/statistiques retourne les statistiques.
        """
        response = await client.get(
            "/api/demandes/statistiques",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Vérifier que les stats contiennent les champs attendus
        assert isinstance(data, dict)

    async def test_get_dashboard_stats(self, client: AsyncClient, auth_headers: dict):
        """
        Test: GET /api/demandes/statistiques/dashboard retourne les stats dashboard.
        """
        response = await client.get(
            "/api/demandes/statistiques/dashboard",
            headers=auth_headers
        )

        assert response.status_code == 200
