---
name: crear-proyecto-desde-fuente
description: Crea un proyecto de desarrollo de software en Odoo a partir de una tarea fuente (Incidencias TI o Pote). Crea los 6 stages estándar, la tarea inicial de análisis con la descripción original, y limpia la tarea fuente según su origen.
---

# SKILL: Crear Proyecto desde Fuente (Incidencias TI o Pote)

Convierte una tarea de Incidencias TI o de Pote en un proyecto formal de desarrollo con estructura estándar de software.

---

## Parámetros de entrada

| Parámetro | Descripción |
|---|---|
| `source_task_id` | ID de la tarea fuente en Odoo |
| `source_project` | `incidencias` o `pote` |
| `task_name` | Nombre de la tarea fuente (será el nombre del proyecto) |
| `task_desc` | Descripción completa de la tarea fuente |

---

## Conexión RPC

```python
import xmlrpc.client, ssl

url = 'https://app.universidadisep.com'
db  = 'UisepFinal'
uid = 5064
pwd = '${ODOO_RPC_PASSWORD}'

ctx = ssl.create_default_context()
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', context=ctx)
```

---

## Paso 0 — Verificar duplicados

```python
count = models.execute_kw(db, uid, pwd, 'project.project', 'search_count',
    [[['name', '=', task_name], ['active', 'in', [True, False]]]])
if count > 0:
    print(f"SKIP: Ya existe un proyecto con el nombre '{task_name}'. Omitiendo.")
    # Registrar en memory/ y salir
    exit(0)
```

---

## Paso 1 — Crear el proyecto

```python
desc_final = task_desc if task_desc else f'[Sin descripción — revisar tarea fuente ID: {source_task_id}]'

project_id = models.execute_kw(db, uid, pwd, 'project.project', 'create', [{
    'name': task_name,
    'description': desc_final,
    'user_id': 5064,                   # Maikel Guzman como PM
    'privacy_visibility': 'employees',
}])
print(f"✅ Proyecto creado: ID={project_id}, Nombre='{task_name}'")
```

---

## Paso 2 — Crear los 6 stages estándar de desarrollo de software

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
    print(f"  Stage '{nombre}' creado con ID={sid}")

# stage_ids[0] = ID del stage "Análisis"
analisis_stage_id = stage_ids[0]
```

---

## Paso 3 — Crear tarea "Análisis de requerimientos y alcance"

```python
analysis_task_id = models.execute_kw(db, uid, pwd, 'project.task', 'create', [{
    'name': 'Análisis de requerimientos y alcance',
    'project_id': project_id,
    'stage_id': analisis_stage_id,
    'description': desc_final,     # Descripción íntegra de la tarea fuente
    'user_ids': [(4, 5064)],       # Asignada a Maikel
    'priority': '1',               # Alta prioridad
}])
print(f"✅ Tarea de análisis creada: ID={analysis_task_id}")
```

---

## Paso 4A — Limpiar tarea fuente: Incidencias TI

> Usar cuando `source_project == 'incidencias'`

```python
# Reasignar a Maikel Guzman (id=5064) — reemplaza al Administrator
models.execute_kw(db, uid, pwd, 'project.task', 'write',
    [[source_task_id], {'user_ids': [(6, 0, [5064])]}])

# Nota en chatter
models.execute_kw(db, uid, pwd, 'project.task', 'message_post',
    [[source_task_id]], {
        'body': (
            f'<p>✅ <b>Proyecto creado automáticamente por Dev Project Creator</b></p>'
            f'<p><b>Proyecto:</b> {task_name}</p>'
            f'<p><b>ID Odoo:</b> {project_id}</p>'
            f'<p><b>Primera tarea:</b> "Análisis de requerimientos y alcance" (ID: {analysis_task_id})</p>'
            f'<p>Asignado cambiado a Maikel Guzman para evitar reprocesamiento en futuras rondas.</p>'
        ),
        'message_type': 'comment',
        'subtype_xmlid': 'mail.mt_note'
    })
print(f"✅ Tarea fuente {source_task_id} reasignada a Maikel Guzman")
```

---

## Paso 4B — Limpiar tarea fuente: Pote

> Usar cuando `source_project == 'pote'`

```python
# Agregar mensaje a la descripción y archivar
desc_actual = task_desc or ''
nueva_desc = desc_actual + '\n\n---\n✅ creado como proyecto'

# Nota en chatter primero (antes de archivar)
models.execute_kw(db, uid, pwd, 'project.task', 'message_post',
    [[source_task_id]], {
        'body': (
            f'<p>✅ <b>Tarea convertida a proyecto</b></p>'
            f'<p><b>Proyecto:</b> {task_name}</p>'
            f'<p><b>ID Odoo:</b> {project_id}</p>'
            f'<p><b>Primera tarea:</b> "Análisis de requerimientos y alcance" (ID: {analysis_task_id})</p>'
            f'<p>Esta tarea ha sido archivada. El trabajo continúa en el nuevo proyecto.</p>'
        ),
        'message_type': 'comment',
        'subtype_xmlid': 'mail.mt_note'
    })

# Archivar la tarea
models.execute_kw(db, uid, pwd, 'project.task', 'write',
    [[source_task_id], {
        'active': False,
        'description': nueva_desc,
    }])
print(f"✅ Tarea fuente {source_task_id} archivada con mensaje 'creado como proyecto'")
```

---

## Paso 5 — Registrar en memory/

```python
from datetime import datetime

