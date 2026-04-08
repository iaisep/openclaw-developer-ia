# Tools — Dev Validator DeployDev

## SSH
```
Servidor: 189.195.191.16
Llave:    /.keys/odoo-dev.pem
```

## Contenedores DEV (servidor .57)

| Contenedor | Función |
|---|---|
| `odoo_latest-w8co804sck0ssc0swkcgw488` | Odoo DEV principal |
| `pgodoo_latest-w8co804sck0ssc0swkcgw488` | PostgreSQL DEV |
| `redisodoo-w8co804sck0ssc0swkcgw488` | Redis DEV |
| `jenkins-c8kwgocc4coc8swkksco4kko` | Jenkins CI/CD |

## Comandos clave

```bash
# Estado contenedor Odoo DEV
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "docker ps --filter name=odoo_latest-w8co804sck0ssc0swkcgw488 --format 'table {{.Names}}\t{{.Status}}'"

# Logs Odoo DEV (últimas 100 líneas)
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "tail -100 /data/coolify/services/w8co804sck0ssc0swkcgw488/log/odoo-bin.log"

# Logs Jenkins (últimas 80 líneas)
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "docker logs --tail 80 jenkins-c8kwgocc4coc8swkksco4kko 2>&1"

# Health check HTTP
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://dev.odoo.universidadisep.com/web/health"

# Buscar errores en log desde hace 10 minutos
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "grep -E 'ERROR|CRITICAL|cannot import|ParseError|Module.*not found' \
   /data/coolify/services/w8co804sck0ssc0swkcgw488/log/odoo-bin.log | tail -20"
```

## XML-RPC Odoo DEV

```python
import xmlrpc.client, ssl

ODOO_URL  = "https://dev.odoo.universidadisep.com"
ODOO_DB   = "final"
ODOO_USER = "iallamadas@universidadisep.com"
ODOO_PASS = "${ODOO_RPC_PASSWORD}"

ctx = ssl.create_default_context()
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common", context=ctx)
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object", context=ctx)

# Verificar estado del módulo
models.execute_kw(ODOO_DB, uid, ODOO_PASS,
    'ir.module.module', 'search_read',
    [[['name', '=', '<modulo>']]],
    {'fields': ['name', 'state', 'installed_version']}
)

# Actualizar módulo instalado
models.execute_kw(ODOO_DB, uid, ODOO_PASS,
    'ir.module.module', 'button_immediate_upgrade',
    [[<module_id>]]
)

# Instalar módulo nuevo
models.execute_kw(ODOO_DB, uid, ODOO_PASS,
    'ir.module.module', 'button_immediate_install',
    [[<module_id>]]
)
```

## URLs
- DEV: `https://dev.odoo.universidadisep.com`
- Jenkins: `https://jenkins.universidadisep.com`
