---
name: fusion-contactos-duplicados
description: Fusión de contactos duplicados en Odoo (res_partner). Usar cuando un ticket reporta que un estudiante tiene dos cuentas, no puede acceder al portal, sus datos están divididos entre dos perfiles, o aparece duplicado en el sistema.
---

# SKILL: Fusión de Contactos Duplicados en Odoo (res_partner)

**Última actualización:** 2026-03-26
**Nivel de riesgo:** 🔴 ALTO (modifica múltiples tablas)

---

## Reglas Críticas

1. **NUNCA eliminar** registros de `res_partner` — solo archivar (`active = false`)
2. **NUNCA eliminar** registros de `res_users` — solo desactivar (`active = false`)
3. **El partner principal** es el que tiene: usuario activo (`res_users`), estudiante activo (`op_student`), y admisiones con `state='done'`
4. **Siempre verificar** antes de mover datos
5. **Invalidar cachés** al final de cada operación
6. Por el nivel de riesgo ALTO, **informar al usuario** antes de ejecutar las modificaciones

---

## Cómo ejecutar las queries

```bash
# DIAGNÓSTICO (réplica espejo, solo lectura)
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "docker exec postgres-replica-i4s8o8000kc040cgwcwowwwc psql -U odoo -d UisepFinal -c '<QUERY>'"
```

Las **modificaciones** se aplican via **Odoo XML-RPC** en producción (ver TOOLS.md).
Para operaciones masivas (UPDATE de múltiples tablas), solicitar confirmación del usuario antes de ejecutar.

---

## FASE 1: IDENTIFICACIÓN

### Buscar todos los partners del contacto

```sql
SELECT
    p.id AS partner_id, p.name, p.email, p.phone, p.mobile, p.active, p.create_date,
    (SELECT COUNT(*) FROM res_users u WHERE u.partner_id = p.id AND u.active = true) AS usuarios_activos,
    (SELECT COUNT(*) FROM op_student s WHERE s.partner_id = p.id AND s.active = true) AS estudiantes_activos,
    (SELECT COUNT(*) FROM op_admission a WHERE a.partner_id = p.id AND a.state = 'done') AS admisiones_done,
    (SELECT COUNT(*) FROM account_move am WHERE am.partner_id = p.id) AS facturas,
    (SELECT COUNT(*) FROM sale_order so WHERE so.partner_id = p.id) AS ordenes_venta
FROM res_partner p
WHERE LOWER(p.name) LIKE '%nombre%apellido%'
   OR LOWER(p.email) LIKE '%email@ejemplo.com%'
   OR p.mobile LIKE '%telefono%'
ORDER BY p.active DESC, p.create_date ASC;
```

### Determinar partner principal (prioridad)

| Prioridad | Criterio |
|-----------|----------|
| 1 | Tiene usuario activo en `res_users` |
| 2 | Tiene estudiante activo en `op_student` |
| 3 | Tiene admisiones con `state='done'` en `op_admission` |
| 4 | Es el registro más antiguo |
| 5 | Tiene más datos asociados |

---

## FASE 2: CONSOLIDACIÓN DE DATOS

⚠️ **REGLA CRÍTICA DE ESTA FASE:** Mover **TODOS** los registros de **TODOS** los modelos listados abajo, sin excepción. No filtrar por estado, tipo ni fecha. Si un registro pertenece a un partner duplicado, se mueve al principal. El agente debe ejecutar los 6 pasos en orden y confirmar cuántos registros movió en cada uno.

---

### Paso 2.1 — Mover movimientos contables (account.move)

**IMPORTANTE:** Incluye absolutamente todos los `move_type`: `out_invoice`, `in_invoice`, `out_refund`, `in_refund`, `entry` (asientos de Stripe, PSTRIP, STRIP, etc.). **No filtrar por tipo ni por estado (posted, draft, cancel).**