log_entry = (
    f"- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] "
    f"Proyecto creado: \"{task_name}\" (ID: {project_id}) | "
    f"Fuente: {source_project} tarea #{source_task_id}\n"
)

# Agregar al archivo memory/proyectos-creados.md
with open('memory/proyectos-creados.md', 'a') as f:
    f.write(log_entry)
print(f"✅ Log registrado en memory/")
```

---

## Script Python completo (ejecutable)

```python
#!/usr/bin/env python3
"""
crear_proyecto.py — Dev Project Creator
Uso: python3 crear_proyecto.py <source_task_id> <source_project> "<task_name>" "<task_desc>"
"""
import xmlrpc.client, ssl, sys
from datetime import datetime

url = 'https://app.universidadisep.com'
db  = 'UisepFinal'
uid = 5064
pwd = '${ODOO_RPC_PASSWORD}'

def main(source_task_id, source_project, task_name, task_desc):
    ctx = ssl.create_default_context()
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', context=ctx)

    # Paso 0 — Anti-duplicados
    count = models.execute_kw(db, uid, pwd, 'project.project', 'search_count',
        [[['name', '=', task_name], ['active', 'in', [True, False]]]])
    if count > 0:
        print(f"SKIP: Proyecto '{task_name}' ya existe.")
        return

    desc_final = task_desc if task_desc else f'[Sin descripción — revisar tarea fuente ID: {source_task_id}]'

    # Paso 1 — Crear proyecto
    project_id = models.execute_kw(db, uid, pwd, 'project.project', 'create', [{
        'name': task_name,
        'description': desc_final,
        'user_id': 5064,
        'privacy_visibility': 'employees',
    }])
    print(f"Proyecto creado ID={project_id}")

    # Paso 2 — Crear stages
    stages_config = [
        ('Análisis', 1), ('Diseño', 2), ('Desarrollo', 3),
        ('Pruebas / QA', 4), ('Producción', 5), ('Cerrado', 6),
    ]
    stage_ids = []
    for nombre, seq in stages_config:
        sid = models.execute_kw(db, uid, pwd, 'project.task.type', 'create', [{
            'name': nombre, 'sequence': seq,
            'project_ids': [(4, project_id)],
        }])
        stage_ids.append(sid)

    # Paso 3 — Crear tarea de análisis
    analysis_task_id = models.execute_kw(db, uid, pwd, 'project.task', 'create', [{
        'name': 'Análisis de requerimientos y alcance',
        'project_id': project_id,
        'stage_id': stage_ids[0],
        'description': desc_final,
        'user_ids': [(4, 5064)],
        'priority': '1',
    }])
    print(f"Tarea análisis ID={analysis_task_id}")

    nota_body = (
        f'<p>✅ <b>Proyecto creado por Dev Project Creator</b></p>'
        f'<p><b>Proyecto:</b> {task_name} (ID: {project_id})</p>'
        f'<p><b>Primera tarea:</b> "Análisis de requerimientos y alcance" (ID: {analysis_task_id})</p>'
    )

    # Paso 4 — Limpiar tarea fuente
    if source_project == 'incidencias':
        # Reasignar a Maikel (5064)
        models.execute_kw(db, uid, pwd, 'project.task', 'write',
            [[source_task_id], {'user_ids': [(6, 0, [5064])]}])
        nota_body += '<p>Asignado cambiado a Maikel Guzman (anti-reprocesamiento).</p>'
        models.execute_kw(db, uid, pwd, 'project.task', 'message_post',
            [[source_task_id]], {'body': nota_body, 'message_type': 'comment',
                                  'subtype_xmlid': 'mail.mt_note'})
        print(f"Tarea {source_task_id} reasignada a Maikel")
    elif source_project == 'pote':
        # Nota antes de archivar
        nota_body += '<p>Tarea archivada. El trabajo continúa en el nuevo proyecto.</p>'
        models.execute_kw(db, uid, pwd, 'project.task', 'message_post',
            [[source_task_id]], {'body': nota_body, 'message_type': 'comment',
                                  'subtype_xmlid': 'mail.mt_note'})
        # Archivar con mensaje en descripción
        nueva_desc = (task_desc or '') + '\n\n---\n✅ creado como proyecto'
        models.execute_kw(db, uid, pwd, 'project.task', 'write',
            [[source_task_id], {'active': False, 'description': nueva_desc}])
        print(f"Tarea {source_task_id} archivada")

    # Paso 5 — Log en memory
    log_entry = (
        f"- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] "
        f"Proyecto: \"{task_name}\" (ID: {project_id}) | "
        f"Fuente: {source_project} tarea #{source_task_id}\n"
    )
    import os
    os.makedirs('memory', exist_ok=True)
    with open('memory/proyectos-creados.md', 'a') as f:
        f.write(log_entry)

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Uso: python3 crear_proyecto.py <source_task_id> <source_project> '<name>' '<desc>'")
        sys.exit(1)
    main(int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4])
```

---

## Reglas de esta skill

- Si la creación del proyecto falla en cualquier paso (error RPC), **no tocar** la tarea fuente.
- Si `task_desc` está vacío, usar `[Sin descripción — revisar tarea fuente ID: X]` como descripción.
- Siempre crear los 6 stages en el orden definido: Análisis, Diseño, Desarrollo, Pruebas/QA, Producción, Cerrado.
- La tarea "Análisis de requerimientos y alcance" siempre va en el stage "Análisis" (primer stage).
- Registrar resultado en `memory/proyectos-creados.md`.
