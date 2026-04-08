# Referencia de Agentes

## Mapa de Interacciones

```mermaid
graph TD
    MAIN[🏗️ main\nDev Lead IA]

    MAIN -->|orquesta| DEVGIT[💻 dev-odoo-github]
    MAIN -->|orquesta| DEVLOC[🔧 dev-odoo-local]
    MAIN -->|orquesta| TICKET[🎫 incidencias-odoo]
    MAIN -->|orquesta| CREATOR[📋 dev-project-creator]
    MAIN -->|orquesta| ARCH[🏛️ dev-project-architect]

    DEVLOC -->|exporta /mnt/cambios-odoo-local| DISTRIB[📦 dev-distrib-local]
    DEVGIT -->|notifica post-push| VALID[🔍 dev-validator-deploydev]
    DISTRIB -->|sessions_send| VALID

    VALID -->|si DEV OK| DEVOPS[🚀 devops-odoo]

    TICKET -->|stage 703\nRequiere código| CREATOR
    CREATOR -->|proyecto creado| ARCH
    ARCH -->|tag=odoo → solicita dev| MAIN

    style MAIN fill:#2563eb,color:#fff
    style DEVGIT fill:#7c3aed,color:#fff
    style DEVLOC fill:#7c3aed,color:#fff
    style DISTRIB fill:#0891b2,color:#fff
    style VALID fill:#0891b2,color:#fff
    style DEVOPS fill:#059669,color:#fff
    style TICKET fill:#dc2626,color:#fff
    style CREATOR fill:#d97706,color:#fff
    style ARCH fill:#d97706,color:#fff
```

---

## 🏗️ main — Dev Lead IA

**Propósito:** Orquestador principal. Coordina a todos los sub-agentes y gestiona el flujo general del equipo de desarrollo.

**Heartbeat:** cada 30 min con `ollama/qwen2.5-7b-gpu` (ligero)

```mermaid
flowchart TD
    HB[Heartbeat 30 min] --> CHECK{¿Tareas pendientes?}
    CHECK -->|timeout vencido| RETRY[Re-asignar tarea]
    CHECK -->|fallida sin reintento| ALERT[Escalar al usuario]
    CHECK -->|OK| IDLE[Esperar siguiente ciclo]

    USER[Solicitud usuario] --> ANALYZE[Analizar solicitud]
    ANALYZE --> DELEGATE{¿A qué agente?}
    DELEGATE -->|desarrollo Odoo + GitHub| DEVGIT[dev-odoo-github]
    DELEGATE -->|desarrollo local| DEVLOC[dev-odoo-local]
    DELEGATE -->|tickets soporte| TICKET[incidencias-odoo]
    DELEGATE -->|nuevo proyecto| CREATOR[dev-project-creator]
```

**Herramientas disponibles:** `group:fs`, `group:runtime`, `group:sessions`, `group:web`, `exec`

---

## 💻 dev-odoo-github

**Propósito:** Implementar cambios de código Odoo 16 en el servidor DEV y hacer push a `DEVMain_Latest`. Jenkins despliega automáticamente.

**Entorno de trabajo:**

| Parámetro | Valor |
|-----------|-------|
| Servidor | 189.195.191.16 (SSH) |
| Llave SSH | `/.keys/odoo-dev.pem` |
| Repo local | `/home/maikel/github/Odoo16UISEP_DEVMain` |
| Addons path | `addons-extra/addons_uisep` |
| Rama de trabajo | `DEVMain_Latest` |
| DB DEV | `final` |
| URL DEV | `https://dev.odoo.universidadisep.com` |
| Contenedor | `odoo_latest-w8co804sck0ssc0swkcgw488` |

```mermaid
flowchart TD
    START[Recibe tarea de desarrollo]
    START --> SSH["SSH a 189.195.191.16\nssh -i /.keys/odoo-dev.pem root@189.195.191.16"]
    SSH --> SYNC["Sincronizar rama\ngit stash → fetch → pull → stash pop"]
    SYNC --> EDIT[Editar archivos en\n/home/maikel/github/Odoo16UISEP_DEVMain]
    EDIT --> DIFF[Revisar git diff --stat]
    DIFF --> COMMIT["git commit + push\na DEVMain_Latest"]
    COMMIT --> JENKINS{Jenkins\ndespliega}
    JENKINS --> WAIT["Esperar ~5 min"]
    WAIT --> LOGS["Revisar logs:\n/data/coolify/services/w8co804.../log/odoo-bin.log"]
    LOGS --> OK{¿Sin errores\nERROR/CRITICAL?}
    OK -->|Sí| DONE[✅ Notificar a dev-validator-deploydev]
    OK -->|No| FIX[Corregir y re-commit]
    FIX --> DIFF
```