```python
# Mover TODOS los account.move — sin filtro de tipo ni estado
moves = models.execute_kw(db, uid, pwd, 'account.move', 'search_read',
    [[['partner_id', 'in', ids_duplicados]]],
    {'fields': ['id', 'name', 'move_type', 'state']})
print(f"account.move a mover: {len(moves)} registros — tipos: {set(m['move_type'] for m in moves)}")
if moves:
    models.execute_kw(db, uid, pwd, 'account.move', 'write',
        [[m['id'] for m in moves], {'partner_id': partner_principal_id}])
    print(f"✓ {len(moves)} movimientos contables movidos al partner {partner_principal_id}")
```

### Paso 2.2 — Mover líneas de movimientos contables (account.move.line)

```python
move_lines = models.execute_kw(db, uid, pwd, 'account.move.line', 'search_read',
    [[['partner_id', 'in', ids_duplicados]]],
    {'fields': ['id']})
if move_lines:
    models.execute_kw(db, uid, pwd, 'account.move.line', 'write',
        [[l['id'] for l in move_lines], {'partner_id': partner_principal_id}])
    print(f"✓ {len(move_lines)} líneas contables movidas")
```

### Paso 2.3 — Mover órdenes de venta y suscripciones (sale.order)

**IMPORTANTE:** Incluye **todas** las órdenes sin importar estado (`draft`, `sent`, `sale`, `done`, `cancel`) y sin importar si son suscripciones (`is_subscription=true`) o no. Las suscripciones activas en estado `sale` deben moverse igual que cualquier otra orden.

```python
# Mover TODAS las sale.order — sin filtro de estado ni tipo
ordenes = models.execute_kw(db, uid, pwd, 'sale.order', 'search_read',
    [[['partner_id', 'in', ids_duplicados]]],
    {'fields': ['id', 'name', 'state', 'is_subscription']})
print(f"sale.order a mover: {len(ordenes)} — suscripciones: {sum(1 for o in ordenes if o.get('is_subscription'))}")
if ordenes:
    models.execute_kw(db, uid, pwd, 'sale.order', 'write',
        [[o['id'] for o in ordenes], {'partner_id': partner_principal_id}])
    print(f"✓ {len(ordenes)} órdenes/suscripciones movidas")

# Mover también las líneas de orden
order_lines = models.execute_kw(db, uid, pwd, 'sale.order.line', 'search_read',
    [[['order_partner_id', 'in', ids_duplicados]]],
    {'fields': ['id']})
if order_lines:
    models.execute_kw(db, uid, pwd, 'sale.order.line', 'write',
        [[l['id'] for l in order_lines], {'order_partner_id': partner_principal_id}])
    print(f"✓ {len(order_lines)} líneas de orden movidas")
```

### Paso 2.4 — Mover transacciones y tokens de pago

```python
# Transacciones de pago (Stripe, etc.)
transacciones = models.execute_kw(db, uid, pwd, 'payment.transaction', 'search_read',
    [[['partner_id', 'in', ids_duplicados]]],
    {'fields': ['id', 'reference']})
if transacciones:
    models.execute_kw(db, uid, pwd, 'payment.transaction', 'write',
        [[t['id'] for t in transacciones], {'partner_id': partner_principal_id}])
    print(f"✓ {len(transacciones)} transacciones de pago movidas")

# Tokens de pago (tarjetas guardadas) — verificar conflicto de provider_ref primero
tokens_dup = models.execute_kw(db, uid, pwd, 'payment.token', 'search_read',
    [[['partner_id', 'in', ids_duplicados]]],
    {'fields': ['id', 'provider_ref']})
tokens_principal = models.execute_kw(db, uid, pwd, 'payment.token', 'search_read',
    [[['partner_id', '=', partner_principal_id]]],
    {'fields': ['provider_ref']})
refs_existentes = {t['provider_ref'] for t in tokens_principal}
tokens_a_mover = [t for t in tokens_dup if t['provider_ref'] not in refs_existentes]
if tokens_a_mover:
    models.execute_kw(db, uid, pwd, 'payment.token', 'write',
        [[t['id'] for t in tokens_a_mover], {'partner_id': partner_principal_id}])
    print(f"✓ {len(tokens_a_mover)} tokens de pago movidos")
```

