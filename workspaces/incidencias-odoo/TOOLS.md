# TOOLS — Incidencias Odoo

## PostgreSQL — Réplica espejo (LECTURA)

Servidor: `189.195.191.16` (servidor .57)
Contenedor: `postgres-replica-i4s8o8000kc040cgwcwowwwc`
DB: `UisepFinal`, usuario: `odoo`

```bash
ssh -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "docker exec postgres-replica-i4s8o8000kc040cgwcwowwwc \
   psql -U odoo -d UisepFinal -c 'SELECT id, name, description FROM project_task WHERE project_id=53 AND stage_id=564 AND active=true LIMIT 20'"
```

### Stage IDs del proyecto 53

| Stage | ID |
|---|---|
| Pendiente | 564 |
| En Proceso | 644 |
| Listo | 565 |
| En Revisión | 567 |
| Enviado a Proyecto | 703 |
| Anulado | 643 |

## Odoo XML-RPC — Producción (ESCRITURA)

```python
import xmlrpc.client
url = 'https://app.universidadisep.com'
db  = 'UisepFinal'
uid = 5064  # iallamadas@universidadisep.com
pwd = '${ODOO_RPC_PASSWORD}'
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
```

### Cambiar stage de una tarea

```python
models.execute_kw(db, uid, pwd, 'project.task', 'write',
  [[task_id], {'stage_id': 644}])  # 644 = En Proceso
```

### Escribir en el chatter (log note)

```python
models.execute_kw(db, uid, pwd, 'project.task', 'message_post',
  [[task_id]], {
    'body': '<p>Acción realizada por IA: ...</p>',
    'message_type': 'comment',
    'subtype_xmlid': 'mail.mt_note'
  })
```

### Leer detalles de una tarea

```python
tasks = models.execute_kw(db, uid, pwd, 'project.task', 'search_read',
  [[['project_id','=',53], ['stage_id','=',564]]],
  {'fields': ['id','name','description','partner_id','user_ids'], 'limit': 20})
```

## Flujo de resolución

1. Leer tarea desde réplica (SQL)
2. Cambiar stage a "En Proceso" (644) via RPC
3. Analizar y ejecutar solución via API/RPC de Odoo
4. Registrar resultado en chatter
5. Mover a "Listo" (565) o "Enviado a Proyecto" (703) si requiere dev
