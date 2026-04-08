# TOOLS — Dev Project Creator

## PostgreSQL — Réplica espejo (LECTURA)

Servidor: `189.195.191.16`
Contenedor: `postgres-replica-i4s8o8000kc040cgwcwowwwc`
DB: `UisepFinal`, usuario: `odoo`
Llave SSH: `/.keys/odoo-dev.pem`

### Leer tareas de Incidencias TI en "Enviado a Proyecto" asignadas a Administrator

```bash
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "docker exec postgres-replica-i4s8o8000kc040cgwcwowwwc psql -U odoo -d UisepFinal -t -A -F'|' -c \"
    SELECT pt.id, pt.name, pt.description, pt.priority
    FROM project_task pt
    JOIN project_task_res_users_rel pu ON pu.project_task_id = pt.id
    WHERE pt.project_id = 53
      AND pt.stage_id = 703
      AND pt.active = true
      AND pu.res_users_id = 2
    ORDER BY pt.priority DESC, pt.id ASC;
  \""
```

### Leer tareas activas del proyecto Pote (id=36)

```bash
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "docker exec postgres-replica-i4s8o8000kc040cgwcwowwwc psql -U odoo -d UisepFinal -t -A -F'|' -c \"
    SELECT pt.id, pt.name, pt.description, pt.priority
    FROM project_task pt
    WHERE pt.project_id = 36
      AND pt.active = true
    ORDER BY pt.id ASC;
  \""
```

---

## Odoo XML-RPC — Producción (ESCRITURA)

```python
import xmlrpc.client, ssl

url = 'https://app.universidadisep.com'
db  = 'UisepFinal'
uid = 5064   # iallamadas@universidadisep.com / Maikel Guzman
pwd = '${ODOO_RPC_PASSWORD}'

ctx = ssl.create_default_context()
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', context=ctx)
```

### Verificar si ya existe un proyecto con ese nombre (anti-duplicados)

```python
count = models.execute_kw(db, uid, pwd, 'project.project', 'search_count',
    [[['name', '=', nombre_proyecto], ['active', 'in', [True, False]]]])
# Si count > 0, el proyecto ya existe — OMITIR
```

### Crear proyecto nuevo

```python
project_id = models.execute_kw(db, uid, pwd, 'project.project', 'create', [{
    'name': task_name,
    'description': task_desc,
    'user_id': 5064,
    'privacy_visibility': 'employees',
}])
```

### Crear stages de tarea para el proyecto (estructura estándar de software)

```python
stages_config = [
    ('Análisis',     1),
    ('Diseño',       2),
    ('Desarrollo',   3),
    ('Pruebas / QA', 4),
    ('Producción',   5),
    ('Cerrado',      6),
]
stage_ids = []
for nombre, seq in stages_config:
    sid = models.execute_kw(db, uid, pwd, 'project.task.type', 'create', [{
        'name': nombre,
        'sequence': seq,
        'project_ids': [(4, project_id)],
    }])
    stage_ids.append(sid)
# stage_ids[0] = ID del stage "Análisis"
```

### Crear tarea "Análisis de requerimientos y alcance"

```python
analysis_task_id = models.execute_kw(db, uid, pwd, 'project.task', 'create', [{
    'name': 'Análisis de requerimientos y alcance',
    'project_id': project_id,
    'stage_id': stage_ids[0],
    'description': task_desc,   # Descripción íntegra de la tarea fuente
    'user_ids': [(4, 5064)],
    'priority': '1',
}])
```

### Reasignar tarea fuente (Incidencias TI → Maikel, id=5064)

```python
models.execute_kw(db, uid, pwd, 'project.task', 'write',
    [[source_task_id], {'user_ids': [(6, 0, [5064])]}])
```

### Archivar tarea fuente (Pote)

```python
models.execute_kw(db, uid, pwd, 'project.task', 'write',
    [[source_task_id], {
        'active': False,
        'description': (task_desc or '') + '\n\n---\n✅ creado como proyecto'
    }])
```

### Nota en chatter de tarea fuente

```python
models.execute_kw(db, uid, pwd, 'project.task', 'message_post',
    [[source_task_id]], {
        'body': f'<p>✅ <b>Proyecto creado:</b> {task_name} (ID: {project_id})</p>',
        'message_type': 'comment',
        'subtype_xmlid': 'mail.mt_note'
    })
```

---

## IDs de referencia

| Elemento | ID |
|---|---|
| Proyecto Incidencias TI | 53 |
| Stage "Enviado a Proyecto" (Incidencias) | 703 |
| Proyecto Pote / Innovación | 36 |
| Usuario Administrator | 2 |
| Usuario Maikel Guzman | 5064 |