### Paso 2.5 — Mover CRM leads y admisiones

```python
# CRM leads
leads = models.execute_kw(db, uid, pwd, 'crm.lead', 'search_read',
    [[['partner_id', 'in', ids_duplicados]]], {'fields': ['id', 'name']})
if leads:
    models.execute_kw(db, uid, pwd, 'crm.lead', 'write',
        [[l['id'] for l in leads], {'partner_id': partner_principal_id}])
    print(f"✓ {len(leads)} leads CRM movidos")

# Admisiones (op.admission)
admisiones = models.execute_kw(db, uid, pwd, 'op.admission', 'search_read',
    [[['partner_id', 'in', ids_duplicados]]], {'fields': ['id', 'state']})
if admisiones:
    models.execute_kw(db, uid, pwd, 'op.admission', 'write',
        [[a['id'] for a in admisiones], {'partner_id': partner_principal_id}])
    print(f"✓ {len(admisiones)} admisiones movidas")
```

### Paso 2.6 — Consolidar cursos del estudiante (op.student.course)

Solo aplica si hay estudiantes en los duplicados:

```python
cursos_dup = models.execute_kw(db, uid, pwd, 'op.student.course', 'search_read',
    [[['student_id', 'in', ids_estudiantes_duplicados]]], {'fields': ['id', 'course_id']})
cursos_principal = models.execute_kw(db, uid, pwd, 'op.student.course', 'search_read',
    [[['student_id', '=', student_principal_id]]], {'fields': ['course_id']})
course_ids_principal = {c['course_id'][0] for c in cursos_principal}
ids_a_mover = [c['id'] for c in cursos_dup if c['course_id'][0] not in course_ids_principal]
if ids_a_mover:
    models.execute_kw(db, uid, pwd, 'op.student.course', 'write',
        [ids_a_mover, {'student_id': student_principal_id}])
    print(f"✓ {len(ids_a_mover)} programas académicos movidos")
```

---

## FASE 3: UNIFICACIÓN DE USUARIOS

⚠️ **ADVERTENCIA CRÍTICA — USUARIOS INTERNOS:** Antes de reasignar cualquier usuario de un partner duplicado, verificar si es usuario interno (`share=False`) o portal (`share=True`). **Nunca reasignar un usuario interno al partner de un estudiante** — esto le daría permisos administrativos incorrectos. Los usuarios internos de los duplicados deben desactivarse, no fusionarse.

