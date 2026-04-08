# AGENTS.md — Dev Distrib Local

Este agente no tiene sub-agentes propios.

## Colaboración con otros agentes del equipo

| Agente | Relación |
|---|---|
| `dev-odoo-local` | Produce los archivos en `/mnt/cambios-odoo-local/` que este agente distribuye |
| `dev-odoo-github` | Trabaja directamente en el servidor DEV con SSH — no duplicar trabajo |
| `devops-odoo` | Revisa los PRs que llegan a `main` desde `DEVMain_Latest` |

## Delegación obligatoria post-push

Después de cada push exitoso a `DEVMain_Latest`, SIEMPRE notificar a `dev-validator-deploydev` via `sessions_send`:

```
agentId: "dev-validator-deploydev"
mensaje: "Validar deploy DEV.\nCommit: <hash>\nMódulo: <nombre>\nPush realizado a las: <HH:MM>"
```

## Quién puede dejar archivos en la carpeta de entrada

- El agente `dev-odoo-local` (automáticamente tras modificaciones)
- Un desarrollador humano que copie archivos manualmente a `/home/maikel/cambios_odoo_local/`
