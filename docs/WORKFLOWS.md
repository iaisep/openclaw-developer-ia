# Workflows — Diagramas de Flujo

## 1. Pipeline Completo: Incidencia → Producción

```mermaid
flowchart TD
    classDef support fill:#fef3c7,stroke:#d97706
    classDef dev fill:#eff6ff,stroke:#2563eb
    classDef infra fill:#f0fdf4,stroke:#059669
    classDef decision fill:#f5f3ff,stroke:#7c3aed

    INC_NEW["📋 Nueva incidencia en Odoo\nproyecto 53 — stage: Pendiente"]:::support

    subgraph SOPORTE["🎫 Pipeline de Soporte (incidencias-odoo)"]
        S1["Leer tickets\nstage_id=564"]:::support
        S2{"¿Resoluble\nvia RPC?"}:::decision
        S3["✅ Ejecutar RPC\nCambiar stage → Listo"]:::support
        S4["Cambiar stage →\nEnviado a Proyecto (703)"]:::support
        S5["Notificar solicitante\nvía email"]:::support
    end

    subgraph PROYECTOS["📋 Creación de Proyecto (dev-project-creator)"]
        P1["Leer proyecto 53\nstage=703, user=2"]
        P2["Crear proyecto en Odoo\n6 stages estándar"]
        P3["Crear tarea:\n'Análisis de requerimientos'"]
        P4["Reasignar ticket fuente\na Maikel"]
    end

    subgraph ARQUITECTURA["🏛️ Análisis Tecnológico (dev-project-architect)"]
        A1["Buscar proyectos\nsin etiqueta (24-29)"]
        A2["Analizar descripción\ny requerimientos"]
        A3{"Herramienta\nóptima"}
        A4_N8N["🔄 n8n"]
        A4_ODOO["📦 odoo"]
        A4_OTHER["otras herramientas"]
        A5["Asignar etiqueta\nDocumentar decisión"]
    end

    subgraph DESARROLLO["💻 Pipeline de Desarrollo"]
        D1["Dev Lead asigna\nal agente correspondiente"]
        D2["💻 dev-odoo-github\nEdita código en DEV"]
        D3["git commit + push\na DEVMain_Latest"]
        D4["⚙️ Jenkins detecta push\nDespliega en DEV"]
    end

    subgraph VALIDACION["🔍 Validación DEV (dev-validator-deploydev)"]
        V1["⏳ Esperar 5 minutos"]
        V2["Verificar contenedor\ny logs DEV"]
        V3{"¿Deploy\nexitoso?"}
        V4["✅ Notificar a devops"]
        V5["❌ Reportar fallo"]
    end

    subgraph DEVOPS["🚀 Review y Producción (devops-odoo)"]
        DO1["Crear PR:\nDEVMain_Latest → main"]
        DO2["Revisar diff\naplicar criterios"]
        DO3{"¿Aprobado?"}
        DO4["✅ Aprobar PR"]
        DO5["❌ Cerrar PR con motivo"]
        DO6["👤 Usuario hace merge"]
        DO7["⚙️ Jenkins despliega\nen Producción"]
        DO8["⏳ Esperar 7 minutos"]
        DO9["Verificar logs\ny upgrade RPC"]
        DO10["✅ Producción OK"]
    end

    INC_NEW --> S1
    S1 --> S2
    S2 -->|Sí| S3
    S2 -->|No| S4
    S3 --> S5
    S4 --> P1

    P1 --> P2
    P2 --> P3
    P3 --> P4
    P4 --> A1

    A1 --> A2
    A2 --> A3
    A3 --> A4_N8N
    A3 --> A4_ODOO
    A3 --> A4_OTHER
    A4_N8N --> A5
    A4_ODOO --> A5
    A4_OTHER --> A5
    A4_ODOO --> D1

    D1 --> D2
    D2 --> D3
    D3 --> D4
    D4 --> V1

    V1 --> V2
    V2 --> V3
    V3 -->|Sí| V4
    V3 -->|No| V5
    V4 --> DO1

    DO1 --> DO2
    DO2 --> DO3
    DO3 -->|Sí| DO4
    DO3 -->|No| DO5
    DO4 --> DO6
    DO6 --> DO7
    DO7 --> DO8
    DO8 --> DO9
    DO9 --> DO10
```

