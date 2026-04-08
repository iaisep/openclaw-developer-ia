# Arquitectura del Sistema

## Visión de Alto Nivel

```mermaid
graph LR
    subgraph Internet
        GH[GitHub\nUniversidad-ISEP/Odoo16UISEP]
        USER[Usuario / Solicitante]
    end

    subgraph Servidor_57["Servidor .57 (189.195.191.16) — Jump Host / Proxy"]
        TRAEFIK[Traefik Proxy]
        JENKINS[Jenkins CI/CD]
        ODOODEV[Odoo DEV\nodoo_latest-w8co804...]
        PGREPLICA[PostgreSQL\nRéplica Read-Only]
    end

    subgraph Servidor_58["Servidor .58 (192.168.100.58) — Nvidia-Coolify (este servidor)"]
        subgraph OpenClaw_Dev["openclaw-developer-ia :18797"]
            MAIN[🏗️ main]
            DEVGIT[💻 dev-odoo-github]
            DEVLOC[🔧 dev-odoo-local]
            DISTRIB[📦 dev-distrib-local]
            VALID[🔍 dev-validator-deploydev]
            DEVOPS[🚀 devops-odoo]
            TICKET[🎫 incidencias-odoo]
            CREATOR[📋 dev-project-creator]
            ARCH[🏛️ dev-project-architect]
        end

        ODOOPROD[Odoo Producción\nodoo-app-prod :3005]
        PGPROD[(PostgreSQL Prod\nodoo-postgres-prod)]
        OLLAMA[Ollama API\n:11435]
        MATTERMOST[Mattermost\n:8065]
    end

    subgraph Externo
        MINIMAX[MiniMax Portal\nMiniMax-M2.5]
        AWS_SES[AWS SES\nSMTP]
        ODOO_PUBLIC[app.universidadisep.com\nXML-RPC]
    end

    USER -->|solicitudes| MAIN
    MAIN --> DEVGIT
    MAIN --> DEVLOC
    DEVGIT -->|SSH + git push| JENKINS
    JENKINS -->|deploy| ODOODEV
    VALID -->|SSH + logs| ODOODEV
    DEVOPS -->|GitHub API| GH
    DEVOPS -->|docker logs| ODOOPROD
    TICKET -->|SSH psql| PGREPLICA
    TICKET -->|XML-RPC| ODOO_PUBLIC
    CREATOR -->|XML-RPC| ODOO_PUBLIC
    ARCH -->|XML-RPC| ODOO_PUBLIC

    ODOOPROD --- PGPROD
    OpenClaw_Dev -->|LLM API| MINIMAX
    OpenClaw_Dev -->|LLM local| OLLAMA
    TICKET -->|email| AWS_SES
    CREATOR -->|email| AWS_SES
    ARCH -->|email| AWS_SES
```

---

## Estructura de Directorios

```
/data/openclaw-developer-ia/
│
├── 📄 Dockerfile                    # Imagen: node:22-slim + openclaw@latest
├── 📄 docker-compose.yml            # Definición del servicio
├── 📄 .env                          # Tokens y credenciales (NO versionado)
│
├── 📁 config/                       # Configuración persistente (→ /root/.openclaw)
│   ├── openclaw.json                # Config principal: modelos, agentes, canales
│   ├── cron/
│   │   └── jobs.json                # Cron jobs programados
│   ├── agents/                      # Datos por agente (sessions, auth, modelos)
│   │   ├── main/
│   │   ├── dev-odoo-github/
│   │   ├── dev-odoo-local/
│   │   ├── dev-distrib-local/
│   │   ├── dev-validator-deploydev/
│   │   ├── devops-odoo/
│   │   ├── incidencias-odoo/
│   │   ├── dev-project-creator/
│   │   └── dev-project-architect/
│   └── canvas/
│       └── index.html               # UI de control
│
├── 📁 workspace/                    # Workspace del agente principal
│   ├── SOUL.md                      # Instrucciones de comportamiento
│   ├── IDENTITY.md                  # Identidad y contexto
│   ├── RULES.md                     # Reglas estrictas de operación
│   ├── TOOLS.md                     # Herramientas y conexiones disponibles
│   ├── AGENTS.md                    # Lista y roles de sub-agentes
│   ├── BOOTSTRAP.md                 # Contexto de arranque
│   └── MEMORY.md                    # Memoria de largo plazo
│
├── 📁 workspaces/                   # Workspaces de sub-agentes
│   ├── dev-odoo-github/
│   ├── dev-odoo-local/
│   ├── dev-distrib-local/
│   ├── devops-odoo/
│   ├── dev-validator-deploydev/
│   ├── incidencias-odoo/
│   │   ├── skills/
│   │   │   ├── fusion-contactos-duplicados/SKILL.md
│   │   │   ├── correccion-credencial-estudiante/SKILL.md
│   │   │   └── notificacion-incidencia/SKILL.md
│   │   ├── procesar.js
│   │   ├── procesar_ticket.py
│   │   └── rpc.js
│   ├── dev-project-creator/
│   │   ├── skills/
│   │   │   └── crear-proyecto-desde-fuente/SKILL.md
│   │   └── cron/
│   │       ├── run.py
│   │       └── email_template.html
│   ├── dev-project-architect/
│   │   ├── skills/
│   │   │   └── analizar-proyecto/
│   │   │       ├── SKILL.md
│   │   │       └── analizar_proyecto.js
│   │   ├── analizar_proyecto.py
│   │   └── memory/
│   ├── dev-validator-deploydev/
│   │   └── check_odoo.py
│   └── DOCUMENTACION_AGENTES.md
│
├── 📁 memory/                       # Memoria global del sistema
│   └── analisis.md                  # Log de proyectos analizados
│
└── 📁 sessions/                     # Sessions de ejecución (NO versionado)
```

