# build the SPA, then serve it (and reverse-proxy the api) with nginx

FROM node:22-alpine AS build
WORKDIR /app

# the app is served behind nginx on the same origin, so the api base is relative
# (empty string -> apiClient/fetch/ws all resolve against the page origin)
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# install deps first for layer caching; .npmrc carries legacy-peer-deps=true
COPY package.json package-lock.json .npmrc ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime

# our server block: serves the SPA, proxies /api (+ websockets) and /media
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