---

## 2. Flujo de Desarrollo: Local → DEV → Producción

```mermaid
sequenceDiagram
    actor User as 👤 Usuario
    participant Main as 🏗️ main
    participant DevGit as 💻 dev-odoo-github
    participant DevLoc as 🔧 dev-odoo-local
    participant Distrib as 📦 dev-distrib-local
    participant Valid as 🔍 dev-validator
    participant DevOps as 🚀 devops-odoo
    participant GH as GitHub
    participant Jenkins as ⚙️ Jenkins
    participant Prod as 🏭 Producción

    User->>Main: "Implementar módulo X"
    
    alt Flujo directo (GitHub)
        Main->>DevGit: Asignar tarea
        DevGit->>DevGit: SSH a .57, git pull
        DevGit->>DevGit: Editar código
        DevGit->>GH: git push DEVMain_Latest
        GH->>Jenkins: Webhook detecta push
        Jenkins->>Jenkins: Deploy en DEV (~5 min)
        DevGit->>Valid: sessions_send: "validar deploy"
    else Flujo local (sin GitHub directo)
        Main->>DevLoc: Asignar tarea
        DevLoc->>DevLoc: Editar en /mnt/odoo-migration-addons
        DevLoc->>DevLoc: Probar en dev3.odoo.universidadisep.com
        DevLoc->>DevLoc: Crear CAMBIOS.md
        DevLoc->>Distrib: Exportar a /mnt/cambios-odoo-local
        Distrib->>GH: SSH + SCP + git push DEVMain_Latest
        GH->>Jenkins: Webhook detecta push
        Jenkins->>Jenkins: Deploy en DEV (~5 min)
        Distrib->>Valid: sessions_send: "validar deploy"
    end

    Valid->>Valid: Esperar 5 min
    Valid->>Jenkins: SSH: verificar logs DEV
    
    alt Deploy exitoso
        Valid->>DevOps: Notificar OK
        DevOps->>GH: Crear PR (DEVMain_Latest → main)
        DevOps->>GH: Revisar diff + criterios
        DevOps->>GH: Aprobar PR
        User->>GH: Hacer merge (acción manual)
        GH->>Jenkins: Webhook: deploy producción
        Jenkins->>Prod: Deploy en Producción (~7 min)
        DevOps->>Prod: Verificar logs + upgrade RPC
        DevOps->>Main: ✅ Producción OK
        Main->>User: Confirmación de deploy
    else Deploy fallido
        Valid->>Main: ❌ Error en deploy
        Main->>User: Reportar error con extracto de logs
    end
```

---

## 3. Ciclo de Heartbeats

```mermaid
gantt
    title Ciclo de Heartbeats del Sistema
    dateFormat mm:ss
    axisFormat %M:%S

    section main (30 min)
    Verificar tareas pendientes :active, m1, 00:00, 2m

    section incidencias-odoo (30 min)
    Leer tickets Pendientes (564) : i1, 00:00, 5m
    Clasificar y procesar : i2, after i1, 10m
    Notificar resultados : i3, after i2, 2m

    section dev-project-creator (60 min)
    Leer proyecto 53 stage 703 : c1, 00:00, 3m
    Leer proyecto 36 Pote : c2, after c1, 2m
    Crear proyectos + stages : c3, after c2, 8m

    section dev-project-architect (60 min)
    Buscar proyectos sin tag : a1, 00:00, 3m
    Analizar y asignar herramienta : a2, after a1, 10m

    section devops-odoo (60 min)
    Verificar commits DEVMain_Latest : d1, 00:00, 2m
    Crear/revisar/aprobar PR : d2, after d1, 8m
```

---

## 4. Clasificación y Procesamiento de Tickets