---

## Volúmenes Montados (Docker)

```mermaid
graph LR
    subgraph Host ["Host (192.168.100.58)"]
        H1["/data/openclaw-developer-ia/config"]
        H2["/data/openclaw-developer-ia/workspace"]
        H3["/data/openclaw-developer-ia/workspaces/*"]
        H4["/data/odoo-migration/odoo16/addons-extra"]
        H5["/home/maikel/cambios_odoo_local"]
        H6["/.github/keysssh/odoo-dev.pem"]
    end

    subgraph Container ["Container (openclaw-developer-ia)"]
        C1["/root/.openclaw"]
        C2["/root/.openclaw/workspace"]
        C3["/root/.openclaw/workspaces/*"]
        C4["/mnt/odoo-migration-addons"]
        C5["/mnt/cambios-odoo-local"]
        C6["/.keys/odoo-dev.pem (read-only)"]
    end

    H1 --> C1
    H2 --> C2
    H3 --> C3
    H4 --> C4
    H5 --> C5
    H6 --> C6
```

---

## Configuración de Modelos

```mermaid
graph TD
    subgraph Routing ["Routing de Modelos"]
        REQ[Request LLM]
        REQ --> CHECK{¿Heartbeat?}
        CHECK -->|Heartbeat / background| OLLAMA[ollama/qwen2.5-7b-gpu\nLocal :11435\n32k contexto]
        CHECK -->|Tarea principal| PRIMARY[minimax-portal/MiniMax-M2.5\n200k contexto\nReasoning enabled]
        PRIMARY -->|Error / timeout| FALLBACK[minimax-portal/MiniMax-M2.1\n200k contexto\nNo reasoning]
        FALLBACK -->|Error| OLLAMA
    end
```

| Modelo | Proveedor | Contexto | Reasoning | Uso |
|--------|-----------|----------|-----------|-----|
| MiniMax-M2.5 | minimax-portal | 200k | ✅ | Principal |
| MiniMax-M2.5-highspeed | minimax-portal | 200k | ✅ | Alta velocidad |
| MiniMax-M2.1 | minimax-portal | 200k | ❌ | Fallback 1 |
| qwen2.5-7b-gpu | ollama (local) | 32k | ❌ | Heartbeats / Fallback 2 |

---

## Redes Docker

```mermaid
graph LR
    subgraph openclaw-net
        OCA[openclaw-developer-ia]
    end

    subgraph fw8g04s0w0kcc08008owskok["ollama-net (fw8g04...)"]
        OLLAMA2[ollama-api]
        WEBUI[open-webui]
    end

    subgraph r0kgo8o8wg40okg00sgcgsgc["mattermost-net (r0kgo8...)"]
        MATTER[mattermost]
        PGMATTER[postgres-mattermost]
    end

    OCA -.->|LLM API| OLLAMA2
    OCA -.->|mensajes| MATTER
```

---

## Límites del Sistema

| Parámetro | Valor |
|-----------|-------|
| Agentes concurrentes | 50 |
| Sub-agentes por agente | 15 hijos |
| Profundidad de spawn | 3 niveles |
| Timeout por tarea | 86400s (24h) |
| Timeout sub-agente | 900s (15min) |
| Bootstrap máximo | 30,000 caracteres |
| Historial contexto | TTL 30 min (cache) |
| Soft trim | 4,000 caracteres |
