# Reglas — DevOps Odoo

## FASE 1 — Revisión de PR

0. **NUNCA crear ni revisar un PR sin autorización explícita del usuario.** Al detectar commits pendientes en DEVMain_Latest, el único paso permitido es notificar al usuario con la lista de commits y esperar su respuesta afirmativa. No crear el PR, no revisar el diff, no ejecutar ninguna acción sobre GitHub hasta recibir "sí, crear PR" o equivalente. Esta regla tiene prioridad sobre cualquier otra instrucción.
1. NUNCA hacer merge manual — solo aprobar o cerrar via GitHub API.
2. SIEMPRE revisar el diff completo antes de emitir decisión.
3. NUNCA aprobar PRs con credenciales hardcodeadas en el código.
4. NUNCA aprobar PRs que modifiquen archivos fuera de `addons_uisep/` sin justificación.
5. Al cerrar un PR, SIEMPRE comentar primero el motivo exacto con archivo y línea afectada antes de ejecutar el cierre.
6. Revisar TODOS los PRs abiertos, no solo el más reciente.
7. Si un PR tiene conflictos de merge, cerrarlo con instrucción de resolución.
8. Dejar registro en `memory/YYYY-MM-DD.md` de cada PR revisado (número, título, decisión).

## FASE 2 — Validación post-deploy producción

9. SIEMPRE esperar mínimo 7 minutos después del merge antes de iniciar la validación — Jenkins en producción tarda ~5-7 min. No reducir este tiempo bajo ninguna circunstancia.
9c. Odoo Producción (`odoo-app-prod`) corre en el servidor LOCAL (.58). Los comandos `docker ps`, `docker logs` se ejecutan SIN SSH. Si algún comando requiere SSH para acceder a `odoo-app-prod`, es incorrecto — corregir el comando. Solo Jenkins (en servidor .57) requiere SSH.
9d. NUNCA confundir el contenedor DEV (`odoo_latest-w8co804sck0ssc0swkcgw488`) con producción (`odoo-app-prod`). Son servidores distintos. Este agente NUNCA interactúa con contenedores DEV.
9b. NUNCA delegar el upgrade del módulo al usuario con mensajes como "ir a Apps → Actualizar". El agente SIEMPRE ejecuta el upgrade via RPC (`button_immediate_upgrade`) directamente. Si el RPC falla, reportar el error — no pedirle al usuario que lo haga manualmente.
9e. NUNCA decir "no tengo credenciales de Odoo" ni "no puedo acceder vía RPC". Las credenciales están en el SOUL.md (ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASS). Siempre están disponibles. Ejecutar el RPC sin preguntar.
9f. SIEMPRE verificar el estado del PR via GitHub API antes de iniciar FASE 2. El campo `merged` debe ser `true`. No asumir merge basándose en lo que dice el usuario sin confirmar con la API.
10. No se verifica Jenkins — no hay acceso desde este workspace. Asumir deploy completado tras la espera de 7 minutos.
11. NUNCA marcar como exitoso si hay `ERROR` o `CRITICAL` en los logs de producción.
12. La única acción permitida sobre producción es la actualización del módulo via RPC — no reiniciar contenedores ni modificar archivos.
13. Después de ejecutar `button_immediate_upgrade`, SIEMPRE verificar que `state == 'installed'` y revisar logs post-upgrade.
14. Si la actualización RPC lanza excepción, adjuntar el error exacto al reporte — no reintentar automáticamente.
15. SIEMPRE guardar resumen en `memory/YYYY-MM-DD.md` al finalizar cada deploy — tanto FASE 1 como FASE 2. Si el archivo del día no existe, crearlo. Si existe, agregar la nueva entrada al final. Nunca terminar un deploy sin escribir la memoria.

## SKILL: revertir-devmain

16. **NUNCA ejecutar la skill `revertir-devmain` de forma automática.** No puede ser invocada por heartbeat, cron, ni por otro agente. Solo un humano puede solicitarla con palabras explícitas como "revertir DEVMain_Latest", "resetear la rama" o "ejecutar skill revertir-devmain".
17. Antes de ejecutar la skill, SIEMPRE pedir confirmación explícita al usuario via agente `main` y ESPERAR respuesta. No proceder con el reset hasta recibir "sí, revertir" o equivalente.
18. SIEMPRE listar los commits que se van a eliminar antes de hacer el force push, para que el usuario sea consciente del alcance.
19. SIEMPRE registrar la ejecución en `memory/YYYY-MM-DD.md` con la lista de commits eliminados y el SHA destino.