```mermaid
flowchart TD
    TICKET[Ticket en Pendiente\nstage_id=564]

    TICKET --> READ["Leer descripción completa"]

    READ --> CLASS{Clasificación\npor keywords}

    CLASS -->|"duplicado\ndos perfiles\ndos cuentas\nregistro doble"| FUSION["Skill: fusion-contactos-duplicados"]
    CLASS -->|"credencial\nprograma incorrecto\ncarnet\ncontraseña\nacceso"| CRED["Skill: correccion-credencial-estudiante"]
    CLASS -->|Otro| OTHER["Dejar en Pendiente\n(sin skill disponible)"]

    FUSION --> PROC_FUSION["1. Buscar duplicados en CRM/res.partner\n2. Verificar que son el mismo contacto\n3. Ejecutar merge via RPC\n4. Verificar resultado"]
    CRED --> PROC_CRED["1. Buscar estudiante en Odoo\n2. Identificar campo incorrecto\n3. Corregir via write RPC\n4. Verificar datos actualizados"]

    PROC_FUSION --> STAGE_IN["Cambiar a En Proceso (644)"]
    PROC_CRED --> STAGE_IN

    STAGE_IN --> EXECUTE[Ejecutar acción RPC]
    EXECUTE --> SUCCESS{¿Éxito?}

    SUCCESS -->|Sí| STAGE_DONE["Cambiar a Listo (565)"]
    SUCCESS -->|No| STAGE_REVIEW["Cambiar a En Revisión (567)"]

    STAGE_DONE --> CHATTER["Registrar en chatter:\nqué se hizo + resultado"]
    STAGE_REVIEW --> CHATTER_ISSUE["Registrar en chatter:\nqué falló + próximos pasos"]

    CHATTER --> NOTIF["Skill: notificacion-incidencia\nEmail al solicitante @universidadisep.com"]
    CHATTER_ISSUE --> NOTIF

    style FUSION fill:#2563eb,color:#fff
    style CRED fill:#2563eb,color:#fff
    style OTHER fill:#6b7280,color:#fff
    style STAGE_DONE fill:#059669,color:#fff
    style STAGE_REVIEW fill:#d97706,color:#fff
```

---

## 5. Decisión de Herramienta Tecnológica

```mermaid
flowchart TD
    START["Nuevo proyecto sin etiqueta"]

    START --> Q1{"¿Es una automatización,\nflujo entre sistemas,\no webhook?"}
    Q1 -->|Sí| N8N["🔄 n8n\ntag: 24"]

    Q1 -->|No| Q2{"¿Es gestión de\nconversaciones o\natención al cliente?"}
    Q2 -->|Sí| CHAT["💬 chatwoot\ntag: 26"]

    Q2 -->|No| Q3{"¿Es email marketing,\ncampañas, leads\no nurturing?"}
    Q3 -->|Sí| MAUTIC["📧 mautic\ntag: 27"]

    Q3 -->|No| Q4{"¿Es sitio web,\nlanding page o\nportal público?"}
    Q4 -->|Sí| WP["🌐 wordpress\ntag: 28"]

    Q4 -->|No| Q5{"¿Es API externa,\nmicroservicio o\nintegración compleja?"}
    Q5 -->|Sí| API["⚙️ desarrollos-apis\ntag: 29"]

    Q5 -->|No| Q6{"¿La lógica es\nINSEPARABLE del\nmodelo de datos Odoo?\n¿No puede hacerse\nde otra forma?"}
    Q6 -->|Sí| ODOO_CHECK["⚠️ Considerar problemas:\n- OOM Kill\n- Workers bloqueados\n- Arquitectura monolítica"]
    Q6 -->|No| API

    ODOO_CHECK --> Q7{"¿Beneficio justifica\nlos riesgos de\nOdoo 16?"}
    Q7 -->|Sí| ODOO["📦 odoo\ntag: 25\n(ÚLTIMA opción)"]
    Q7 -->|No| API

    style N8N fill:#059669,color:#fff
    style CHAT fill:#2563eb,color:#fff
    style MAUTIC fill:#7c3aed,color:#fff
    style WP fill:#0891b2,color:#fff
    style API fill:#d97706,color:#fff
    style ODOO fill:#dc2626,color:#fff
    style ODOO_CHECK fill:#fef3c7,stroke:#d97706
```

---

## 6. Validación de Deploy DEV + Producción

