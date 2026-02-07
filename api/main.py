"""
═══════════════════════════════════════════════════════════════════════════════
GéoClic Suite V14 - API FastAPI
═══════════════════════════════════════════════════════════════════════════════
Point d'entrée de l'API REST pour GéoClic Suite:
- GéoClic Data (Admin)
- GéoClic SIG Desktop
- GéoClic Mobile
- App Citoyen (Portail Citoyen)
- GéoClic Demandes (Back-office demandes citoyennes)
"""

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager
from pathlib import Path
import traceback
import logging
import time
import os

from config import settings

# ═══════════════════════════════════════════════════════════════════════════════
# SENTRY - MONITORING & ERROR TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

if settings.sentry_dsn:
    import sentry_sdk
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        # Trace 10% des requêtes pour le monitoring de performance (configurable)
        traces_sample_rate=settings.sentry_traces_sample_rate,
        # Envoyer les infos de la requête HTTP (URL, méthode, headers)
        send_default_pii=False,  # Pas de données personnelles (RGPD)
        # Attacher l'URL et la méthode à chaque erreur
        enable_tracing=True,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING STRUCTURÉ
# ═══════════════════════════════════════════════════════════════════════════════

logger = logging.getLogger("geoclic")


def setup_logging():
    """Configure le logging structuré pour la production."""
    log_level = logging.DEBUG if settings.debug else logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Handler console avec format structuré
    handler = logging.StreamHandler()
    handler.setLevel(log_level)

    if settings.debug:
        # Format lisible en développement
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # Format JSON en production (facilite l'analyse avec ELK/Loki/etc.)
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                if record.exc_info and record.exc_info[0]:
                    log_entry["exception"] = self.formatException(record.exc_info)
                return str(log_entry)

        formatter = JSONFormatter()

    handler.setFormatter(formatter)

    # Éviter les handlers dupliqués
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    # Réduire le bruit des loggers tiers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )


setup_logging()


def ensure_photo_directories():
    """Crée les répertoires de stockage des photos si nécessaire."""
    try:
        base_path = Path(settings.photo_storage_path)
        demandes_path = base_path / "demandes"

        # Créer les répertoires
        base_path.mkdir(parents=True, exist_ok=True)
        demandes_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Répertoire photos: {base_path}")
        logger.info(f"Répertoire demandes: {demandes_path}")
    except PermissionError as e:
        logger.warning(f"Impossible de créer le répertoire photos: {e}")
    except Exception as e:
        logger.warning(f"Erreur lors de la création des répertoires photos: {e}")


from database import engine, create_tables
from routers import auth, points, lexique, projects, sync, photos, stats, users, champs, qrcodes, ogs, imports, postgis, sig, public, demandes, zones, services
from routers import settings as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    # Démarrage
    logger.info("GéoClic Suite V14 API - Démarrage...")
    if settings.sentry_dsn:
        logger.info(f"Sentry activé (env: {settings.sentry_environment})")
    else:
        logger.info("Sentry non configuré (SENTRY_DSN vide)")
    await create_tables()
    logger.info("Base de données connectée")
    ensure_photo_directories()
    yield
    # Arrêt
    logger.info("GéoClic Suite V14 API - Arrêt...")
    await engine.dispose()


app = FastAPI(
    title="GéoClic Suite V14 API",
    description="""
    API REST unifiée pour la gestion territoriale des collectivités.

    ## Applications connectées

    * **GéoClic Data** - Administration web (Vue 3)
    * **GéoClic SIG Desktop** - Application cartographique (Flutter)
    * **GéoClic Mobile** - Relevés terrain (Flutter)
    * **App Citoyen** - Signalements citoyens (Flutter APK)
    * **GéoClic Demandes** - Back-office demandes citoyennes (Vue 3)

    ## Fonctionnalités principales

    * **Points** - CRUD pour les points géographiques (POINT, LINE, POLYGON)
    * **Lexique** - Gestion des menus en cascade (6 niveaux)
    * **Projets** - Gestion des projets/chantiers
    * **Sync** - Synchronisation bidirectionnelle Mobile ↔ Serveur
    * **Photos** - Upload et gestion des photos terrain
    * **QR Codes** - Génération et scan (format hybride)
    * **Demandes Citoyens** - Workflow complet de gestion des signalements
    * **Statistiques** - Tableaux de bord et exports

    ## Workflow de validation (Points)

    1. `draft` - Brouillon (modifiable)
    2. `pending` - Soumis pour validation
    3. `validated` - Validé par modérateur
    4. `published` - Publié dans OGS

    ## Workflow demandes citoyens

    1. `nouveau` - Nouvelle demande reçue
    2. `en_moderation` - En attente de validation (optionnel)
    3. `envoye` - Transmise au service compétent (auto ou manuelle)
    4. `accepte` - Acceptée par le service (optionnel)
    5. `en_cours` - Prise en charge par un agent
    6. `planifie` - Intervention planifiée
    7. `traite` - Résolu
    8. `rejete` / `cloture` - Fermé
    """,
    version="14.0.0",
    lifespan=lifespan,
)

