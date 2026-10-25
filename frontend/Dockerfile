# Build from the repo root, since the npm workspace lockfile lives there:
#   docker build -f frontend/Dockerfile .

# ── Stage 1: build the Vite bundle ────────────────────────────────────────────
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
COPY frontend/package.json ./frontend/
RUN npm ci --workspace frontend --ignore-scripts

COPY frontend/ ./frontend/

# Vite inlines VITE_* variables at build time, so they arrive as build args.
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_GOOGLE_CLIENT_ID=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID

RUN npm run build --workspace frontend


# ── Stage 2: serve the static files ───────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html

EXPOSE 80
