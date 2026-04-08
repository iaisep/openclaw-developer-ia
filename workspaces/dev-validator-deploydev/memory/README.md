# Memoria — Dev Validator DeployDev

Cada archivo en esta carpeta corresponde a un día de actividad: `YYYY-MM-DD.md`

## Formato de entrada por validación DEV

```
### HH:MM — Commit <hash> — <módulo>
- **Contenedor DEV:** ✅ Running / ❌ Caído
- **Logs Odoo DEV:** ✅ Sin errores / ❌ <detalle error>
- **HTTP DEV:** ✅ 200 / ❌ <código>
- **Módulo actualizado vía RPC:** ✅ state=installed / ⏭️ No requerido / ❌ <error>
- **Resultado:** ✅ Deploy DEV OK / ❌ Con problemas
- **Notas:** <cualquier anomalía>
```
