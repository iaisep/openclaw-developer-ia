# TOOLS — Dev Odoo GitHub

## SSH — Servidor DEV Odoo

```bash
ssh -i /.keys/odoo-dev.pem root@189.195.191.16
```

- Contenedor Odoo DEV: Coolify ID `w8co804sck0ssc0swkcgw488`
- Directorio addons: `/opt/odoo/addons-extra/` (dentro del contenedor)
- Acceder al contenedor: `docker exec -it <container_id> bash`

## Git / GitHub

- Repo: `Universidad-ISEP/Odoo16UISEP`
- Rama de trabajo: `DEVMain_Latest`
- Token: `${GITHUB_TOKEN}`
- Remote URL con auth: `https://${GITHUB_TOKEN}@github.com/Universidad-ISEP/Odoo16UISEP.git`

### Flujo estándar

```bash
cd /opt/odoo/addons-extra/<modulo>
git add .
git commit -m "feat(<modulo>): descripción del cambio"
git push origin DEVMain_Latest
```

Jenkins despliega automáticamente. **Nunca reiniciar Odoo manualmente.**

## Odoo RPC — Producción

```python
import xmlrpc.client
url = 'https://app.universidadisep.com'
db  = 'UisepFinal'
uid = 5064  # iallamadas@universidadisep.com
pwd = '${ODOO_RPC_PASSWORD}'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
# uid = common.authenticate(db, 'iallamadas@universidadisep.com', pwd, {})
```

## PostgreSQL — Réplica espejo (lectura)

```bash
ssh -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "docker exec postgres-replica-i4s8o8000kc040cgwcwowwwc \
   psql -U odoo -d UisepFinal -c 'SELECT ...'"
```

## GitHub API — Pull Requests

```bash
curl -H "Authorization: token ${GITHUB_TOKEN}" \
  https://api.github.com/repos/Universidad-ISEP/Odoo16UISEP/pulls
```
