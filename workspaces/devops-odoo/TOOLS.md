# TOOLS — DevOps Odoo

## GitHub API

```
Token: ${GITHUB_TOKEN}
Repo:  Universidad-ISEP/Odoo16UISEP
PR:    DEVMain_Latest → main
```

### Comandos PR

```bash
# Listar PRs abiertos hacia main
curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
  "https://api.github.com/repos/Universidad-ISEP/Odoo16UISEP/pulls?state=open&base=main" \
  | python3 -c "import sys,json; prs=json.load(sys.stdin); [print(p['number'], p['title'], p['head']['ref']) for p in prs]"

# Archivos cambiados en PR
curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
  "https://api.github.com/repos/Universidad-ISEP/Odoo16UISEP/pulls/<PR>/files" \
  | python3 -c "import sys,json; [print(f['filename'], f['status'], '+'+str(f['additions']), '-'+str(f['deletions'])) for f in json.load(sys.stdin)]"

# Diff del PR
curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
     -H "Accept: application/vnd.github.v3.diff" \
  "https://api.github.com/repos/Universidad-ISEP/Odoo16UISEP/pulls/<PR>" | head -300

# Aprobar PR
curl -s -X POST -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/Universidad-ISEP/Odoo16UISEP/pulls/<PR>/reviews" \
  -d '{"event":"APPROVE","body":"✅ Revisado y aprobado."}'

# Comentar en PR
curl -s -X POST -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/Universidad-ISEP/Odoo16UISEP/issues/<PR>/comments" \
  -d '{"body":"<mensaje>"}'

# Cerrar PR
curl -s -X PATCH -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/Universidad-ISEP/Odoo16UISEP/pulls/<PR>" \
  -d '{"state":"closed"}'
```

---

## Odoo Producción (.58 — local, sin SSH)

```bash
# Estado contenedor
docker ps --filter name=odoo-app-prod --format "table {{.Names}}\t{{.Status}}"

# Logs producción
docker logs --tail 100 odoo-app-prod 2>&1

# Buscar errores en logs
docker logs --tail 100 odoo-app-prod 2>&1 | grep -E "ERROR|CRITICAL|cannot import|ParseError" | tail -20

# Health check HTTP
curl -s -o /dev/null -w '%{http_code}' --max-time 20 https://app.universidadisep.com/web/health
```

## Jenkins (.57 — via SSH)

```bash
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "docker logs --tail 80 jenkins-c8kwgocc4coc8swkksco4kko 2>&1 | tail -40"
```

## XML-RPC Producción

```python
import xmlrpc.client, ssl

ODOO_URL  = "https://app.universidadisep.com"
ODOO_DB   = "UisepFinal"
ODOO_USER = "iallamadas@universidadisep.com"
ODOO_PASS = "${ODOO_RPC_PASSWORD}"

ctx = ssl.create_default_context()
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common", context=ctx)
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object", context=ctx)

# Estado del módulo
models.execute_kw(ODOO_DB, uid, ODOO_PASS,
    'ir.module.module', 'search_read',
    [[['name', '=', '<modulo>']]],
    {'fields': ['name', 'state', 'installed_version']}
)

# Actualizar módulo instalado
models.execute_kw(ODOO_DB, uid, ODOO_PASS,
    'ir.module.module', 'button_immediate_upgrade', [[<id>]])

# Instalar módulo nuevo
models.execute_kw(ODOO_DB, uid, ODOO_PASS,
    'ir.module.module', 'button_immediate_install', [[<id>]])
```