```python
# Paso 3.1 — Clasificar usuarios de los duplicados
GRUPOS_PORTAL = [10, 25, 37, 137]  # Portal, B2B, Multisitio, Objetivos

todos_usuarios_dup = models.execute_kw(db, uid, pwd, 'res.users', 'search_read',
    [[['partner_id', 'in', ids_duplicados], ['id', '>', 3]]],
    {'fields': ['id', 'login', 'active', 'share']})

usuarios_portal_dup  = [u for u in todos_usuarios_dup if u['share'] == True]
usuarios_internos_dup = [u for u in todos_usuarios_dup if u['share'] == False]

print(f"Usuarios portal en duplicados: {len(usuarios_portal_dup)}")
print(f"Usuarios internos en duplicados: {len(usuarios_internos_dup)} — NO reasignar, desactivar")

# Paso 3.2 — Usuarios internos de duplicados: desactivar directamente (NO mover al principal)
if usuarios_internos_dup:
    models.execute_kw(db, uid, pwd, 'res.users', 'write',
        [[u['id'] for u in usuarios_internos_dup], {'active': False}])
    print(f"✓ {len(usuarios_internos_dup)} usuarios internos desactivados (no fusionados)")

# Paso 3.3 — Usuarios portal de duplicados: reasignar al partner principal
if usuarios_portal_dup:
    models.execute_kw(db, uid, pwd, 'res.users', 'write',
        [[u['id'] for u in usuarios_portal_dup], {'partner_id': partner_principal_id}])
    print(f"✓ {len(usuarios_portal_dup)} usuarios portal reasignados al partner principal")

# Paso 3.4 — Identificar y conservar el único usuario activo correcto en el principal
todos_usuarios_principal = models.execute_kw(db, uid, pwd, 'res.users', 'search_read',
    [[['partner_id', '=', partner_principal_id], ['id', '>', 3]]],
    {'fields': ['id', 'login', 'active', 'share']})

partner_email = models.execute_kw(db, uid, pwd, 'res.partner', 'read',
    [[partner_principal_id]], {'fields': ['email']})[0]['email']

# El usuario correcto: portal (share=True) con login = email del partner
usuario_principal = next(
    (u for u in todos_usuarios_principal if u['share'] == True and u['login'] == partner_email),
    next((u for u in todos_usuarios_principal if u['share'] == True), None)
)

if not usuario_principal:
    print("⚠️ No hay usuario portal activo en el principal — verificar manualmente")
else:
    print(f"✓ Usuario principal: ID {usuario_principal['id']} ({usuario_principal['login']}) share={usuario_principal['share']}")

    # Paso 3.5 — Desactivar cualquier otro usuario activo en el principal
    secundarios = [u['id'] for u in todos_usuarios_principal
                   if u['id'] != usuario_principal['id'] and u['active']]
    if secundarios:
        models.execute_kw(db, uid, pwd, 'res.users', 'write',
            [secundarios, {'active': False}])
        print(f"✓ {len(secundarios)} usuarios secundarios desactivados")

    # Paso 3.6 — Asegurar que los grupos del usuario principal son solo los del portal
    # Nunca heredar grupos de usuarios internos fusionados
    models.execute_kw(db, uid, pwd, 'res.users', 'write',
        [[usuario_principal['id']], {'groups_id': [(6, 0, GRUPOS_PORTAL)]}])
    print(f"✓ Grupos del usuario principal normalizados a portal: {GRUPOS_PORTAL}")

    # Paso 3.7 — Vincular estudiante al usuario correcto
    models.execute_kw(db, uid, pwd, 'op.student', 'write',
        [[student_principal_id], {'user_id': usuario_principal['id']}])
    print(f"✓ Estudiante {student_principal_id} vinculado al usuario {usuario_principal['id']}")
```

---

## FASE 4: ARCHIVAR DUPLICADOS

⚠️ **ESTA FASE ES OBLIGATORIA.** La fusión no está completa hasta que los partners duplicados estén archivados. Ejecutar siempre, sin excepción, después de mover todos los datos.

```python
# 1. Archivar estudiantes vinculados a los partners duplicados
estudiantes_dup = models.execute_kw(db, uid, pwd, 'op.student', 'search_read',
    [[['partner_id', 'in', ids_duplicados], ['id', '!=', student_principal_id]]],
    {'fields': ['id']})
if estudiantes_dup:
    models.execute_kw(db, uid, pwd, 'op.student', 'write',
        [[e['id'] for e in estudiantes_dup], {'active': False}])
    print(f"✓ {len(estudiantes_dup)} estudiantes duplicados archivados")

# 2. Archivar los partners duplicados (OBLIGATORIO — sin este paso la fusión está incompleta)
models.execute_kw(db, uid, pwd, 'res.partner', 'write',
    [ids_duplicados, {'active': False}])
print(f"✓ Partners duplicados archivados: {ids_duplicados}")

# 3. Confirmar que solo queda 1 partner activo
activos = models.execute_kw(db, uid, pwd, 'res.partner', 'search_read',
    [[['id', 'in', [partner_principal_id] + ids_duplicados], ['active', '=', True]]],
    {'fields': ['id', 'name']})
print(f"Partners activos restantes: {len(activos)} — esperado: 1")
if len(activos) != 1:
    print("⚠️ ADVERTENCIA: quedan más de 1 partner activo, verificar manualmente")
```

---

## FASE 5: INVALIDAR CACHÉS

```python
# Tocar el partner principal para forzar recarga en Odoo
partner_data = models.execute_kw(db, uid, pwd, 'res.partner', 'read',
    [[partner_principal_id]], {'fields': ['comment']})[0]
models.execute_kw(db, uid, pwd, 'res.partner', 'write',
    [[partner_principal_id], {'comment': partner_data.get('comment') or False}])
```

