# TOOLS — Dev Project Architect

## Odoo XML-RPC — Producción (LECTURA y ESCRITURA)

```python
import xmlrpc.client, ssl

url  = 'https://app.universidadisep.com'
db   = 'UisepFinal'
uid  = 5064
pwd  = '${ODOO_RPC_PASSWORD}'
user = 'iallamadas@universidadisep.com'

ctx    = ssl.create_default_context()
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', context=ctx)
```

### Leer proyectos recién creados sin etiqueta de herramienta (24-29)

```python
# Proyectos activos con etiqueta Tecnología (1) pero sin etiqueta de herramienta asignada
todos = models.execute_kw(db, uid, pwd, 'project.project', 'search_read',
    [[['active', '=', True], ['tag_ids', 'in', [1]]]],
    {'fields': ['id', 'name', 'description', 'tag_ids']})

herramienta_ids = {24, 25, 26, 27, 28, 29}
pendientes = [p for p in todos if not herramienta_ids.intersection(set(p['tag_ids']))]
```

### Leer descripción completa de un proyecto

```python
proj = models.execute_kw(db, uid, pwd, 'project.project', 'read',
    [[project_id]], {'fields': ['id', 'name', 'description', 'tag_ids']})
```

### Leer también la tarea "Análisis de requerimientos y alcance" (descripción original)

```python
tarea_analisis = models.execute_kw(db, uid, pwd, 'project.task', 'search_read',
    [[['project_id', '=', project_id],
      ['name', '=', 'Análisis de requerimientos y alcance']]],
    {'fields': ['id', 'name', 'description']})
```

### Asignar etiqueta de herramienta al proyecto

```python
# tag_id: 24=n8n | 25=odoo | 26=chatwoot | 27=mautic | 28=wordpress | 29=desarrollos-apis
models.execute_kw(db, uid, pwd, 'project.project', 'write',
    [[project_id], {'tag_ids': [(4, tag_id)]}])
```

### Nota de inicio de análisis en chatter

```python
models.execute_kw(db, uid, pwd, 'project.project', 'message_post',
    [[project_id]], {
        'body': '<p>🏛️ <b>Dev Project Architect</b> — Iniciando análisis de herramienta...</p>',
        'message_type': 'comment',
        'subtype_xmlid': 'mail.mt_note'
    })
```

### Nota de decisión final en chatter

```python
models.execute_kw(db, uid, pwd, 'project.project', 'message_post',
    [[project_id]], {
        'body': (
            f'<p>🏛️ <b>Herramienta recomendada: {herramienta}</b></p>'
            f'<hr/>'
            f'<p><b>Justificación:</b><br/>{justificacion}</p>'
            f'<p><b>Consideraciones sobre Odoo 16:</b><br/>{nota_odoo}</p>'
        ),
        'message_type': 'comment',
        'subtype_xmlid': 'mail.mt_note'
    })
```

---

## IDs de etiquetas de herramienta

| Etiqueta | ID |
|---|---|
| n8n | 24 |
| odoo | 25 |
| chatwoot | 26 |
| mautic | 27 |
| wordpress | 28 |
| desarrollos-apis | 29 |

## AWS SES

```
SMTP_HOST = email-smtp.us-east-1.amazonaws.com
SMTP_PORT = 587
SMTP_USER = ${AWS_SES_USER}
SMTP_PASS = ${AWS_SES_PASSWORD}
FROM      = mguzman@universidadisep.com
```