**Reglas críticas:**
- ⛔ NUNCA tocar rama `main`
- ⛔ NUNCA reiniciar Odoo DEV manualmente
- ⛔ NUNCA forzar push (`--force`)
- ✅ SIEMPRE hacer `git pull` antes de editar
- ✅ `search_read` antes de cualquier `write` o `unlink` RPC

---

## 🔧 dev-odoo-local

**Propósito:** Desarrollar cambios en el contenedor Odoo local (`/data/odoo-migration`). NO hace push a GitHub — exporta cambios para que `dev-distrib-local` los procese.

**Entorno de trabajo:**

| Parámetro | Valor |
|-----------|-------|
| Contenedor | `odoo-app-prod` (LOCAL, sin SSH) |
| Addons en container | `/mnt/odoo-migration-addons/addons_uisep` |
| Addons en host | `/data/odoo-migration/odoo16/addons-extra` |
| Carpeta exportación | `/mnt/cambios-odoo-local/<modulo>/` |
| URL | `https://dev3.odoo.universidadisep.com` |
| DB | `UisepFinal` |

```mermaid
flowchart TD
    START[Recibe tarea de desarrollo]
    START --> EDIT[Editar archivos en\n/mnt/odoo-migration-addons/addons_uisep]
    EDIT --> TEST[Probar cambios en\ndev3.odoo.universidadisep.com]
    TEST --> CAMBIOS["Crear CAMBIOS.md\n(descripción detallada)"]
    CAMBIOS --> EXPORT["Copiar SOLO archivos modificados a\n/mnt/cambios-odoo-local/<modulo>/"]
    EXPORT --> NOTIFY[Notificar a dev-distrib-local\npara procesar]

    style EXPORT fill:#0891b2,color:#fff
```

**Reglas:**
- ⛔ NUNCA copiar módulos completos — solo archivos modificados
- ⛔ NUNCA tocar contenedores de producción
- ✅ SIEMPRE crear `CAMBIOS.md` con descripción detallada
- ✅ La carpeta de exportación es el único canal de salida

---

## 📦 dev-distrib-local

**Propósito:** Recoger cambios de `/mnt/cambios-odoo-local` y distribuirlos al repositorio DEV vía SSH.

```mermaid
flowchart TD
    START[Detecta archivos en\n/mnt/cambios-odoo-local/]
    START --> READ["Leer CAMBIOS.md\nde cada módulo"]
    READ --> IMPACT[Analizar impacto\nvs DEVMain_Latest]
    IMPACT --> PULL["SSH al .57:\ngit fetch + pull DEVMain_Latest"]
    PULL --> SCP["scp archivos al repo DEV\n(uno a uno)"]
    SCP --> DIFF["Verificar git diff --stat\nantes de commit"]
    DIFF --> REVIEW{¿Cambios\nesperados?}
    REVIEW -->|Sí| COMMIT["git commit -m 'feat(<mod>): ...'\ngit push DEVMain_Latest"]
    REVIEW -->|Conflictos| ESCALATE[Escalar al usuario\n⛔ NO resolver automáticamente]
    COMMIT --> MOVE["Mover módulo procesado\na _procesados/YYYY-MM-DD_HHMM/"]
    MOVE --> NOTIFY["sessions_send →\ndev-validator-deploydev"]

    style ESCALATE fill:#dc2626,color:#fff
    style NOTIFY fill:#059669,color:#fff
```

**Reglas:**
- ✅ Procesar un módulo a la vez
- ✅ SIEMPRE `git pull` antes de copiar
- ✅ SIEMPRE revisar `git diff` antes del commit
- ⛔ NUNCA forzar push
- ⛔ NUNCA resolver conflictos automáticamente

---

## 🔍 dev-validator-deploydev

**Propósito:** Validar que cada commit a `DEVMain_Latest` se desplegó correctamente en el entorno DEV.

**Invocado por:** `dev-distrib-local` o `dev-odoo-github` vía `sessions_send`

