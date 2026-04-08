# MEMORY — DevOps Odoo

> 📋 **AL INICIAR CUALQUIER TAREA**: Lee el archivo `memory/YYYY-MM-DD.md` de hoy (si existe) para tener contexto de los deploys del día. Usa la herramienta `read` con la ruta `memory/2026-03-27.md` (ajusta la fecha).

## Archivos de memoria diaria

| Fecha | Archivo |
|---|---|
| 2026-03-27 | [memory/2026-03-27.md](memory/2026-03-27.md) |

## Notas permanentes del proyecto

- Token GitHub: `${GITHUB_TOKEN}` — acceso escritura al repo.
- El mismo token NO puede aprobar PRs que él mismo creó (limitación GitHub). El merge siempre lo hace el usuario manualmente.
- Verificar merge via API (`merged: true`) antes de iniciar FASE 2.
- Credenciales RPC producción: `iallamadas@universidadisep.com` / `${ODOO_RPC_PASSWORD}` → `uid=5064` en DB `UisepFinal` en `https://app.universidadisep.com`.
- `odoo-app-prod` corre LOCAL en .58 — `docker` directo, sin SSH.
- Jenkins corre en .57 — no accesible desde este workspace. Asumir deploy completado tras la espera.
- Si RPC falla con `Fault 2: Odoo is currently processing a scheduled action` — es transitorio, esperar 60s y reintentar.

## Historial reciente — 2026-03-27

| Hora | PR | Módulo(s) | Estado |
|---|---|---|---|
| 03:00 | #61 | `isep_hotel_loyalty` | ✅ mergeado y actualizado |
| 03:33 | #62 | `isep_cloudbeds_sales` | ✅ mergeado y actualizado |
| ~03:30 | #63 | `isep_pos_restaurant_fix` | ❌ cerrado — fallo Jenkins CI |
| ~03:30 | #64 | Dev main latest | ❌ cerrado — sin contenido |
| 04:40 | #65 | `isep_enfasis_adicional` | ✅ mergeado e instalado (primera vez) |
| 05:11 | #66 | `isep_gestion_titulacion_custom`, `isep_gradebook`, `isep_website_custom` | ✅ mergeado y actualizado |
| 05:36 | #67 | `isep_tesis_model` | ✅ mergeado y actualizado |
