# ═══════════════════════════════════════════════════════════════════════════════
# Dockerfile - GéoClic Fleet Manager
# Multi-stage: Build Vue.js frontend + Python API runtime with SSH/rsync
# ═══════════════════════════════════════════════════════════════════════════════

# --- Stage 1: Build Vue.js frontend ---
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY fleet/web/package.json fleet/web/package-lock.json* ./
RUN npm install
COPY fleet/web/ ./
RUN npm run build

# --- Stage 2: Runtime ---
FROM python:3.11-slim

# Installer SSH client + rsync + curl + openssl (nécessaires pour le fleet script)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    rsync \
    curl \
    openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installer les dépendances Python
COPY fleet/api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'API fleet
COPY fleet/api/ ./

# Copier le frontend build
COPY --from=frontend-build /build/dist /app/web/dist

# Copier le script fleet (sera aussi accessible via volume)
COPY fleet/geoclic-fleet.sh /opt/geoclic/fleet/geoclic-fleet.sh
RUN chmod +x /opt/geoclic/fleet/geoclic-fleet.sh

EXPOSE 5555

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5555"]
