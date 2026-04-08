# Reglas — Dev Odoo Local

1. Trabajar SIEMPRE en `/mnt/odoo-migration-addons/addons_uisep/` — nunca fuera de este path.
2. Exportar a `/mnt/cambios-odoo-local/<modulo>/` SOLO los archivos modificados, nunca el módulo completo.
3. Crear siempre el archivo `CAMBIOS.md` en cada carpeta exportada con la lista de archivos y motivo.
4. Verificar cambios con `docker exec odoo-app-prod` antes de exportar.
5. Si el contenedor odoo-migration no está corriendo, iniciarlo con `cd /data/odoo-migration && docker compose up -d`.
6. Nunca modificar archivos de configuración del servidor ni del docker-compose.
7. Nunca escribir en producción (`odoo_latest` / `pgodoo_latest`) — solo en el entorno local (odoo-migration).
8. Logear en CAMBIOS.md el resultado del upgrade del módulo (ok/error).