```mermaid
flowchart TD
    TRIGGER[Recibe notificación\nde push a DEVMain_Latest]
    TRIGGER --> WAIT["⏳ Esperar 5 minutos\n(Jenkins tarda ~5 min)"]
    WAIT --> CONTAINER["Verificar contenedor:\ndocker ps | grep odoo_latest-w8co804"]
    CONTAINER --> RUNNING{¿Running?}
    RUNNING -->|No| RESTART_ALERT["⚠️ Alertar — NO reiniciar\nEscalar a usuario"]
    RUNNING -->|Sí| LOGS["Revisar logs:\ntail -100 odoo-bin.log"]
    LOGS --> ERRORS{¿ERROR o\nCRITICAL?}
    ERRORS -->|Sí| REPORT_FAIL["❌ Reportar fallo\ncon extracto del error"]
    ERRORS -->|No| HTTP["Health check HTTP\ncurl dev.odoo.universidadisep.com"]
    HTTP --> STATUS{¿HTTP 200?}
    STATUS -->|No| REPORT_FAIL
    STATUS -->|Sí| RPC{¿Requiere\nupgrade de módulo?}
    RPC -->|Sí| UPGRADE["Upgrade via XML-RPC:\n/web/dataset/call_kw"]
    RPC -->|No| CHECK_STATE
    UPGRADE --> POST_LOGS[Revisar logs post-upgrade]
    POST_LOGS --> CHECK_STATE["Verificar state=installed\nen ir.module.module"]
    CHECK_STATE --> SAVE["Guardar resumen\nen memory/YYYY-MM-DD.md"]
    SAVE --> NOTIFY_DEVOPS["✅ Notificar a devops-odoo\npara revisar PR"]
    REPORT_FAIL --> SAVE2["Guardar error\nen memory/YYYY-MM-DD.md"]

    style WAIT fill:#d97706,color:#fff
    style REPORT_FAIL fill:#dc2626,color:#fff
    style NOTIFY_DEVOPS fill:#059669,color:#fff
```

**Entorno DEV:**

| Parámetro | Valor |
|-----------|-------|
| Servidor | 189.195.191.16 (SSH) |
| Contenedor Odoo | `odoo_latest-w8co804sck0ssc0swkcgw488` |
| Logs | `/data/coolify/services/w8co804.../log/odoo-bin.log` |
| URL | `https://dev.odoo.universidadisep.com` |
| RPC DB | `final` |

---

## 🚀 devops-odoo

**Propósito:** Revisar Pull Requests de `DEVMain_Latest → main`, validar el deploy en Producción y gestionar emergencias en la rama de desarrollo.

**Heartbeat:** 60 min (FASE 1 automática)

**Skills disponibles:**

| Skill | Invocación | Automática |
|-------|-----------|-----------|
| `revertir-devmain` | Solo por humano | ⛔ Nunca |

```mermaid
flowchart TD
    subgraph FASE1["FASE 1 — Revisión de PR"]
        HB1[Heartbeat 60 min]
        HB1 --> CHECK_COMMITS["Verificar commits en\nDEVMain_Latest vs main\nGitHub API"]
        CHECK_COMMITS --> AHEAD{¿Commits\nadelante?}
        AHEAD -->|No| IDLE1[Sin cambios pendientes]
        AHEAD -->|Sí| PR_EXISTS{¿PR abierto\nexiste?}
        PR_EXISTS -->|No| CREATE_PR["Crear PR automáticamente:\nDEVMain_Latest → main"]
        PR_EXISTS -->|Sí| REVIEW_PR
        CREATE_PR --> REVIEW_PR["Revisar diff del PR"]
        REVIEW_PR --> CRITERIA{Criterios\nde calidad}
        CRITERIA -->|Pasa| APPROVE["✅ Aprobar PR\n+ comentario"]
        CRITERIA -->|Falla| CLOSE["❌ Cerrar PR\n+ comentario explicativo"]
    end

    subgraph FASE2["FASE 2 — Post-deploy Producción"]
        MERGE[Usuario hace merge en GitHub]
        MERGE --> VERIFY_MERGE["Verificar merge via API\ngit log main"]
        VERIFY_MERGE --> WAIT2["⏳ Esperar 7 minutos\n(Jenkins prod ~5-7 min)"]
        WAIT2 --> PROD_CONTAINER["docker logs --tail 100 odoo-app-prod\n(LOCAL, sin SSH)"]
        PROD_CONTAINER --> PROD_ERRORS{¿Errores?}
        PROD_ERRORS -->|Sí| PROD_FAIL["❌ Reportar fallo\nen producción"]
        PROD_ERRORS -->|No| PROD_HTTP["Health check\nhttps://app.universidadisep.com"]
        PROD_HTTP --> PROD_RPC{¿Upgrade\nnecesario?}
        PROD_RPC -->|Sí| PROD_UPGRADE["Upgrade via RPC en Prod\n(UisepFinal)"]
        PROD_RPC -->|No| PROD_SAVE
        PROD_UPGRADE --> PROD_SAVE["Guardar en memory/YYYY-MM-DD.md"]
        PROD_SAVE --> DONE2["✅ Deploy exitoso en Producción"]
    end

    APPROVE -.->|usuario hace merge| MERGE

    style FASE1 fill:#eff6ff
    style FASE2 fill:#f0fdf4
    style PROD_FAIL fill:#dc2626,color:#fff
    style DONE2 fill:#059669,color:#fff
```

