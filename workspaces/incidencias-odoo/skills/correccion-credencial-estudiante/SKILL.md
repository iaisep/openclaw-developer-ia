---
name: correccion-credencial-estudiante
description: Corrección de credencial digital de estudiante que muestra un programa académico incorrecto. Usar cuando un ticket reporta que la credencial muestra el programa equivocado, un programa antiguo, o hay discrepancia entre op_admission y op_student_course.
---

# SKILL: Corrección de Credenciales de Estudiante con Programa Incorrecto

**Última actualización:** 2026-03-10
**Nivel de riesgo:** 🟡 MEDIO (requiere acceso directo a base de datos)

---

## Descripción del Problema

Cuando un estudiante reporta que su **credencial digital** muestra un programa académico incorrecto (generalmente un programa antiguo que ya no está cursando), el problema se debe a una discrepancia entre:

- **`op_admission`**: Tabla que alimenta el portal y la información principal
- **`op_student_course`**: Tabla de registros internos de programas del estudiante

El template `campus_certificate_template.xml` del módulo `student_digital_wallet` toma el **primer registro** de `op_student_course` (ordenado por ID) sin filtrar por estado, lo que puede causar que muestre un programa antiguo en lugar del actual.

---

## Cómo ejecutar las queries

Las queries SQL se ejecutan via SSH a la réplica espejo para diagnóstico y via SSH al servidor DEV para escritura:

```bash
# LECTURA (réplica espejo .57)
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "docker exec postgres-replica-i4s8o8000kc040cgwcwowwwc psql -U odoo -d UisepFinal -c '<QUERY>'"

# ESCRITURA (producción via RPC — ver TOOLS.md)
# Las modificaciones en DB de producción se hacen via xmlrpc contra app.universidadisep.com
# NO hay acceso SSH directo a producción desde el agente
```

**IMPORTANTE:** Este skill usa SQL solo para DIAGNÓSTICO desde la réplica. Las modificaciones (UPDATE, DELETE) se aplican via **Odoo XML-RPC** en producción, no con SQL directo.

---

## CRITERIOS DE APLICACIÓN

### CUÁNDO SÍ APLICAR

1. El estudiante **NO culminó formalmente** el programa antiguo (cambio de programa, deserción, transferencia)
2. El programa registrado **NO corresponde** al programa actual del estudiante
3. El registro del programa antiguo **NO tiene dependencias activas** (sin materias cursadas, sin tesis, sin prácticas)
4. El estudiante **NO está en doble titulación** legítima

### CUÁNDO NO APLICAR

1. El estudiante obtuvo título/certificado del programa → usar `state='finished'` en lugar de eliminar
2. Estudiante en doble titulación legítima → coordinar con área académica
3. El programa tiene materias cursadas y aprobadas → `state='finished'` y documentar
4. Registros con tesis, prácticas o proyectos asociados

---

## PASO 1: DIAGNÓSTICO (queries en réplica)

### Identificar al estudiante

```sql
SELECT s.id as student_id, s.partner_id, s.user_id, p.name, p.email
FROM op_student s
JOIN res_partner p ON p.id = s.partner_id
WHERE LOWER(p.name) LIKE '%nombre%estudiante%'
  OR LOWER(p.email) LIKE '%email@estudiante.com%'
AND s.active = true;
```

### Verificar programas en op_student_course

```sql
SELECT sc.id, c.name as programa, sc.state, sc.create_date, sc.course_id
FROM op_student_course sc
JOIN op_course c ON c.id = sc.course_id
WHERE sc.student_id = [student_id]
ORDER BY sc.id;
```

### Verificar admisiones en op_admission

```sql
SELECT a.id, c.name as programa, a.state, a.application_number, a.application_date
FROM op_admission a
JOIN op_course c ON c.id = a.course_id
WHERE a.partner_id = [partner_id]
ORDER BY a.application_date DESC;
```

### Determinar escenario

| Escenario | Descripción | Solución |
|-----------|-------------|----------|
| **A** | Admisión incorrecta + Registro incorrecto en `op_student_course` | Cancelar admisión + Eliminar registro |
| **B** | Solo registro incorrecto en `op_student_course` | Solo eliminar registro |
| **C** | Programa completado con materias | Cambiar a `state='finished'` (NO eliminar) |
| **D** | Doble titulación legítima | Coordinar con académica (NO modificar) |

---

## PASO 2: VERIFICACIÓN DE SEGURIDAD (OBLIGATORIA antes de cualquier modificación)

