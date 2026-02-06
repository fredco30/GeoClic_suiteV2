"""
Configuration de l'API GéoClic V12 Pro.

IMPORTANT: Les valeurs sensibles (SECRET_KEY, DATABASE_URL) doivent
être définies via des variables d'environnement ou un fichier .env.
Ne JAMAIS laisser les valeurs par défaut en production.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Configuration de l'application."""

    # Base de données
    # Format: postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE
    database_url: str = "postgresql+asyncpg://geoclic:geoclic_secure_password@db:5432/geoclic_db"

    # Sécurité
    # IMPORTANT: Doit être définie via variable d'environnement SECRET_KEY ou JWT_SECRET_KEY
    secret_key: str = os.environ.get("JWT_SECRET_KEY", os.environ.get("SECRET_KEY", ""))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8  # 8 heures (réduit depuis 24h)

    # CORS - Origines autorisées
    # En production, définir CORS_ORIGINS avec les domaines réels (ex: "https://geoclic.fr")
    # En dev, les origines localhost sont utilisées par défaut
    allowed_origins_str: str = os.environ.get("CORS_ORIGINS", ",".join([
        # Localhost HTTP (développement uniquement)
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:8000",
        # Localhost HTTPS
        "https://localhost:3000",
        "https://localhost:3001",
        "https://localhost:5443",
        "https://localhost:8443",
        "https://127.0.0.1:5443",
        "https://127.0.0.1:8443",
    ]))

    @property
    def allowed_origins(self) -> List[str]:
        if self.allowed_origins_str == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins_str.split(",")]

    # Debug - TOUJOURS False en production
    debug: bool = os.environ.get("DEBUG", "false").lower() == "true"

    # Stockage photos
    photo_storage_path: str = "/app/storage/photos"
    max_photo_size_mb: int = 10
    photo_thumbnail_size: int = 300

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Vérification de sécurité au démarrage
if not settings.secret_key:
    import warnings
    warnings.warn(
        "SÉCURITÉ CRITIQUE: JWT_SECRET_KEY non définie! "
        "Définissez la variable d'environnement JWT_SECRET_KEY avec une clé aléatoire de 32+ caractères. "
        "Exemple: openssl rand -hex 32",
        RuntimeWarning,
        stacklevel=1,
    )
