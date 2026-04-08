# TOOLS — Dev Odoo Local

## Contenedor odoo-migration (local en .58)

- Ruta addons: `/data/odoo-migration/odoo16/addons-extra/`
- Montado en el agente como: `/mnt/odoo-migration-addons/`

Acceso directo a los archivos sin SSH — el directorio está montado como volumen.

## Exportar archivos modificados

Después de editar un módulo, copiar solo los archivos cambiados:

```
Destino: /mnt/cambios-odoo-local/<nombre_modulo>/
```

Estructura esperada:
```
/mnt/cambios-odoo-local/
  sale_custom/
    models/
      sale_order.py
    __manifest__.py
```

Crear la carpeta del módulo si no existe. Solo incluir archivos realmente modificados.

## Odoo RPC — Producción (verificación)

```python
import xmlrpc.client
url = 'https://app.universidadisep.com'
db  = 'UisepFinal'
uid = 5064
pwd = '${ODOO_RPC_PASSWORD}'
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
```

## PostgreSQL — Réplica espejo (lectura)

```bash
ssh -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "docker exec postgres-replica-i4s8o8000kc040cgwcwowwwc \
   psql -U odoo -d UisepFinal -c 'SELECT ...'"
```

## Notas

- NO hacer push a GitHub desde este agente.
- NO reiniciar Odoo — los cambios son en local/staging.
- Documentar cada cambio con un comentario en el archivo exportado.
