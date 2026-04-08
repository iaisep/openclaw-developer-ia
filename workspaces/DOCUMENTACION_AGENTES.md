# Documentación de Agentes — OpenClaw Developer IA

> **Fecha:** 7 de abril de 2026
> **Ubicación:** `/data/openclaw-developer-ia/workspaces`

---

## Agentes configurados

### 🎫 `incidencias-odoo`
**Propósito:** Atiende tickets del proyecto de Incidencias TI (proyecto id=53) en Odoo producción.

**Flujo:**
1. Lee tareas en stage **Pendiente** (id=564) desde la réplica PostgreSQL en servidor `.57` (read-only)
2. Intenta resolver el problema de forma autónoma
3. Mueve la tarea por los stages: Pendiente → En Proceso → Listo
4. Si requiere desarrollo de código, escala al stage **Enviado a Proyecto** (id=703) y deja el testigo a `dev-project-creator`
5. Registra todo via XML-RPC en el chatter de producción

**Stages del proyecto 53:**

| Stage | ID |
|---|---|
| Pendiente | 564 |
| En Proceso | 644 |
| Listo | 565 |
| En Revisión | 567 |
| Enviado a Proyecto | 703 |
| Anulado | 643 |

---

### 🏗️ `dev-project-creator`
**Propósito:** Convierte solicitudes en proyectos de desarrollo de software en Odoo.

**Lee de dos fuentes:**
- **Incidencias TI** (proyecto 53, stage "Enviado a Proyecto" id=703) — solo tareas asignadas a Administrator (user id=2)
- **Pote / Innovación** (proyecto 36) — todas las tareas activas

**Por cada tarea:**
1. Crea un nuevo proyecto en el módulo Proyectos con estructura estándar de desarrollo de software
2. Crea la tarea inicial **"Análisis de requerimientos y alcance"** con la descripción original
3. Limpia la tarea fuente (reasigna o archiva según su origen)
4. Pasa el testigo a `dev-project-architect`

---

### 🏛️ `dev-project-architect`
**Propósito:** Analiza proyectos recién creados y asigna la herramienta tecnológica más adecuada.

**Por cada proyecto recibido:**
1. Lee la descripción del proyecto desde Odoo
2. Notifica inicio del análisis en el chatter
3. Evalúa el stack disponible considerando las limitaciones reales (especialmente los problemas de OOM y memoria de Odoo en producción)
4. Asigna una etiqueta de herramienta al proyecto
5. Notifica la decisión con justificación técnica en el chatter

**Herramientas disponibles:**

| Etiqueta | tag_id | Cuándo usarla |
|---|---|---|
| `n8n` | 24 | Automatizaciones, flujos, integraciones entre sistemas, webhooks, triggers periódicos |
| `odoo` | 25 | Lógica **inseparable** del modelo de datos de Odoo (solo si impacto en memoria es bajo) |
| `chatwoot` | 26 | Atención al cliente, bandejas compartidas, bots de conversación |
| `mautic` | 27 | Campañas de email marketing, embudos de nutrición de leads, scoring |
| `wordpress` | 28 | Sitios web, landing pages, portales públicos, formularios de captación |
| `desarrollos-apis` | 29 | Microservicios, APIs REST/GraphQL, integraciones externas, comodín |

> ⚠️ **Criterio clave:** Toda funcionalidad que pueda vivir fuera de Odoo, debe vivir fuera. Odoo 16 en producción presenta problemas estructurales de OOM Kill, procesos idle bloqueados y arquitectura monolítica que no permite escalar horizontalmente.

---

### 💻 `dev-odoo-github`
**Propósito:** Implementa código Odoo 16 en el entorno DEV y lo sube a GitHub para que Jenkins despliegue automáticamente.

**Flujo:**
1. Recibe tarea de código
2. Implementa en el servidor DEV (189.195.191.16) via SSH
3. Hace commit y push a rama `DEVMain_Latest`
4. Jenkins despliega automáticamente en DEV
5. Verifica ausencia de errores en logs

**Infraestructura DEV:**

| Recurso | Valor |
|---|---|
| Servidor | `189.195.191.16` |
| Llave SSH | `/.keys/odoo-dev.pem` |
| Repo en DEV | `/home/maikel/github/Odoo16UISEP_DEVMain/addons-extra/addons_uisep` |
| Contenedor Odoo | `odoo_latest-w8co804sck0ssc0swkcgw488` |
| Contenedor Postgres | `pgodoo_latest-w8co804sck0ssc0swkcgw488` |
| DB | `final` |
| URL DEV | https://dev.odoo.universidadisep.com |

