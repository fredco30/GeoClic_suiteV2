# ═══════════════════════════════════════════════════════════════════════════════
# Dockerfile pour Portail Citoyen (Vue 3)
# Version: 14.3
# ═══════════════════════════════════════════════════════════════════════════════

# Stage 1: Build
FROM node:20-alpine as build-stage

LABEL maintainer="GéoClic Team"
LABEL version="14.3"
LABEL description="Portail Citoyen - Interface de signalement pour les citoyens"

WORKDIR /app

# Copier les fichiers de dépendances
COPY package*.json ./

# Installer les dépendances (npm install car pas de package-lock.json)
RUN npm install

# Copier le code source
COPY . .

# Variables d'environnement de build
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

# Build de production (vite build directement pour éviter vue-tsc incompatible)
RUN npx vite build

# Stage 2: Production avec Nginx
FROM nginx:alpine as production-stage

LABEL maintainer="GéoClic Team"
LABEL version="14.3"
LABEL description="Portail Citoyen - Interface de signalement pour les citoyens"

# Copier la configuration Nginx personnalisée
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copier les fichiers buildés
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Port exposé
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Commande de démarrage
CMD ["nginx", "-g", "daemon off;"]
