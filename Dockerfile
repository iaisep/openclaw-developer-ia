FROM node:22-slim

RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Instalar openclaw y luego sus peer deps dentro del propio paquete para correcta resolución
RUN npm install -g openclaw@latest && \
    cd /usr/local/lib/node_modules/openclaw && \
    npm install --no-save grammy @buape/carbon @larksuiteoapi/node-sdk "@slack/web-api@7.15.0" "@slack/bolt@4.7.0"

RUN mkdir -p /root/.openclaw

EXPOSE 18789

CMD ["node", "/usr/local/lib/node_modules/openclaw/dist/index.js", "gateway"]
