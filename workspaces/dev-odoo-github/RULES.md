# Reglas — Dev Odoo GitHub

1. SIEMPRE hacer `git pull origin DEVMain_Latest` antes de editar cualquier archivo.
2. NUNCA tocar la rama `main` — solo trabajar en `DEVMain_Latest`.
3. NUNCA reiniciar Odoo en DEV manualmente — Jenkins lo hace.
4. NUNCA hacer `git push` sin commit previo con mensaje descriptivo.
5. Editar siempre en `/home/maikel/github/Odoo16UISEP_DEVMain/...` — NUNCA en `/data/coolify/services/...`.
6. Hacer `search_read` antes de cualquier `write` o `unlink` RPC.
7. NUNCA ejecutar `unlink` masivos (>10 registros) sin confirmación del usuario.
8. Logear cada operación de escritura RPC realizada.
9. Si hay error en Odoo logs post-deploy, notificar al Dev Lead inmediatamente.
10. NUNCA cambiar credenciales ni archivos de configuración del servidor.
