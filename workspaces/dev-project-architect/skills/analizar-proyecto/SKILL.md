---
name: analizar-proyecto
description: Analiza un proyecto recién creado, determina la herramienta tecnológica óptima del stack (n8n, odoo, chatwoot, mautic, wordpress, desarrollos-apis), asigna la etiqueta correspondiente y deja justificación técnica en el chatter. Considera siempre las limitaciones estructurales de Odoo 16.
---

# SKILL: Analizar Proyecto y Asignar Herramienta

---

## Script Python completo (ejecutable)

```python
#!/usr/bin/env python3
"""
analizar_proyecto.py — Dev Project Architect
Analiza un proyecto y asigna la etiqueta de herramienta más adecuada.
Uso: python3 analizar_proyecto.py <project_id>
     python3 analizar_proyecto.py  (analiza todos los pendientes)
"""
import xmlrpc.client, ssl, sys, os, smtplib, re
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── Conexión ──────────────────────────────────────────────────────────────────
ODOO_URL  = "https://app.universidadisep.com"
ODOO_DB   = "UisepFinal"
ODOO_UID  = 5064
ODOO_PASS = "${ODOO_RPC_PASSWORD}"

SMTP_HOST = "email-smtp.us-east-1.amazonaws.com"
SMTP_PORT = 587
SMTP_USER = "${AWS_SES_USER}"
SMTP_PASS = "${AWS_SES_PASSWORD}"
FROM_EMAIL = "mguzman@universidadisep.com"
RECIPIENTS = [
    "iallamadas@universidadisep.com",
    "automatizacion02@universidadisep.com",
    "automatizacion03@universidadisep.com",
    "automatizacion04@universidadisep.com",
    "automatizacion05@universidadisep.com",
    "automatizacion06@universidadisep.com",
    "automatizacion07@universidadisep.com",
    "automatizacion08@universidadisep.com",
    "automatizacion09@universidadisep.com",
]

# IDs de etiquetas de herramienta
TOOL_TAGS = {
    'n8n':              24,
    'odoo':             25,
    'chatwoot':         26,
    'mautic':           27,
    'wordpress':        28,
    'desarrollos-apis': 29,
}
TOOL_TAG_IDS = set(TOOL_TAGS.values())

TOOL_EMOJIS = {
    'n8n': '🔄', 'odoo': '🟣', 'chatwoot': '💬',
    'mautic': '📧', 'wordpress': '🌐', 'desarrollos-apis': '🔌',
}

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
MEMORY_PATH  = os.path.join(SCRIPT_DIR, '..', '..', 'memory', 'analisis.md')
LOG_PATH     = os.path.join(SCRIPT_DIR, '..', '..', 'memory', 'analisis.log')

# ── Limitaciones Odoo 16 (texto para chatter) ─────────────────────────────────
ODOO_WARNINGS = (
    "Odoo 16 presenta: OOM Kill por alta presión de memoria, workers idle bloqueados sin "
    "liberación, procesos en fallo ejecutándose recursivamente, sobrecarga por módulos "
    "slide/mail/livechat, y memoria compartida entre Postgres, Redis y Odoo sin aislamiento. "
    "Arquitectura monolítica: cualquier módulo nuevo degradaría el entorno completo."
)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, 'a') as f:
        f.write(line + '\n')


def get_models():
    ctx = ssl.create_default_context()
    return xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object', context=ctx)


def strip_html(html):
    """Elimina tags HTML para obtener texto plano."""
    return re.sub(r'<[^>]+>', ' ', html or '').strip()


def decidir_herramienta(nombre, desc_texto):
    """
    Reglas deterministas + heurística por palabras clave.
    Devuelve (herramienta, justificacion, nota_odoo).
    """
    texto = (nombre + ' ' + desc_texto).lower()

    # Señales fuertes por herramienta
    n8n_keywords = [
        'automatiz', 'sincroniz', 'integrac', 'flujo', 'webhook', 'trigger',
        'pipeline', 'cron', 'notificac', 'programad', 'n8n', 'schedule',
        'procesamiento', 'batch', 'masiv', 'importar', 'exportar', 'log',
        'monitoreo', 'analisis de log', 'análisis de log',
    ]
    odoo_keywords = [
        'formulario odoo', 'vista odoo', 'módulo odoo', 'modelo odoo',
        'campo odoo', 'reporte odoo', 'factura', 'inventario', 'venta',
        'compra', 'contabilidad', 'nómina', 'rh odoo', 'erp',
    ]
    chatwoot_keywords = [
        'chat', 'conversac', 'bandeja', 'whatsapp', 'soporte', 'atencion',
        'atención', 'ticket soporte', 'bot atencion', 'agente',
    ]
    mautic_keywords = [
        'campaña', 'email marketing', 'lead', 'embudo', 'nutricion',
        'nutrición', 'segmentac', 'scoring', 'marketing', 'captacion',
        'captación', 'mautic',
    ]
    wordpress_keywords = [
        'sitio web', 'landing', 'portal', 'wordpress', 'pagina web',
        'página web', 'blog', 'contenido público', 'formulario captacion',
    ]

    scores = {k: 0 for k in TOOL_TAGS}

    for kw in n8n_keywords:
        if kw in texto: scores['n8n'] += 2
    for kw in odoo_keywords:
        if kw in texto: scores['odoo'] += 1  # peso menor por limitaciones
    for kw in chatwoot_keywords:
        if kw in texto: scores['chatwoot'] += 2
    for kw in mautic_keywords:
        if kw in texto: scores['mautic'] += 2
    for kw in wordpress_keywords:
        if kw in texto: scores['wordpress'] += 2

    # Penalizar odoo si hay señales de automatización (mejor n8n)
    if scores['n8n'] > 0 and scores['odoo'] > 0:
        scores['odoo'] = max(0, scores['odoo'] - scores['n8n'])

    ganador = max(scores, key=lambda k: scores[k])
    max_score = scores[ganador]

    if max_score == 0:
        ganador = 'desarrollos-apis'

    # Construir justificación
    justificaciones = {
        'n8n': (
            "La descripción indica un flujo de automatización, sincronización o integración "
            "entre sistemas. n8n permite modelar este tipo de lógica como nodos visuales, "
            "con menor consumo de recursos que implementarlo dentro de Odoo y sin riesgo "
            "de afectar el rendimiento del ERP."
        ),
        'odoo': (
            "La funcionalidad descrita requiere acceso directo a modelos de datos de Odoo "
            "con transacciones ACID y no puede desacoplarse del ERP. Se asigna odoo como "
            "herramienta a pesar de las limitaciones conocidas, con la recomendación de "
            "minimizar el uso de módulos pesados y optimizar las queries."
        ),
        'chatwoot': (
            "La descripción involucra gestión de conversaciones, atención al cliente o "
            "canales de comunicación. Chatwoot es la herramienta especializada del stack "
            "para este tipo de interacciones, evitando sobrecargar Odoo con lógica de chat."
        ),
        'mautic': (
            "La descripción corresponde a automatizaciones de marketing, campañas de email, "
            "embudos de leads o segmentación de contactos. Mautic está diseñado para este "
            "dominio y libera a Odoo de lógica de marketing que no le corresponde."
        ),
        'wordpress': (
            "La descripción menciona contenido web, landing pages o portales públicos. "
            "WordPress es la herramienta adecuada para gestión de contenido y sitios, "
            "sin impactar los recursos del servidor Odoo."
        ),
        'desarrollos-apis': (
            "La descripción no encaja claramente en ninguna herramienta específica del stack, "
            "o requiere una integración personalizada. Se asigna como comodín para desarrollo "
            "de API o microservicio independiente que no agregue carga a Odoo."
        ),
    }

    nota_odoo_map = {
        'n8n': (
            "Se descartó implementar en Odoo porque: el flujo de automatización añadiría "
            "carga de CPU/memoria a workers ya presionados, y n8n puede ejecutar esta "
            "lógica de forma independiente sin riesgo de OOM Kill."
        ),
        'odoo': (
            f"⚠️ Se asignó Odoo por necesidad. Tener presente: {ODOO_WARNINGS} "
            "Se recomienda revisión de impacto antes de implementar."
        ),
        'chatwoot': (
            "Se descartó Odoo: implementar lógica de chat dentro del ERP añadiría "
            "dependencia del módulo im_livechat, conocido por su alto consumo de memoria."
        ),
        'mautic': (
            "Se descartó Odoo: la lógica de marketing masivo generaría colas de email "
            "que sobrecargarían el módulo mail de Odoo, con riesgo de workers bloqueados."
        ),
        'wordpress': (
            "Se descartó Odoo: gestionar contenido web dentro del ERP no es su dominio "
            "y añadiría módulos innecesarios que comparten la memoria del servidor."
        ),
        'desarrollos-apis': (
            "Se descartó Odoo como primera opción: una API independiente permite escalar "
            "sin afectar el entorno monolítico de Odoo. Si en el análisis se detecta "
            "necesidad de acceso al modelo de Odoo, reevaluar con equipo técnico."
        ),
    }

    return ganador, justificaciones[ganador], nota_odoo_map[ganador]


def analizar_proyecto(models, project_id):
    db, uid, pwd = ODOO_DB, ODOO_UID, ODOO_PASS

    # Leer proyecto
    proj = models.execute_kw(db, uid, pwd, 'project.project', 'read',
        [[project_id]], {'fields': ['id','name','description','tag_ids']})[0]
    nombre = proj['name']

    # Verificar que no tenga ya etiqueta de herramienta
    if TOOL_TAG_IDS.intersection(set(proj['tag_ids'])):
        log(f"  SKIP {project_id}: ya tiene etiqueta de herramienta")
        return None

    # Leer descripción de la tarea de análisis (contiene la descripción original)
    tarea = models.execute_kw(db, uid, pwd, 'project.task', 'search_read',
        [[['project_id','=',project_id],
          ['name','=','Análisis de requerimientos y alcance']]],
        {'fields': ['description']})
    desc_tarea = tarea[0].get('description','') if tarea else ''

    desc_completa = strip_html((proj.get('description') or '') + ' ' + (desc_tarea or ''))

    # Paso 2 — Notificar inicio
    models.execute_kw(db, uid, pwd, 'project.project', 'message_post',
        [[project_id]], {
            'body': (
                '<p>🏛️ <b>Dev Project Architect</b> — '
                'Iniciando análisis de herramienta tecnológica...</p>'
            ),
            'message_type': 'comment',
            'subtype_xmlid': 'mail.mt_note'
        })

    # Paso 3 — Decidir
    herramienta, justificacion, nota_odoo = decidir_herramienta(nombre, desc_completa)
    tag_id = TOOL_TAGS[herramienta]
    emoji  = TOOL_EMOJIS[herramienta]

    # Paso 4 — Asignar etiqueta
    models.execute_kw(db, uid, pwd, 'project.project', 'write',
        [[project_id], {'tag_ids': [(4, tag_id)]}])

    # Paso 5 — Documentar decisión en chatter
    models.execute_kw(db, uid, pwd, 'project.project', 'message_post',
        [[project_id]], {
            'body': (
                f'<p>{emoji} <b>Herramienta recomendada: {herramienta.upper()}</b></p>'
                f'<hr/>'
                f'<p><b>Justificación técnica:</b><br/>{justificacion}</p>'
                f'<br/>'
                f'<p><b>Consideraciones Odoo 16:</b><br/>'
                f'<em>{nota_odoo}</em></p>'
            ),
            'message_type': 'comment',
            'subtype_xmlid': 'mail.mt_note'
        })

    log(f"  ✅ '{nombre}' (ID:{project_id}) → {herramienta}")

    # Log en memory
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, 'a') as f:
        f.write(
            f"- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] "
            f"'{nombre}' (ID:{project_id}) → {herramienta} | "
            f"{justificacion[:100]}\n"
        )

    return {
        'project_id': project_id,
        'name': nombre,
        'herramienta': herramienta,
        'emoji': emoji,
        'justificacion': justificacion,
        'nota_odoo': nota_odoo,
    }


def enviar_email(resultados, errores, fecha_hora):
    if not resultados and not errores:
        return

    # Construir filas de la tabla HTML
    filas = ""
    for r in resultados:
        filas += (
            f"<tr>"
            f"<td style='padding:10px;border-bottom:1px solid #e0e0e0;font-weight:600'>{r['name']}</td>"
            f"<td style='padding:10px;border-bottom:1px solid #e0e0e0;text-align:center'>"
            f"  <span style='background:#e3f2fd;color:#0d47a1;padding:3px 10px;"
            f"border-radius:12px;font-weight:700;font-size:12px'>"
            f"{r['emoji']} {r['herramienta']}</span></td>"
            f"<td style='padding:10px;border-bottom:1px solid #e0e0e0;font-size:12px;"
            f"color:#546e7a'>{r['justificacion'][:120]}...</td>"
            f"</tr>"
        )

    filas_err = ""
    for e in errores:
        filas_err += (
            f"<tr><td colspan='3' style='padding:10px;color:#c62828;border-bottom:"
            f"1px solid #ffcdd2'>❌ Proyecto ID {e['project_id']}: {e['error']}</td></tr>"
        )

    total = len(resultados)
    asunto = f"🏛️ Dev Project Architect — {total} proyecto(s) analizados · {fecha_hora}"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:'Segoe UI',Arial,sans-serif">
<div style="max-width:680px;margin:32px auto;background:#fff;border-radius:12px;
            overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.10)">

  <!-- HEADER -->
  <div style="background:linear-gradient(135deg,#1a1a2e,#0f3460);padding:36px 40px;text-align:center">
    <div style="font-size:48px">🏛️</div>
    <h1 style="margin:8px 0 4px;font-size:22px;color:#e0e0e0">Dev Project Architect</h1>
    <p style="margin:0;font-size:13px;color:#90caf9">Reporte de análisis · {fecha_hora} · Universidad ISEP</p>
  </div>

  <!-- RESUMEN -->
  <div style="display:flex;background:#f8f9fc;border-bottom:1px solid #e8eaf0">
    <div style="flex:1;text-align:center;padding:20px;border-right:1px solid #e8eaf0">
      <span style="font-size:32px;font-weight:800;color:#2e7d32;display:block">{len(resultados)}</span>
      <span style="font-size:11px;color:#757575;text-transform:uppercase;letter-spacing:.6px">Analizados</span>
    </div>
    <div style="flex:1;text-align:center;padding:20px;border-right:1px solid #e8eaf0">
      <span style="font-size:32px;font-weight:800;color:#c62828;display:block">{len(errores)}</span>
      <span style="font-size:11px;color:#757575;text-transform:uppercase;letter-spacing:.6px">Errores</span>
    </div>
    <div style="flex:1;text-align:center;padding:20px">
      <span style="font-size:14px;font-weight:700;color:#0f3460;display:block;margin-top:6px">Odoo 16</span>
      <span style="font-size:11px;color:#e65100;text-transform:uppercase;letter-spacing:.6px">⚠️ Última opción</span>
    </div>
  </div>

  <!-- TABLA DE RESULTADOS -->
  <div style="padding:32px 40px">
    <p style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
              color:#0f3460;border-bottom:2px solid #e3f2fd;padding-bottom:6px;margin-bottom:16px">
      Proyectos analizados
    </p>
    <table style="width:100%;border-collapse:collapse">
      <thead>
        <tr style="background:#f0f4ff">
          <th style="padding:10px;text-align:left;font-size:12px;color:#546e7a">Proyecto</th>
          <th style="padding:10px;text-align:center;font-size:12px;color:#546e7a">Herramienta</th>
          <th style="padding:10px;text-align:left;font-size:12px;color:#546e7a">Justificación</th>
        </tr>
      </thead>
      <tbody>
        {filas if filas else "<tr><td colspan='3' style='text-align:center;padding:20px;color:#90a4ae'>Sin proyectos analizados en esta ronda</td></tr>"}
        {filas_err}
      </tbody>
    </table>

    <!-- NOTA ODOO -->
    <div style="margin-top:24px;background:#fff8e1;border-left:4px solid #f57f17;
                border-radius:6px;padding:14px 18px">
      <p style="margin:0 0 6px;font-size:12px;font-weight:700;color:#e65100">
        ⚠️ Recordatorio — Limitaciones Odoo 16
      </p>
      <p style="margin:0;font-size:12px;color:#5d4037;line-height:1.6">
        OOM Kill · Procesos idle bloqueados · Bucles de fallo recursivo ·
        Sobrecarga de módulos slide/mail/livechat · Memoria compartida Postgres/Redis/Odoo ·
        Arquitectura monolítica sin escalado horizontal.
        <b>Toda funcionalidad que pueda vivir fuera de Odoo, debe vivir fuera.</b>
      </p>
    </div>
  </div>

  <!-- FOOTER -->
  <div style="background:#f0f2f5;text-align:center;padding:20px 40px;
              border-top:1px solid #e0e0e0">
    <p style="margin:0;font-size:11px;color:#9e9e9e;line-height:1.7">
      Generado por <strong>Dev Project Architect 🏛️</strong><br/>
      Recibe el testigo de Dev Project Creator · Odoo 16 — UisepFinal<br/>
      <strong>Universidad ISEP</strong> — Dirección de TI
    </p>
  </div>
</div>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"]    = FROM_EMAIL
    msg["To"]      = RECIPIENTS[0]
    msg["Cc"]      = ", ".join(RECIPIENTS[1:])
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(FROM_EMAIL, RECIPIENTS, msg.as_string())
        log(f"  Email enviado a {len(RECIPIENTS)} destinatarios")
    except Exception as e:
        log(f"  ERROR email: {e}")


def main():
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    log("=" * 60)
    log(f"Dev Project Architect — inicio de ronda {fecha_hora}")

    models = get_models()
    db, uid, pwd = ODOO_DB, ODOO_UID, ODOO_PASS

    # Obtener project_ids desde argumento o buscar todos los pendientes
    if len(sys.argv) > 1:
        ids_a_analizar = [int(x) for x in sys.argv[1:]]
        log(f"Proyectos recibidos como argumento: {ids_a_analizar}")
    else:
        todos = models.execute_kw(db, uid, pwd, 'project.project', 'search_read',
            [[['active','=',True], ['tag_ids','in',[1]]]],
            {'fields': ['id','tag_ids']})
        ids_a_analizar = [
            p['id'] for p in todos
            if not TOOL_TAG_IDS.intersection(set(p['tag_ids']))
        ]
        log(f"Proyectos pendientes encontrados: {len(ids_a_analizar)}")

    resultados = []
    errores    = []

    for pid in ids_a_analizar:
        log(f"Analizando proyecto ID={pid}...")
        try:
            r = analizar_proyecto(models, pid)
            if r:
                resultados.append(r)
        except Exception as e:
            log(f"  ERROR proyecto {pid}: {e}")
            errores.append({'project_id': pid, 'error': str(e)})

    log(f"Ronda finalizada: {len(resultados)} analizados, {len(errores)} errores")
    enviar_email(resultados, errores, fecha_hora)
    log("=" * 60)


if __name__ == "__main__":
    main()
```
