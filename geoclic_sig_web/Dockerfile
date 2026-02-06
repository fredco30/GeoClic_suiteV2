# ═══════════════════════════════════════════════════════════════════════════════
# Dockerfile pour GéoClic SIG Web (Vue 3 + Leaflet)
# ═══════════════════════════════════════════════════════════════════════════════

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build arg for API URL (vide = detection automatique via URLs relatives)
ARG VITE_API_URL=
ENV VITE_API_URL=$VITE_API_URL

# Build
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

LABEL maintainer="GéoClic Team"
LABEL version="1.0.0"
LABEL description="GéoClic SIG Web - Application cartographique"

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/sig/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