**Criterios de revisión de PR:**

| Criterio | ✅ Aprobado | ❌ Rechazado |
|----------|------------|-------------|
| Alcance | Solo cambios en `addons_uisep` | Modifica core de Odoo |
| Seguridad | Sin credenciales hardcodeadas | Tokens/passwords en código |
| Python | Convenciones Odoo, sin SQL raw sin sanitizar | SQL injection, código inseguro |
| XML | XMLs bien formados | XML inválido |
| Versionado | `__manifest__.py` con `16.0.x.y.z` | Versión incorrecta |
| Operaciones | Sin operaciones destructivas sin control | `unlink` masivo sin guard |

**Ambientes:**

| Ambiente | Acceso | Contenedor |
|----------|--------|-----------|
| DEV | SSH a 189.195.191.16 | `odoo_latest-w8co804sck0ssc0swkcgw488` |
| Producción | LOCAL (sin SSH) | `odoo-app-prod` |

### Skill: revertir-devmain

Revierte `DEVMain_Latest` al último commit de `main`. Se usa cuando hay commits incorrectos o no autorizados en la rama de desarrollo.

```mermaid
flowchart TD
    HUMAN["👤 Humano solicita:\n'revertir DEVMain_Latest'"]
    HUMAN --> CONFIRM["devops-odoo pide confirmación\n⛔ ESPERA respuesta"]
    CONFIRM --> YES{"¿Usuario\nconfirma?"}
    YES -->|No / silencio| ABORT["🚫 Abortar\nNo hacer nada"]
    YES -->|"sí, revertir"| LIST["Listar commits que se eliminarán\nvía GitHub API compare"]
    LIST --> FETCH["SSH .57:\ngit fetch origin"]
    FETCH --> RESET["git reset --hard origin/main"]
    RESET --> PUSH["git push --force origin DEVMain_Latest"]
    PUSH --> VERIFY["Verificar via API:\nahead_by == 0"]
    VERIFY --> LOG["Registrar en memory/YYYY-MM-DD.md"]
    LOG --> NOTIFY["✅ Notificar a main\ncon lista de commits eliminados"]

    style ABORT fill:#dc2626,color:#fff
    style CONFIRM fill:#d97706,color:#fff
    style NOTIFY fill:#059669,color:#fff
```

**Cómo invocarla** — el humano debe decir explícitamente alguna de estas frases:
- `"revertir DEVMain_Latest"`
- `"resetear la rama de dev a main"`
- `"limpiar DEVMain_Latest"`
- `"ejecutar skill revertir-devmain"`

**Garantías:**
- Pide confirmación antes de ejecutar
- Lista los commits que se eliminarán antes del force push
- Registra la operación en memoria con los commits afectados
- ⛔ Nunca se ejecuta por heartbeat, cron ni invocación de otro agente

---

## 🎫 incidencias-odoo

**Propósito:** Atender tickets del proyecto Incidencias TI (proyecto ID=53) en Odoo.

**Heartbeat:** 30 min vía cron job `incidencias-autonomas`