```mermaid
flowchart TD
    subgraph DEV["Validación DEV"]
        D_PUSH["Push a DEVMain_Latest"]
        D_WAIT["⏳ Esperar 5 min\n(Jenkins DEV)"]
        D_CONTAINER["docker ps | grep odoo_latest-w8co804"]
        D_LOGS["tail -100 odoo-bin.log\nbuscar: ERROR|CRITICAL"]
        D_HTTP["curl https://dev.odoo.universidadisep.com\nesperado: HTTP 200"]
        D_STATE["XML-RPC: verificar\nir.module.module state=installed"]
        D_OK["✅ DEV OK\n→ Crear PR"]
        D_FAIL["❌ DEV Fallo\n→ Reportar al usuario"]
    end

    subgraph PROD["Validación Producción"]
        P_MERGE["Merge en GitHub"]
        P_WAIT["⏳ Esperar 7 min\n(Jenkins Producción)"]
        P_CONTAINER["docker logs --tail 100 odoo-app-prod\n(LOCAL — sin SSH)"]
        P_HTTP["curl https://app.universidadisep.com\nesperado: HTTP 200"]
        P_UPGRADE{¿Módulo\nnecesita upgrade?}
        P_RPC["XML-RPC upgrade:\ndb=UisepFinal, uid=5064"]
        P_POST_LOGS["Revisar logs post-upgrade"]
        P_OK["✅ Producción OK"]
        P_FAIL["❌ Producción Fallo\n→ Reportar urgente"]
    end

    D_PUSH --> D_WAIT --> D_CONTAINER --> D_LOGS
    D_LOGS -->|Sin errores| D_HTTP
    D_LOGS -->|Con errores| D_FAIL
    D_HTTP -->|200| D_STATE
    D_HTTP -->|No 200| D_FAIL
    D_STATE -->|installed| D_OK
    D_STATE -->|No instalado| D_FAIL

    P_MERGE --> P_WAIT --> P_CONTAINER --> P_HTTP
    P_HTTP -->|200| P_UPGRADE
    P_HTTP -->|No 200| P_FAIL
    P_UPGRADE -->|Sí| P_RPC --> P_POST_LOGS --> P_OK
    P_UPGRADE -->|No| P_OK

    style D_OK fill:#059669,color:#fff
    style D_FAIL fill:#dc2626,color:#fff
    style P_OK fill:#059669,color:#fff
    style P_FAIL fill:#dc2626,color:#fff
```

---

## 7. Comunicación entre Agentes

```mermaid
sequenceDiagram
    participant Cron as ⏰ Cron / Heartbeat
    participant Ticket as 🎫 incidencias-odoo
    participant Creator as 📋 dev-project-creator
    participant Arch as 🏛️ dev-project-architect
    participant Main as 🏗️ main
    participant DevGit as 💻 dev-odoo-github
    participant Distrib as 📦 dev-distrib-local
    participant Valid as 🔍 dev-validator
    participant DevOps as 🚀 devops-odoo

    Note over Cron,Ticket: Cada 30 minutos
    Cron->>Ticket: Ejecutar job incidencias-autonomas
    Ticket->>Ticket: Procesar tickets Pendientes (564)
    Ticket-->>Creator: (automático vía stage 703 en Odoo)

    Note over Cron,Creator: Cada 60 minutos
    Cron->>Creator: Heartbeat
    Creator->>Creator: Lee proyecto 53 (stage 703, user=2)
    Creator->>Creator: Lee proyecto 36
    Creator->>Creator: Crea proyectos + stages
    Creator-->>Arch: (automático vía proyectos sin etiqueta)

    Note over Cron,Arch: Cada 60 minutos
    Cron->>Arch: Heartbeat
    Arch->>Arch: Analiza proyectos sin tag
    Arch->>Main: (solicitud de desarrollo si tag=odoo)

    Note over Main,DevGit: On-demand
    Main->>DevGit: sessions_send: tarea de desarrollo
    DevGit->>DevGit: Implementa cambios + push
    DevGit->>Valid: sessions_send: "validar push <commit>"

    Note over Distrib,Valid: On-demand
    Distrib->>Distrib: Procesa /mnt/cambios-odoo-local
    Distrib->>Valid: sessions_send: "validar deploy"

    Note over Valid,DevOps: On-demand
    Valid->>Valid: Verifica DEV (5 min)
    Valid->>DevOps: sessions_send: "DEV OK, crear PR"

    Note over Cron,DevOps: Cada 60 minutos
    Cron->>DevOps: Heartbeat FASE 1
    DevOps->>DevOps: Verifica commits pendientes
    DevOps->>DevOps: Crea/revisa/aprueba PR
```
