# AGENTS.md — Dev Validator DeployDev

Este agente es invocado por `dev-distrib-local` vía `sessions_send` después de cada push exitoso a `DEVMain_Latest`.

## Quién lo invoca

| Agente | Cuándo |
|---|---|
| `dev-distrib-local` | Inmediatamente después de cada commit+push exitoso |

## Mensaje esperado de invocación

```
Validar deploy DEV.
Commit: <hash>
Módulo: <nombre_modulo>
Push realizado a las: <HH:MM>
```