# Middleware pour Private Network Access (Chrome security)
# Permet les requêtes depuis IP publique vers IP privée
class PrivateNetworkAccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("Origin", "")

        # Handle preflight requests for Private Network Access
        if request.method == "OPTIONS":
            # Check if this is a Private Network Access preflight
            if request.headers.get("Access-Control-Request-Private-Network") == "true":
                response = Response(status_code=204)
                response.headers["Access-Control-Allow-Private-Network"] = "true"
                response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
                response.headers["Access-Control-Allow-Methods"] = "*"
                response.headers["Access-Control-Allow-Headers"] = "*"
                response.headers["Access-Control-Allow-Credentials"] = "true"
                return response

        response = await call_next(request)

        # Add Private Network Access header to all responses
        response.headers["Access-Control-Allow-Private-Network"] = "true"

        # Si CORS wildcard avec credentials, on doit renvoyer l'origine exacte
        if settings.allowed_origins == ["*"] and origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response

app.add_middleware(PrivateNetworkAccessMiddleware)

# CORS pour Flutter Web et Mobile
# Note: Avec allow_credentials=True, on ne peut pas utiliser "*" comme origine
# Si wildcard configuré, on utilise allow_origin_regex pour accepter toutes les origines
cors_use_wildcard = settings.allowed_origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[] if cors_use_wildcard else settings.allowed_origins,
    allow_origin_regex=r".*" if cors_use_wildcard else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Gestionnaire d'exceptions global pour garantir les headers CORS
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Capture toutes les exceptions non gérées et retourne une réponse JSON.
    Cela garantit que les headers CORS sont ajoutés même en cas d'erreur 500.
    Les erreurs sont envoyées à Sentry si configuré.
    """
    logger.error(f"Erreur non gérée sur {request.method} {request.url.path}: {exc}", exc_info=True)

    # Envoyer à Sentry si configuré
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.capture_exception(exc)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erreur interne du serveur",
            "error": str(exc) if settings.debug else "Une erreur s'est produite",
        },
    )

# Inclusion des routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentification"])
app.include_router(points.router, prefix="/api/points", tags=["Points"])
app.include_router(lexique.router, prefix="/api/lexique", tags=["Lexique"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projets"])
app.include_router(sync.router, prefix="/api/sync", tags=["Synchronisation"])
app.include_router(photos.router, prefix="/api/photos", tags=["Photos"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistiques"])
app.include_router(users.router, prefix="/api/users", tags=["Utilisateurs"])
app.include_router(champs.router, prefix="/api/champs", tags=["Champs dynamiques"])
app.include_router(qrcodes.router, prefix="/api/qrcodes", tags=["QR Codes"])
app.include_router(ogs.router, prefix="/api/ogs", tags=["OneGeo Suite"])
app.include_router(imports.router, prefix="/api/imports", tags=["Import de données"])
app.include_router(postgis.router, prefix="/api/postgis", tags=["PostGIS externe"])
app.include_router(sig.router, prefix="/api/sig", tags=["SIG Desktop"])
app.include_router(public.router, prefix="/api/public", tags=["Portail Citoyen"])
app.include_router(demandes.router, prefix="/api/demandes", tags=["Demandes Citoyens"])
app.include_router(zones.router, prefix="/api/zones", tags=["Zones géographiques"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Paramètres système"])
app.include_router(services.router, prefix="/api/services", tags=["GeoClic Services"])


@app.get("/", tags=["Health"])
async def root():
    """Point de santé de l'API."""
    return {
        "status": "ok",
        "app": "GéoClic Suite V14 API",
        "version": "14.0.0",
    }


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Vérification de santé détaillée avec test réel de la DB."""
    from database import AsyncSessionLocal

    health = {
        "status": "healthy",
        "version": "14.0.0",
        "checks": {},
    }

    # Vérification de la base de données
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        health["checks"]["database"] = {"status": "ok"}
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["database"] = {"status": "error", "detail": str(e)}
        logger.error(f"Health check DB failed: {e}")

    # Vérification du stockage photos
    photo_path = Path(settings.photo_storage_path)
    if photo_path.exists() and os.access(str(photo_path), os.W_OK):
        health["checks"]["storage"] = {"status": "ok", "path": str(photo_path)}
    else:
        health["status"] = "degraded"
        health["checks"]["storage"] = {"status": "error", "detail": "Répertoire photos inaccessible"}

    # Vérification Sentry
    if settings.sentry_dsn:
        health["checks"]["sentry"] = {"status": "ok", "environment": settings.sentry_environment}
    else:
        health["checks"]["sentry"] = {"status": "disabled"}

    return health