```sql
SELECT
    (SELECT COUNT(*) FROM op_section_op_student_course_rel
     WHERE op_student_course_id = [id_registro_incorrecto]) as secciones,
    (SELECT COUNT(*) FROM op_student_course_op_subject_rel
     WHERE op_student_course_id = [id_registro_incorrecto]) as materias,
    (SELECT COUNT(*) FROM practice_questionnaire
     WHERE op_student_course_course_id = [id_registro_incorrecto]) as cuestionarios,
    (SELECT COUNT(*) FROM practice_request
     WHERE course_id = [id_registro_incorrecto]) as practice_requests,
    (SELECT COUNT(*) FROM tesis_model
     WHERE course_id = [id_registro_incorrecto]) as tesis,
    (SELECT COUNT(*) FROM mail_message
     WHERE model = 'op.student.course' AND res_id = [id_registro_incorrecto]) as mensajes;
```

**Resultado esperado para proceder:** todos los contadores = 0.
**Si algún contador > 0: NO modificar.** Registrar en chatter y mover a "En Revisión" (567).

Verificar también estado de admisión del programa incorrecto:
```sql
SELECT id, state FROM op_admission
WHERE partner_id = [partner_id] AND course_id = [course_id_incorrecto];
```
- `state='cancel'` o NULL → seguro proceder
- `state='done'` o `'confirm'` → revisar con académica antes de modificar

---

## PASO 3: CORRECCIÓN VIA RPC

Las modificaciones se aplican en Odoo producción via XML-RPC (ver TOOLS.md para credenciales).

### Escenario A: Cancelar admisión + eliminar registro

```python
# 1. Cancelar admisión incorrecta
models.execute_kw(db, uid, pwd, 'op.admission', 'write',
    [[admission_id_incorrecto], {'state': 'cancel'}])

# 2. Eliminar registro de op_student_course (solo si verificación pasó)
models.execute_kw(db, uid, pwd, 'op.student.course', 'unlink',
    [[id_registro_incorrecto]])

# 3. Invalidar caché tocando el partner
models.execute_kw(db, uid, pwd, 'res.partner', 'write',
    [[partner_id], {'comment': False}])  # touch sin cambio real
```

### Escenario B: Solo eliminar registro

```python
models.execute_kw(db, uid, pwd, 'op.student.course', 'unlink',
    [[id_registro_incorrecto]])
```

### Escenario C: Cambiar a finished (NO eliminar)

```python
models.execute_kw(db, uid, pwd, 'op.student.course', 'write',
    [[id_registro_incorrecto], {'state': 'finished'}])
```

---

## PASO 4: NOTA EN CHATTER (OBLIGATORIA)

```python
models.execute_kw(db, uid, pwd, 'project.task', 'message_post',
    [[task_id]], {
        'body': f'''<p><strong>Corrección de credencial ejecutada por IA:</strong></p>
        <ul>
        <li>Estudiante: {nombre} (ID: {student_id})</li>
        <li>Programa incorrecto: {programa_incorrecto}</li>
        <li>Programa correcto: {programa_correcto}</li>
        <li>Escenario aplicado: {escenario}</li>
        <li>Acción: {accion_tomada}</li>
        </ul>
        <p>Indicar al estudiante que cierre sesión y limpie caché del navegador.</p>''',
        'message_type': 'comment',
        'subtype_xmlid': 'mail.mt_note'
    })
```

---

## PASO 5: INSTRUCCIONES PARA EL ESTUDIANTE

Registrar en el chatter del ticket y en la nota de resolución:

1. Cerrar sesión del portal de Odoo completamente
2. Limpiar caché del navegador: `Ctrl + Shift + Del` → "Imágenes y archivos en caché"
3. Cerrar el navegador completamente (todas las ventanas)
4. Abrir navegador nuevamente e iniciar sesión en `https://app.universidadisep.com`
5. Verificar que la credencial muestra el programa correcto

---

## PASO 6: VERIFICACIÓN POST-CORRECCIÓN (réplica)

```sql
-- Solo debe haber 1 admisión con state='done' (la correcta)
SELECT a.id, c.name as programa, a.state
FROM op_admission a
JOIN op_course c ON c.id = a.course_id
WHERE a.partner_id = [partner_id] AND a.state = 'done';

-- El programa correcto debe ser el primero por ID
SELECT sc.id, c.name as programa, sc.state
FROM op_student_course sc
JOIN op_course c ON c.id = sc.course_id
WHERE sc.student_id = [student_id]
ORDER BY sc.id;
```

---

## Solución permanente (escalar a dev-odoo-github)

Si el problema se repite frecuentemente, escalar a stage 703 con nota técnica:

> **Archivo:** `addons_uisep/student_digital_wallet/views/campus_certificate_template.xml`
> **Fix:** Cambiar `student.course_detail_ids[0]` por `.filtered(lambda c: c.state == 'running')[0]`
> **Rama:** DEVMain_Latest → Jenkins → DEV → main → PROD