```mermaid
flowchart TD
    CRON["⏰ Cron: cada 30 min"]
    CRON --> READ_TICKETS["Consultar réplica PostgreSQL\nproyecto_id=53, stage_id=564 (Pendiente)"]
    READ_TICKETS --> ANY{¿Hay tickets?}
    ANY -->|No| IDLE[Sin tickets pendientes]
    ANY -->|Sí| CLASSIFY{Clasificar ticket}

    CLASSIFY -->|"menciona 'duplicado'\n'dos perfiles'"| FUSION["Cargar skill:\nfusion-contactos-duplicados"]
    CLASSIFY -->|"menciona 'credencial'\n'programa incorrecto'"| CRED["Cargar skill:\ncorreccion-credencial-estudiante"]
    CLASSIFY -->|Otro tipo| LEAVE["Dejar en Pendiente\n(skill no disponible aún)"]

    FUSION --> STAGE_PROC["Cambiar stage → En Proceso (644)\nvía XML-RPC"]
    CRED --> STAGE_PROC

    STAGE_PROC --> RESOLVE{¿Resoluble\nvia RPC?}
    RESOLVE -->|Sí| RPC_ACTION["Ejecutar acción:\nwrite/update en modelos Odoo"]
    RESOLVE -->|No, requiere código| ESCALATE["Cambiar stage →\nEnviado a Proyecto (703)"]

    RPC_ACTION --> STAGE_DONE["Cambiar stage → Listo (565)"]
    ESCALATE --> CHATTER2["Registrar nota\nen chatter"]
    STAGE_DONE --> CHATTER["Registrar nota\nen chatter"]
    CHATTER --> EMAIL["📧 Enviar email al solicitante\nvía AWS SES"]
    CHATTER2 --> EMAIL2["📧 Notificar escalación\nvía AWS SES"]
    EMAIL --> NEXT[Siguiente ticket]
    EMAIL2 --> NEXT

    style STAGE_DONE fill:#059669,color:#fff
    style ESCALATE fill:#d97706,color:#fff
    style LEAVE fill:#6b7280,color:#fff
```

**Stages del proyecto 53:**

| Stage | ID | Descripción |
|-------|----|-------------|
| Pendiente | 564 | Tickets sin procesar |
| En Proceso | 644 | Siendo atendido |
| Listo | 565 | Resuelto via RPC |
| En Revisión | 567 | Requiere clarificación |
| Enviado a Proyecto | 703 | Requiere desarrollo |
| Anulado | 643 | Cancelado |

**Skills disponibles:**

| Skill | Activación | Acción |
|-------|-----------|--------|
| `fusion-contactos-duplicados` | "duplicado", "dos perfiles", "dos cuentas" | Fusiona perfiles en Odoo |
| `correccion-credencial-estudiante` | "credencial", "programa incorrecto", "carnet" | Corrige datos del estudiante |
| `notificacion-incidencia` | Siempre al cambiar stage | Envía email por AWS SES |

**Accesos:**

| Recurso | Tipo | Endpoint |
|---------|------|----------|
| Lectura tickets | PostgreSQL read-only | Réplica en servidor .57 |
| Escritura Odoo | XML-RPC | `https://app.universidadisep.com` |

---

## 📋 dev-project-creator

**Propósito:** Convertir tickets de alta complejidad y solicitudes del área de innovación en proyectos formales de desarrollo.

**Heartbeat:** 60 min

```mermaid
flowchart TD
    HB["⏰ Heartbeat 60 min"]
    HB --> READ1["Leer proyecto 53\nstage=703, user_id=2 (Administrator)"]
    HB --> READ2["Leer proyecto 36\n(Pote/Innovación — todas activas)"]

    READ1 --> PROCESS["Por cada tarea encontrada"]
    READ2 --> PROCESS

    PROCESS --> CHECK_DUP{"¿Ya existe proyecto\ncon este nombre?"}
    CHECK_DUP -->|Sí| SKIP["Saltar (evitar duplicados)"]
    CHECK_DUP -->|No| CREATE_PROJ["Crear proyecto en Odoo\n(módulo Proyectos)"]

    CREATE_PROJ --> STAGES["Crear 6 stages estándar:\n1-Análisis\n2-Diseño\n3-Desarrollo\n4-Pruebas/QA\n5-Producción\n6-Cerrado"]
    STAGES --> CREATE_TASK["Crear tarea inicial:\n'Análisis de requerimientos y alcance'\nen stage Análisis"]
    CREATE_TASK --> COPY_DESC["Copiar descripción EXACTA\nde la tarea fuente"]
    COPY_DESC --> CLEAN_SOURCE{¿De qué fuente?}
    CLEAN_SOURCE -->|Proyecto 53| REASSIGN["Reasignar ticket\na Maikel Guzman (id=5064)"]
    CLEAN_SOURCE -->|Proyecto 36| ARCHIVE["Archivar tarea fuente\n'✅ creado como proyecto'"]
    REASSIGN --> CHATTER["Registrar en chatter\nde tarea fuente"]
    ARCHIVE --> CHATTER
    CHATTER --> PASS["Pasar testigo a\ndev-project-architect"]

    style CREATE_PROJ fill:#2563eb,color:#fff
    style SKIP fill:#6b7280,color:#fff
    style PASS fill:#059669,color:#fff
```

