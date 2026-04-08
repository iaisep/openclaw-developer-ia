---
name: notificacion-incidencia
description: Enviar notificación por correo al usuario que abrió una incidencia cuando su ticket cambia de estado. Usar en cada transición de stage: al tomar la incidencia (En Proceso), al resolverla (Listo), al escalarla (Enviado a Proyecto) o al enviarla a revisión (En Revisión).
---

# SKILL: Notificación de Incidencia por Email

Notifica al usuario que reportó la incidencia cada vez que el ticket cambia de estado.

---

## Configuración AWS SES

```
SMTP_HOST = email-smtp.us-east-1.amazonaws.com
SMTP_PORT = 587
SMTP_USER = ${AWS_SES_USER}
SMTP_PASS = ${AWS_SES_PASSWORD}
FROM      = mguzman@universidadisep.com
```

---

## Cómo extraer el correo del solicitante desde la descripción

La descripción siempre contiene el email del **solicitante interno** (dominio `@universidadisep.com`). Ese es el único destinatario de la notificación — el email del alumno NO se usa para enviar correos.

```python
import re

def extraer_email_solicitante(descripcion):
    """Busca el email @universidadisep.com en la descripción del ticket (solicitante interno)."""
    patron = r'[a-zA-Z0-9._%+\-]+@universidadisep\.com'
    emails = re.findall(patron, descripcion or '')
    return emails[0] if emails else None
```

Si no se encuentra email `@universidadisep.com` en la descripción, registrar en chatter y **no enviar** (no abortar la resolución del ticket).

---

## Función de envío

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

CC_FIJO = "iallamadas@universidadisep.com"

def notificar_usuario(to_email, asunto, cuerpo_html):
    """Envía notificación via AWS SES SMTP. CC fijo a iallamadas@universidadisep.com."""
    if not to_email:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = "mguzman@universidadisep.com"
    msg["To"] = to_email
    msg["Cc"] = CC_FIJO

    msg.attach(MIMEText(cuerpo_html, "html"))

    destinatarios = [to_email, CC_FIJO]

    try:
        with smtplib.SMTP("email-smtp.us-east-1.amazonaws.com", 587) as server:
            server.starttls()
            server.login(
                "${AWS_SES_USER}",
                "${AWS_SES_PASSWORD}"
            )
            server.sendmail("mguzman@universidadisep.com", destinatarios, msg.as_string())
        return True
    except Exception as e:
        # No abortar el flujo del ticket si el email falla
        return False
```

---

## Plantillas por stage

### Al tomar la incidencia → En Proceso (644)

```python
asunto = f"Tu incidencia está siendo atendida — #{task_id}"
cuerpo = f"""
<p>Hola,</p>
<p>Tu incidencia <strong>"{task_name}"</strong> ha sido recibida y está siendo atendida.</p>
<p>Te notificaremos cuando tengamos una resolución.</p>
<br>
<p>— Soporte Técnico UISEP</p>
"""
```

### Al resolver → Listo (565)

```python
asunto = f"Tu incidencia ha sido resuelta — #{task_id}"
cuerpo = f"""
<p>Hola,</p>
<p>Tu incidencia <strong>"{task_name}"</strong> ha sido resuelta.</p>
<p><strong>Acción tomada:</strong> {resumen_accion}</p>
<p>Si el problema persiste, abre una nueva incidencia en el portal.</p>
<br>
<p>— Soporte Técnico UISEP</p>
"""
```

### Al escalar a desarrollo → Enviado a Proyecto (703)

```python
asunto = f"Tu incidencia requiere desarrollo — #{task_id}"
cuerpo = f"""
<p>Hola,</p>
<p>Tu incidencia <strong>"{task_name}"</strong> ha sido analizada y requiere desarrollo de código para resolverse.</p>
<p>Ha sido enviada al equipo de desarrollo. Te contactaremos cuando esté lista.</p>
<br>
<p>— Soporte Técnico UISEP</p>
"""
```

### Al enviar a revisión → En Revisión (567)

```python
asunto = f"Tu incidencia está en revisión — #{task_id}"
cuerpo = f"""
<p>Hola,</p>
<p>Tu incidencia <strong>"{task_name}"</strong> requiere revisión adicional por parte del equipo académico o técnico.</p>
<p>Te contactaremos a la brevedad.</p>
<br>
<p>— Soporte Técnico UISEP</p>
"""
```

---

## Flujo de uso dentro del agente

Invocar `notificar_usuario` **después** de cambiar el stage en Odoo y **antes** de registrar la nota en chatter:

```python
# 1. Extraer email del solicitante interno (@universidadisep.com) desde la descripción
email_usuario = extraer_email_solicitante(task_description)

# 2. Cambiar stage via RPC (según corresponda)
models.execute_kw(db, uid, pwd, 'project.task', 'write',
    [[task_id], {'stage_id': stage_destino}])

# 3. Enviar notificación
enviado = notificar_usuario(email_usuario, asunto, cuerpo)

# 4. Registrar en chatter (incluir si el email fue enviado o no)
nota_email = f"Notificación enviada a {email_usuario}." if enviado else \
             f"No se encontró email en la descripción — notificación no enviada."

models.execute_kw(db, uid, pwd, 'project.task', 'message_post',
    [[task_id]], {
        'body': f'<p>{accion_tomada}</p><p><em>{nota_email}</em></p>',
        'message_type': 'comment',
        'subtype_xmlid': 'mail.mt_note'
    })
```

---

## Reglas

- **Nunca abortar** la resolución del ticket si el email falla — el email es secundario.
- **Solo notificar** en cambios de stage relevantes: En Proceso, Listo, Enviado a Proyecto, En Revisión.
- **No notificar** al cancelar (stage 643) ni al volver a Pendiente.
- Remitente siempre: `mguzman@universidadisep.com`