---

## FASE 6: VERIFICACIÓN FINAL

Ejecutar estas queries en la réplica para confirmar que **todo** fue consolidado. Si algún resultado no es el esperado, volver a la fase correspondiente.

```sql
-- 1. Cero registros financieros en los duplicados (debe retornar 0 en todas las columnas)
SELECT
    (SELECT COUNT(*) FROM account_move WHERE partner_id IN ([ids_duplicados])) AS moves_pendientes,
    (SELECT COUNT(*) FROM sale_order WHERE partner_id IN ([ids_duplicados])) AS ordenes_pendientes,
    (SELECT COUNT(*) FROM payment_transaction WHERE partner_id IN ([ids_duplicados])) AS transacciones_pendientes,
    (SELECT COUNT(*) FROM crm_lead WHERE partner_id IN ([ids_duplicados])) AS leads_pendientes;
-- Esperado: 0 | 0 | 0 | 0

-- 2. Solo 1 partner activo
SELECT id, name, active FROM res_partner
WHERE id IN ([partner_principal_id], [ids_duplicados]);
-- Esperado: principal active=true, duplicados active=false

-- 3. Solo 1 usuario activo, tipo portal (share=true), con exactamente 4 grupos
SELECT u.id, u.login, u.active, u.share,
    (SELECT COUNT(*) FROM res_groups_users_rel WHERE uid = u.id) AS total_grupos
FROM res_users u
WHERE u.partner_id = [partner_principal_id] AND u.id > 3
ORDER BY u.active DESC;
-- Esperado: 1 activo, share=true, total_grupos=4, login=email del partner

-- 4. Estudiante principal con todos los datos consolidados
SELECT
    s.id, s.user_id,
    (SELECT COUNT(*) FROM op_student_course WHERE student_id = s.id) AS programas,
    (SELECT COUNT(*) FROM op_admission WHERE partner_id = s.partner_id AND state = 'done') AS admisiones_done,
    (SELECT COUNT(*) FROM account_move WHERE partner_id = s.partner_id) AS facturas_totales,
    (SELECT COUNT(*) FROM sale_order WHERE partner_id = s.partner_id) AS ordenes_totales
FROM op_student s WHERE s.id = [student_principal_id];
```

---

## NOTA EN CHATTER (OBLIGATORIA)

```python
models.execute_kw(db, uid, pwd, 'project.task', 'message_post',
    [[task_id]], {
        'body': f'''<p><strong>Fusión de contactos duplicados ejecutada por IA:</strong></p>
        <ul>
        <li>Partner principal conservado: ID {partner_principal_id}</li>
        <li>Partners archivados: {ids_duplicados}</li>
        <li>Datos consolidados: facturas, órdenes, admisiones, programas</li>
        <li>Usuario activo único: ID {usuario_principal["id"]} ({partner_email})</li>
        </ul>
        <p>Solicitar al estudiante que cierre sesión, limpie caché y vuelva a ingresar.</p>''',
        'message_type': 'comment',
        'subtype_xmlid': 'mail.mt_note'
    })
```

---

## Instrucciones post-fusión para el estudiante

1. Cerrar sesión completamente del portal
2. Limpiar caché del navegador: `Ctrl + Shift + Del` → "Imágenes y archivos en caché"
3. Cerrar el navegador completamente
4. Abrir navegador e iniciar sesión en `https://app.universidadisep.com`
5. Verificar que aparezcan todos los programas académicos y datos consolidados

---

## Escenarios especiales

### Partner principal sin admisiones

Si tras la fusión el portal no muestra programas (sin `op_admission` con `state='done'`), crear admisiones desde `op_student_course` via RPC usando `op.admission` `create`. Consultar al usuario antes de ejecutar esta operación.

### Tokens de pago (Stripe) en duplicados

Verificar primero que no haya conflicto de `provider_ref` antes de mover `payment.token`. Si hay conflicto, informar al usuario.
