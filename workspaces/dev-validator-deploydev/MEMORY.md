# MEMORY — Dev Validator DeployDev

> 📋 **AL INICIAR CUALQUIER TAREA**: Lee el archivo `memory/YYYY-MM-DD.md` de hoy (si existe) para tener contexto de las validaciones del día.

## Archivos de memoria diaria

| Fecha | Archivo |
|---|---|
| 2026-03-27 | [memory/2026-03-27.md](memory/2026-03-27.md) |

## Notas permanentes del proyecto

- Contenedor Odoo DEV: `odoo_latest-w8co804sck0ssc0swkcgw488` en servidor .57 — requiere SSH con `/.keys/odoo-dev.pem`.
- Credenciales RPC DEV: `iallamadas@universidadisep.com` / `${ODOO_RPC_PASSWORD}` → DB `final` en `https://dev.odoo.universidadisep.com`.
- Jenkins no es accesible desde este workspace — asumir deploy completado tras espera de 5 min.
- Después de validar DEV exitosamente → disparar `devops-odoo` automáticamente.
- Si RPC falla con `Fault 2: Odoo is currently processing a scheduled action` — esperar 60s y reintentar.
