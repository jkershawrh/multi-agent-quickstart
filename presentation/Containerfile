FROM registry.access.redhat.com/ubi9/nodejs-22 AS build
WORKDIR /opt/app-root/src
COPY --chown=1001:0 package*.json ./
RUN npm ci
COPY --chown=1001:0 . .
RUN npm run build

FROM docker.io/nginxinc/nginx-unprivileged:1.27-alpine
COPY --from=build /opt/app-root/src/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
