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

# Copier le build dans /services/ pour matcher le base path
COPY --from=builder /app/dist /usr/share/nginx/html/services

# Configuration nginx pour SPA avec base /services/
RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    location /services/ { \
        alias /usr/share/nginx/html/services/; \
        try_files $uri $uri/ /services/index.html; \
    } \
    \
    location / { \
        return 301 /services/; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