---

### 🔧 `dev-odoo-local`
**Propósito:** Desarrolla sobre el contenedor local de migración (`/data/odoo-migration`). **No sube a GitHub.**

**Flujo:**
1. Modifica addons en `/mnt/odoo-migration-addons/` (montado desde `/data/odoo-migration/odoo16/addons-extra`)
2. Prueba en el entorno local (https://dev3.odoo.universidadisep.com)
3. Exporta los archivos modificados a `/mnt/cambios-odoo-local/<modulo>/` con documentación clara

**Infraestructura local:**

| Recurso | Valor |
|---|---|
| Contenedor | `odoo-app-prod` (local, sin SSH) |
| DB | `UisepFinal` |
| Addons | `/mnt/odoo-migration-addons/` |
| Exportación | `/mnt/cambios-odoo-local/` → `/home/maikel/cambios_odoo_local` en host |
| URL | https://dev3.odoo.universidadisep.com |

---

### 🚀 `devops-odoo`
**Propósito:** Guardián de la calidad del pipeline de producción. Opera en dos fases.

**FASE 1 — Evaluación del Pull Request** (`DEVMain_Latest` → `main`):
- Analiza el diff del PR en GitHub (`Universidad-ISEP/Odoo16UISEP`)
- Verifica calidad del código Odoo (sin drops de columna, sin migraciones rotas, imports correctos, etc.)
- Aprueba o rechaza via GitHub API Review con justificación clara

**FASE 2 — Validación post-deploy en Producción:**
- Después del merge, Jenkins despliega en producción
- Verifica health check, logs de Odoo y que los módulos actualicen correctamente
- Actualiza módulos via XML-RPC si es necesario
- Reporta el resultado final en el PR o en el chatter de Odoo

**Infraestructura:**

| Recurso | Ubicación | Acceso |
|---|---|---|
| Jenkins | Servidor .57 — 189.195.191.16 | SSH con `/.keys/odoo-dev.pem` |
| Odoo Producción | Servidor .58 — local | `docker` directo, **sin SSH** |
| GitHub repo | `Universidad-ISEP/Odoo16UISEP` | Token via API |

> ⚠️ **Regla crítica:** NUNCA usar SSH para acceder a Odoo Producción. El contenedor `odoo-app-prod` es local en `.58` — ejecutar `docker` directamente.

---

### ⚠️ `dev-distrib-local` y `dev-validator-deploydev`
Estos dos workspaces tienen el archivo `IDENTITY.md` vacío (plantilla sin completar). **No tienen rol asignado aún** — están pendientes de configuración.

---

## Diagrama del pipeline completo

```
[Incidencia recibida en Odoo — proyecto 53]
                    │
                    ▼
           incidencias-odoo
          ¿Resoluble sin código?
           │                  │
          Sí                  No
           │                  │
           ▼                  ▼
        [Listo]     Escala → stage "Enviado a Proyecto" (703)
                              │
                              ▼
                   dev-project-creator
                 (crea proyecto en Odoo)
                              │
                              ▼
                  dev-project-architect
                   (asigna herramienta)
                              │
                    ┌─────────┴──────────┐
                    │                    │
              herramienta=odoo     otra herramienta
                    │              (n8n, chatwoot, etc.)
                    ▼
           dev-odoo-github
        (desarrollo en DEV + push a DEVMain_Latest)
                    │
                    ▼
              devops-odoo
          (revisa PR → aprueba/rechaza)
                    │
                    ▼
             [merge a main]
                    │
                    ▼
          Jenkins despliega en Producción
                    │
                    ▼
              devops-odoo
          (valida post-deploy)
                    │
                    ▼
               [Producción ✅]
```

---

## Conexión común — XML-RPC Odoo Producción

Todos los agentes que escriben en producción usan estas credenciales:

```python
import xmlrpc.client, ssl

ODOO_URL  = "https://app.universidadisep.com"
ODOO_DB   = "UisepFinal"
ODOO_USER = "iallamadas@universidadisep.com"
ODOO_PASS = "${ODOO_RPC_PASSWORD}"

ctx = ssl.create_default_context()
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common", context=ctx)
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})  # uid=5064
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object", context=ctx)
```
