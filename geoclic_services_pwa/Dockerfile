# Stage 1: Build
FROM node:18-alpine AS builder

WORKDIR /app

# Copier package.json et installer les dépendances
COPY package*.json ./
RUN npm install

# Copier le code source
COPY . .

# Build
RUN npm run build

# Stage 2: Serve avec nginx
FROM nginx:alpine

# Copier le build dans /terrain/ pour matcher le base path
COPY --from=builder /app/dist /usr/share/nginx/html/terrain

# Copier les fichiers PWA (manifest, sw, icons, offline.html)
COPY --from=builder /app/public /usr/share/nginx/html/terrain

# Configuration nginx pour SPA PWA avec base /terrain/
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    location /terrain/ { \
        alias /usr/share/nginx/html/terrain/; \
        try_files $uri $uri/ /terrain/index.html; \
    } \
    \
    # Service Worker sans cache \
    location = /terrain/sw.js { \
        alias /usr/share/nginx/html/terrain/sw.js; \
        expires off; \
        add_header Cache-Control "no-cache, no-store, must-revalidate"; \
    } \
    \
    location / { \
        return 301 /terrain/; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
