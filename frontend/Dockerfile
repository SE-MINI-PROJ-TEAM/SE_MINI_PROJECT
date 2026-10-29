# React SPA served by nginx, which also reverse-proxies /api to the Flask container.
# Build context is the repository root:  docker build -f frontend/Dockerfile .
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM nginx:1.27-alpine
RUN apk add --no-cache openssl && rm /etc/nginx/conf.d/default.conf
COPY frontend/docker/nginx.conf /etc/nginx/conf.d/app.conf
COPY frontend/docker/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY frontend/docker/locations.conf /etc/nginx/snippets/locations.conf
COPY --chmod=755 frontend/docker/40-selfsigned-cert.sh /docker-entrypoint.d/40-selfsigned-cert.sh
COPY frontend/docker/api-security-headers.conf /etc/nginx/snippets/api-security-headers.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80 443
HEALTHCHECK --interval=5s --timeout=3s --retries=12 CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