**Reglas clave:**
- ✅ `search_count` ANTES de crear (evitar duplicados)
- ✅ Primera tarea SIEMPRE "Análisis de requerimientos y alcance"
- ✅ Descripción IDÉNTICA a la fuente sin modificaciones
- ⛔ Si falla la creación, NO modificar la tarea fuente

---

## 🏛️ dev-project-architect

**Propósito:** Analizar nuevos proyectos y asignar la herramienta tecnológica óptima del stack UISEP.

**Heartbeat:** 60 min

```mermaid
flowchart TD
    HB["⏰ Heartbeat 60 min"]
    HB --> SEARCH["Buscar proyectos activos:\ntag_id=1 (Tecnología)\nSIN etiquetas 24-29"]

    SEARCH --> ANY{¿Proyectos\nsin analizar?}
    ANY -->|No| IDLE[Sin proyectos nuevos]
    ANY -->|Sí| READ_DESC["Leer descripción completa\ndel proyecto + tarea análisis"]
    READ_DESC --> NOTIFY_START["Registrar inicio\nen chatter del proyecto"]
    NOTIFY_START --> ANALYZE["Analizar requerimientos\nvs criterios de herramientas"]

    ANALYZE --> DECISION{Herramienta\nóptima}

    DECISION -->|"Automatización\nIntegración\nWebhooks"| N8N["🔄 n8n (tag: 24)"]
    DECISION -->|"Conversaciones\nAtención cliente"| CHATWOOT["💬 chatwoot (tag: 26)"]
    DECISION -->|"Email marketing\nLeads"| MAUTIC["📧 mautic (tag: 27)"]
    DECISION -->|"Sitio web\nLanding page"| WP["🌐 wordpress (tag: 28)"]
    DECISION -->|"API externa\nMicroservicio"| API["⚙️ desarrollos-apis (tag: 29)"]
    DECISION -->|"Lógica inseparable\nde modelo Odoo ÚNICA opción"| ODOO_TAG["📦 odoo (tag: 25)"]

    N8N --> ASSIGN["Asignar tag al proyecto\nvía XML-RPC write"]
    CHATWOOT --> ASSIGN
    MAUTIC --> ASSIGN
    WP --> ASSIGN
    API --> ASSIGN
    ODOO_TAG --> ASSIGN

    ASSIGN --> DOCUMENT["Documentar decisión en chatter\ncon justificación técnica"]
    DOCUMENT --> MEMORY["Guardar en\nmemory/analisis.md"]
    MEMORY --> EMAIL["📧 Enviar notificación\nvía AWS SES"]

    style ODOO_TAG fill:#dc2626,color:#fff
    style ASSIGN fill:#059669,color:#fff
```

**Problemas de Odoo 16 que considera (para evitar asignarlo):**

| Problema | Descripción |
|----------|-------------|
| OOM Kill | Kernel mata proceso cuando memoria se agota |
| Workers idle bloqueados | Consumen memoria sin liberar |
| Procesos en fallo recursivos | Bucle de error degrada servicio |
| Sobrecarga módulos | slide/mail/livechat consumen RAM desproporcionadamente |
| Arquitectura monolítica | No escala horizontalmente por módulo |

**Herramientas disponibles:**

| Tag ID | Herramienta | Usar cuando |
|--------|-------------|-------------|
| 24 | n8n | Automatizaciones, flujos, integraciones, webhooks |
| 25 | odoo | Lógica inseparable del modelo Odoo (ÚLTIMA opción) |
| 26 | chatwoot | Gestión de conversaciones, atención al cliente |
| 27 | mautic | Email marketing, campañas, leads, nutrición |
| 28 | wordpress | Sitios web, landing pages, portales públicos |
| 29 | desarrollos-apis | APIs, microservicios, integraciones externas |
