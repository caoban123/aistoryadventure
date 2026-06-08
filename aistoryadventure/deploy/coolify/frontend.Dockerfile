FROM nginx:1.27-alpine

WORKDIR /usr/share/nginx/html

COPY frontend/ ./
COPY deploy/coolify/frontend.nginx.conf /etc/nginx/conf.d/default.conf
COPY deploy/coolify/frontend-entrypoint.sh /docker-entrypoint.d/40-ai-story-config.sh

RUN sed -i 's/\r$//' /docker-entrypoint.d/40-ai-story-config.sh && \
    chmod +x /docker-entrypoint.d/40-ai-story-config.sh

EXPOSE 8080
