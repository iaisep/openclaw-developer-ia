#!/usr/bin/env python3
import xmlrpc.client, ssl, re, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

url = 'https://app.universidadisep.com'
db = 'UisepFinal'
uid = 5064
pwd = '${ODOO_RPC_PASSWORD}'
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', context=ssl.create_default_context())

task_id = 1287

# 1. Cambiar stage a En Proceso (644)
models.execute_kw(db, uid, pwd, 'project.task', 'write', [[task_id], {'stage_id': 644}])
print("Stage -> En Proceso (644)")

# 2. Nota en chatter
models.execute_kw(db, uid, pwd, 'project.task', 'message_post', [[task_id]], {
    'body': '<p><b>Análisis (IA):</b> El ticket reporta spam excesivo a alumnos. La descripción sugiere revisar flujos de n8n para identificar bucles o envíos duplicados.<br/><b>Acción:</b> Este es un problema de lógica de automatizaciones que requiere revisión código/desarrollo. Se escala a "Enviado a Proyecto".</p>',
    'message_type': 'comment',
    'subtype_xmlid': 'mail.mt_note'
})
print("Nota registrada en chatter")

# 3. Cambiar a Enviado a Proyecto (703)
models.execute_kw(db, uid, pwd, 'project.task', 'write', [[task_id], {'stage_id': 703}])
print("Stage -> Enviado a Proyecto (703)")

# 4. Buscar email del solicitante
task = models.execute_kw(db, uid, pwd, 'project.task', 'search_read', [[['id','=',task_id]]], {'fields': ['description'], 'limit': 1})
desc = task[0]['description'] if task else ''
emails = re.findall(r'[a-zA-Z0-9._%+\-]+@universidadisep\.com', desc)
email_usuario = emails[0] if emails else None
print(f"Email solicitante: {email_usuario}")

# 5. Enviar correo
if email_usuario:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Actualización de tu incidencia — #{task_id}"
    msg["From"] = "mguzman@universidadisep.com"
    msg["To"] = email_usuario
    msg["Cc"] = "iallamadas@universidadisep.com"
    cuerpo = f"""<html><body>
<p>Tu incidencia #{task_id} ha sido procesada.</p>
<p><b>Estado:</b> Enviado a Proyecto<br/>
<b>Motivo:</b> El problema reportado (spam excesivo por flujos automatizados) requiere revisión de código y flujos n8n. Se ha escalado al equipo de desarrollo.</p>
<p>Te notifyaremos cuando esté resuelto.</p>
</body></html>"""
    msg.attach(MIMEText(cuerpo, "html"))
    with smtplib.SMTP("email-smtp.us-east-1.amazonaws.com", 587) as s:
        s.starttls()
        s.login("AKIA5TSAYHSG3OD7XYK3", "BPMhIBG4+f4qfob+msLNNH9pYBlB74ERNi/cKXL1N+WI")
        s.sendmail("mguzman@universidadisep.com", [email_usuario, "iallamadas@universidadisep.com"], msg.as_string())
    print(f"Correo enviado a {email_usuario}")
else:
    print("No se encontró email - correo no enviado")