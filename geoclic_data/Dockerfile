# ===============================================================================
# Dockerfile pour GéoClic Data Admin (Vue 3 + Vuetify)
# Version: 14.3
# ===============================================================================

# Stage 1: Build
FROM node:20-alpine as build-stage

LABEL maintainer="GéoClic Team"
LABEL version="14.3"
LABEL description="Interface d'administration GéoClic Data"

WORKDIR /app

# Copier les fichiers de dependances
COPY package*.json ./

# Installer les dependances (npm install car pas de package-lock.json)
RUN npm install

# Copier le code source
COPY . .

# Variables d'environnement de build (vide = détection automatique dans api.ts)
ARG VITE_API_URL=
ENV VITE_API_URL=$VITE_API_URL

# Build de production (build-only pour eviter vue-tsc)
RUN npm run build-only

# Stage 2: Production avec Nginx
FROM nginx:alpine as production-stage

LABEL maintainer="GéoClic Team"
LABEL version="14.3"
LABEL description="Interface d'administration GéoClic Data"

# Copier la configuration Nginx personnalisee
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copier les fichiers buildes
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Port expose
EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Commande de demarrage
CMD ["nginx", "-g", "daemon off;"]
