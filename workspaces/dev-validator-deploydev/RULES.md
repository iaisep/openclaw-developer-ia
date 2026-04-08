# Reglas — Dev Validator DeployDev

1. SIEMPRE esperar mínimo 2 minutos antes de iniciar la validación — Jenkins necesita tiempo para detectar el push y ejecutar el pipeline.
2. Si Jenkins todavía no muestra resultado al revisar (no hay `Finished:`), esperar 1 minuto más y revisar de nuevo. Máximo 3 intentos.
3. NUNCA marcar como exitoso si hay líneas `ERROR` o `CRITICAL` en el log de Odoo posteriores al timestamp del push.
4. Si el contenedor Odoo no aparece en `docker ps`, reportar inmediatamente como fallo crítico — no continuar con otros checks.
5. El reporte final SIEMPRE debe incluir las líneas exactas de error si se encontraron — no resumir ni parafrasear los errores.
6. No reiniciar contenedores ni modificar archivos en el servidor DEV — la única acción permitida es ejecutar la actualización del módulo via RPC.
7. SIEMPRE verificar que el módulo existe en Odoo DEV antes de intentar actualizarlo — si no existe, instalarlo con `button_immediate_install`.
8. Después de ejecutar la actualización RPC, SIEMPRE verificar el estado final del módulo (`state == 'installed'`) y revisar logs post-upgrade. No reportar éxito sin confirmar el estado.
9. Si la actualización RPC lanza una excepción, capturar el mensaje exacto y adjuntarlo al reporte — no reintentar automáticamente.
7. Registrar cada validación en `memory/YYYY-MM-DD.md` con commit hash, módulo y resultado.
