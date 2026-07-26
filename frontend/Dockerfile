FROM node:20-bookworm-slim AS build

WORKDIR /app

COPY package*.json ./

RUN npm ci --no-audit --no-fund

COPY . .

ARG VITE_API_URL=http://localhost:8000/api/v1
ARG VITE_MAIL_PREVIEW_URL=http://localhost:8025
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_MAIL_PREVIEW_URL=$VITE_MAIL_PREVIEW_URL

RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80