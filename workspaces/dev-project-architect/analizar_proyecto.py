#!/usr/bin/env python3
"""
analizar_proyecto.py — Dev Project Architect
Analiza un proyecto y asigna la etiqueta de herramienta más adecuada.
Uso: python3 analizar_proyecto.py <project_id>
     python3 analizar_proyecto.py  (analiza todos los pendientes)
"""
import xmlrpc.client, ssl, sys, os, smtplib, re, json, base64
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
SMTP_USER = "AKIA5TSAYHSG3OD7XYK3"
SMTP_PASS = "BPMhIBG4+f4qfob+msLNNH9pYBlB74ERNi/cKXL1N+WI"
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
    "caraujo@universidadisep.com",
    "mgaja@universidadisep.com",
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

    # ── Regla absoluta: desarrollo de módulo/funcionalidad DENTRO de Odoo ──────
    # Se activa solo cuando el texto indica explícitamente que el DESARROLLO
    # vive dentro de Odoo (módulo custom, implementación en Odoo, desarrollo Odoo).
    # "Error en Odoo" o "proceso en Odoo" NO activan esto — son contexto, no intención.
    odoo_absoluto = bool(
        re.search(r'\bodoo\s+16\b', texto) or                     # "Odoo 16" → desarrollo de módulo
        re.search(r'implementar.{0,50}odoo', texto) or            # "implementar en/para Odoo"
        re.search(r'implementaci[oó]n.{0,50}odoo', texto) or      # "implementación ... Odoo"
        re.search(r'desarrollar.{0,40}odoo', texto) or            # "desarrollar en Odoo"
        re.search(r'desarrollo.{0,20}(módulo|modulo)', texto) or  # "desarrollo de módulo"
        re.search(r'(módulo|modulo).{0,40}\bodoo\b', texto) or    # "módulo ... odoo" (módulo para Odoo)
        re.search(r'módulo personaliz', texto) or                  # "módulo personalizado"
        re.search(r'modulo personaliz', texto)
    )

    # Señales fuertes por herramienta
    n8n_keywords = [
        'automatiz', 'sincroniz', 'integrac', 'flujo', 'webhook', 'trigger',
        'pipeline', 'cron', 'notificac', 'programad', 'n8n', 'schedule',
        'procesamiento', 'batch', 'masiv', 'importar', 'exportar', 'log',
        'monitoreo', 'analisis de log', 'análisis de log',
    ]
    # Señales Odoo: frases que indican claramente desarrollo DENTRO del ERP
    odoo_keywords_strong = [
        'formulario odoo', 'vista odoo', 'módulo odoo', 'modulo odoo',
        'modelo odoo', 'campo odoo', 'reporte odoo', 'odoo 16',
        'módulo personaliz', 'modulo personaliz',
    ]
    odoo_keywords_context = [
        # Funcionalidades propias del ERP que no tienen sentido fuera de Odoo
        'factura', 'inventario', 'venta', 'compra', 'contabilidad',
        'nómina', 'nomina', 'rh odoo', 'erp',
        # Procesos académicos que se gestionan dentro del ERP universitario
        'titulación', 'titulacion', 'expediente', 'matrícula', 'matricula',
        'alumno candidato', 'egresado', 'registro académico',
        # Módulo/campo/vista como sustantivo (desarrollo de módulo)
        'módulo met', 'modulo met', 'módulo electrónico', 'modulo electronico',
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
    for kw in odoo_keywords_strong:
        if kw in texto: scores['odoo'] += 4   # señal fuerte: claramente en Odoo
    for kw in odoo_keywords_context:
        if kw in texto: scores['odoo'] += 2   # señal de contexto ERP
    for kw in chatwoot_keywords:
        if kw in texto: scores['chatwoot'] += 2
    for kw in mautic_keywords:
        if kw in texto: scores['mautic'] += 2
    for kw in wordpress_keywords:
        if kw in texto: scores['wordpress'] += 2

    # Penalizar Odoo solo si n8n domina claramente Y Odoo no tiene señales fuertes.
    # Si el proyecto dice explícitamente "en Odoo" o "módulo Odoo", NO penalizar.
    if scores['n8n'] > 0 and scores['odoo'] > 0 and not odoo_absoluto:
        if scores['odoo'] < scores['n8n']:
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


def _inferir_contexto(nombre, desc_texto):
    """
    Extrae del nombre y descripción: tipo de trigger, modelos Odoo involucrados,
    acción principal, y palabras clave técnicas.
    """
    texto = (nombre + ' ' + desc_texto).lower()

    # Tipo de trigger
    if any(k in texto for k in ['cron', 'programad', 'cada hora', 'diario', 'periódic', 'schedule']):
        trigger = 'cron'
    elif any(k in texto for k in ['error', 'fallo', 'falla', 'excepción', 'exception']):
        trigger = 'error_event'
    elif any(k in texto for k in ['botón', 'acción', 'manual', 'click', 'on demand']):
        trigger = 'manual'
    else:
        trigger = 'webhook'

    # Modelos Odoo detectados
    modelos = []
    if any(k in texto for k in ['alumno', 'estudiante', 'matrícula', 'academic', 'académic', 'curso', 'asignatura']):
        modelos.append('openeducat.student / slide.channel')
    if any(k in texto for k in ['log', 'registro', 'error log', 'servidor']):
        modelos.append('ir.logging / server logs')
    if any(k in texto for k in ['factura', 'pago', 'venta', 'sale']):
        modelos.append('account.move / sale.order')
    if any(k in texto for k in ['contacto', 'partner', 'cliente']):
        modelos.append('res.partner')
    if any(k in texto for k in ['tarea', 'proyecto', 'task']):
        modelos.append('project.task / project.project')
    if any(k in texto for k in ['correo', 'email', 'notif']):
        modelos.append('mail.message / mail.template')
    if not modelos:
        modelos.append('(modelo a determinar en análisis)')

    # Acción principal
    if any(k in texto for k in ['analiz', 'monitoreo', 'monitor', 'reporte', 'report', 'log']):
        accion = 'análisis y monitoreo'
    elif any(k in texto for k in ['sincroniz', 'sync', 'importar', 'exportar', 'masiv']):
        accion = 'sincronización masiva'
    elif any(k in texto for k in ['error', 'fallo', 'correg', 'fix', 'reparar']):
        accion = 'detección y corrección de errores'
    elif any(k in texto for k in ['notif', 'correo', 'email', 'aviso']):
        accion = 'notificación automática'
    elif any(k in texto for k in ['creat', 'crear', 'generar', 'generat']):
        accion = 'creación automatizada'
    else:
        accion = 'automatización de proceso'

    return trigger, modelos, accion


def generar_prompt_ia(herramienta, nombre, desc_texto):
    """
    Genera un prompt de desarrollo IA específico al proyecto,
    no genérico. Analiza nombre y descripción para incluir
    contexto técnico real.
    """
    trigger, modelos, accion = _inferir_contexto(nombre, desc_texto)
    desc_recortada = desc_texto[:800] if desc_texto else '(sin descripción)'
    modelos_str = ', '.join(modelos)

    encabezado = (
        f"PROYECTO: {nombre}\n"
        f"DESCRIPCIÓN ORIGINAL:\n{desc_recortada}\n"
        f"{'─'*60}\n\n"
    )

    if herramienta == 'n8n':
        trigger_desc = {
            'cron':        'un Schedule Trigger (ejecución periódica configurable)',
            'error_event': 'un Webhook POST que Odoo dispara cuando ocurre el error/evento',
            'manual':      'un Webhook POST invocado desde un botón/acción en Odoo',
            'webhook':     'un Webhook POST llamado desde Odoo via HTTP Request',
        }[trigger]

        prompt = (
            f"{encabezado}"
            f"Eres un experto en automatización con n8n e integración Odoo 16.\n\n"
            f"Tu misión: implementar el workflow n8n que resuelve — {accion} — para el proyecto descrito.\n\n"
            f"ARQUITECTURA (patrón Odoo → n8n → Odoo):\n"
            f"1. TRIGGER: {trigger_desc}\n"
            f"2. LECTURA: n8n consulta Odoo via XML-RPC para obtener los datos necesarios\n"
            f"   → Modelos involucrados: {modelos_str}\n"
            f"3. PROCESAMIENTO: n8n ejecuta la lógica de {accion} de forma autónoma\n"
            f"4. ESCRITURA: n8n registra el resultado en Odoo via XML-RPC (message_post + write)\n"
            f"5. NOTIFICACIÓN: n8n envía alerta (email/chatter) si hay errores o resultados relevantes\n\n"
            f"NODOS REQUERIDOS (en este orden):\n"
            f"  [1] Trigger ({trigger_desc})\n"
            f"  [2] HTTP Request → Odoo XML-RPC: leer datos de {modelos_str}\n"
            f"  [3] Code Node: implementar lógica de {accion}\n"
            f"  [4] IF/Switch: ramificar según resultado (éxito / error / sin datos)\n"
            f"  [5] HTTP Request → Odoo XML-RPC: escribir resultado / message_post en chatter\n"
            f"  [6] Error Trigger: capturar fallos y notificar\n\n"
            f"RESTRICCIONES:\n"
            f"- Odoo 16 NO ejecuta la lógica (OOM Kill, workers idle, arquitectura monolítica)\n"
            f"- Todo el procesamiento vive en n8n\n"
            f"- Usar XML-RPC con uid=5064, db=UisepFinal, url=https://app.universidadisep.com\n\n"
            f"ENTREGABLES:\n"
            f"1. Diseño detallado del flujo nodo por nodo\n"
            f"2. Código JavaScript del Code Node con la lógica real\n"
            f"3. Configuración XML-RPC de cada HTTP Request\n"
            f"4. JSON exportable del workflow completo\n\n"
            f"Empieza describiendo el flujo completo, luego genera el código de cada nodo."
        )

    elif herramienta == 'odoo':
        prompt = (
            f"{encabezado}"
            f"Eres un desarrollador Odoo 16 con dominio de sus limitaciones estructurales.\n\n"
            f"Tu misión: implementar — {accion} — directamente en Odoo 16.\n"
            f"Modelos involucrados: {modelos_str}\n\n"
            f"RESTRICCIONES CRÍTICAS (no negociables):\n"
            f"- NO agregar dependencia de im_livechat, slide, mail_tracking ni módulos pesados\n"
            f"- Queries optimizadas: search_read con fields=['id','name'] como mínimo, nunca browse() masivo\n"
            f"- Sin compute fields store=True sobre modelos con >1000 registros\n"
            f"- Métodos transaccionales cortos: commit frecuente, no acumular recordsets en memoria\n"
            f"- Validar con --limit-memory-soft=2147483648 en staging antes de producción\n\n"
            f"ENTREGABLES:\n"
            f"1. __manifest__.py con dependencias mínimas\n"
            f"2. models/ con los modelos/extensiones necesarias\n"
            f"3. views/ con vistas XML optimizadas (sin widgets pesados)\n"
            f"4. security/ir.model.access.csv\n"
            f"5. Estimación de impacto en RAM (workers × consumo por request)\n\n"
            f"Diseña la arquitectura del módulo, documenta el impacto en memoria, luego implementa."
        )

    elif herramienta == 'chatwoot':
        prompt = (
            f"{encabezado}"
            f"Eres experto en Chatwoot y en integración con Odoo 16.\n\n"
            f"Tu misión: configurar e implementar — {accion} — usando Chatwoot.\n"
            f"Contexto Odoo: {modelos_str}\n\n"
            f"ENTREGABLES:\n"
            f"1. Configuración del inbox/canal (tipo, credenciales, agentes asignados)\n"
            f"2. Flujo de conversación del bot con árbol de decisión\n"
            f"3. Webhook Chatwoot → n8n/Odoo para sincronizar eventos de conversación\n"
            f"4. Plantillas de respuesta rápida por caso de uso\n"
            f"5. Reglas de escalado a agente humano con SLA\n\n"
            f"Describe primero el árbol de conversación, luego la configuración técnica."
        )

    elif herramienta == 'mautic':
        prompt = (
            f"{encabezado}"
            f"Eres experto en Mautic y automatización de marketing.\n\n"
            f"Tu misión: diseñar e implementar — {accion} — en Mautic.\n"
            f"Fuente de datos Odoo: {modelos_str}\n\n"
            f"ENTREGABLES:\n"
            f"1. Segmento de contactos: filtros exactos para extraer el público objetivo desde Odoo\n"
            f"2. Campaña: trigger → condiciones → acciones (emails, puntos, tags)\n"
            f"3. Plantillas HTML responsive para cada email del flujo\n"
            f"4. Lead scoring: puntos por comportamiento relevante al proyecto\n"
            f"5. Webhook/API para sincronizar contactos Odoo ↔ Mautic\n\n"
            f"Define primero el objetivo de conversión, luego el flujo y las plantillas."
        )

    elif herramienta == 'wordpress':
        prompt = (
            f"{encabezado}"
            f"Eres experto en WordPress con enfoque en rendimiento y conversión.\n\n"
            f"Tu misión: desarrollar — {accion} — en WordPress.\n"
            f"Integración con Odoo ({modelos_str}) si aplica.\n\n"
            f"ENTREGABLES:\n"
            f"1. Arquitectura de páginas y jerarquía de URLs\n"
            f"2. Stack de plugins justificado (sin plugins innecesarios)\n"
            f"3. Template/componentes para las secciones clave\n"
            f"4. Formularios con integración a Mautic (captación) u Odoo (operacional)\n"
            f"5. Configuración de caché (WP Rocket o W3TC) + CDN\n"
            f"6. Checklist de seguridad y SEO técnico\n\n"
            f"Propón el wireframe primero, luego el stack y la implementación."
        )

    else:  # desarrollos-apis
        prompt = (
            f"{encabezado}"
            f"Eres arquitecto de software experto en APIs REST y microservicios.\n\n"
            f"Tu misión: diseñar e implementar — {accion} — como servicio independiente.\n"
            f"Modelos Odoo involucrados (si aplica): {modelos_str}\n\n"
            f"ENTREGABLES:\n"
            f"1. Contratos de API (OpenAPI 3.0): endpoints, request/response schemas, códigos HTTP\n"
            f"2. Stack tecnológico: lenguaje, framework, DB (justificado)\n"
            f"3. Autenticación: API Key en header o JWT según el cliente\n"
            f"4. Integración Odoo: XML-RPC con uid=5064, db=UisepFinal (si se requiere)\n"
            f"5. Docker Compose: servicio + dependencias\n"
            f"6. Tests de integración con casos de éxito y error\n\n"
            f"Diseña los contratos primero, luego la implementación."
        )

    return prompt


def generar_json_n8n(nombre, desc_texto):
    """
    Genera un workflow n8n JSON específico al proyecto.
    El nodo de código contiene lógica real basada en la descripción,
    y los nodos de lectura/escritura Odoo usan los modelos inferidos.
    """
    trigger, modelos, accion = _inferir_contexto(nombre, desc_texto)
    slug   = re.sub(r'[^a-z0-9]+', '-', nombre.lower())[:40].strip('-')
    texto  = (nombre + ' ' + desc_texto).lower()

    # ── Código del nodo principal (específico al proyecto) ────────────────────
    es_logs = any(k in texto for k in ['log', 'oom', 'memoria', 'proceso', 'worker', 'idle'])
    es_contenido_academico = any(k in texto for k in ['académic', 'academic', 'contenido', 'slide', 'curso', 'asignatura'])
    es_sync = any(k in texto for k in ['sincroniz', 'masiv', 'importar', 'exportar'])
    es_error = any(k in texto for k in ['error', 'fallo', 'falla', 'correg'])
    es_notif = any(k in texto for k in ['notif', 'correo', 'email', 'aviso'])

    if es_logs:
        modelo_lectura = 'ir.logging'
        campos_lectura = "['id','name','level','message','func','path','create_date']"
        dominio_lectura = "[['level','in',['ERROR','CRITICAL']],'|',['message','ilike','OOM'],['message','ilike','MemoryError']]"
        logica_codigo = (
            "// ── Análisis de logs Odoo16 ──────────────────────────────\n"
            "const registros = $input.first().json;\n"
            "const logs = Array.isArray(registros) ? registros : [registros];\n\n"
            "const resumen = { total: logs.length, oom: 0, errores: [], workers_idle: 0 };\n\n"
            "for (const log of logs) {\n"
            "  const msg = (log.message || '').toLowerCase();\n"
            "  if (msg.includes('oom') || msg.includes('memory')) resumen.oom++;\n"
            "  if (msg.includes('idle') || msg.includes('blocked'))  resumen.workers_idle++;\n"
            "  if (log.level === 'CRITICAL' || log.level === 'ERROR') {\n"
            "    resumen.errores.push({ id: log.id, msg: log.message?.slice(0,200), fecha: log.create_date });\n"
            "  }\n"
            "}\n\n"
            "const alerta = resumen.oom > 0 || resumen.workers_idle > 0 || resumen.errores.length > 5;\n"
            "const reporte = `📊 Análisis logs Odoo16:\\n`\n"
            "  + `- Total errores: ${resumen.total}\\n`\n"
            "  + `- OOM / MemoryError: ${resumen.oom}\\n`\n"
            "  + `- Workers idle/blocked: ${resumen.workers_idle}\\n`\n"
            "  + `- Críticos: ${resumen.errores.length}\\n`\n"
            "  + (alerta ? '⚠️ Se requiere revisión inmediata.' : '✅ Sin alertas críticas.');\n\n"
            "return [{ json: { resumen, reporte, alerta, totalLogs: resumen.total } }];"
        )
        accion_odoo_write = "message_post en project.task del proyecto de monitoreo con el reporte generado"
        modelo_escritura = 'project.task'
        campo_escritura = 'message_post'

    elif es_contenido_academico:
        modelo_lectura = 'slide.channel'
        campos_lectura = "['id','name','website_published','channel_type','active']"
        dominio_lectura = "[['active','=',True],['website_published','=',False]]"
        logica_codigo = (
            "// ── Validación y corrección de contenidos académicos ─────\n"
            "const registros = $input.first().json;\n"
            "const items = Array.isArray(registros) ? registros : [registros];\n\n"
            "const errores   = [];\n"
            "const corregidos = [];\n\n"
            "for (const item of items) {\n"
            "  const problemas = [];\n"
            "  if (!item.name || item.name.trim() === '')   problemas.push('nombre vacío');\n"
            "  if (!item.channel_type)                      problemas.push('tipo de canal no definido');\n"
            "  if (item.website_published === false)        problemas.push('no publicado');\n\n"
            "  if (problemas.length > 0) {\n"
            "    errores.push({ id: item.id, nombre: item.name, problemas });\n"
            "  } else {\n"
            "    corregidos.push(item.id);\n"
            "  }\n"
            "}\n\n"
            "const reporte = `📚 Validación contenidos académicos:\\n`\n"
            "  + `- Total revisados: ${items.length}\\n`\n"
            "  + `- Con errores: ${errores.length}\\n`\n"
            "  + `- Sin problemas: ${corregidos.length}\\n`\n"
            "  + errores.map(e => `  ⚠️ ID ${e.id} (${e.nombre}): ${e.problemas.join(', ')}`).join('\\n');\n\n"
            "return [{ json: { errores, corregidos, reporte, hayErrores: errores.length > 0 } }];"
        )
        accion_odoo_write = "write en slide.channel para corregir registros + message_post con reporte"
        modelo_escritura = 'slide.channel'
        campo_escritura = 'write'

    elif es_sync:
        modelo_lectura = modelos[0].split('/')[0].strip() if modelos else 'project.task'
        campos_lectura = "['id','name','active','write_date']"
        dominio_lectura = "[['active','=',True]]"
        logica_codigo = (
            "// ── Sincronización masiva ────────────────────────────────\n"
            "const registros = $input.first().json;\n"
            "const items = Array.isArray(registros) ? registros : [registros];\n\n"
            "const procesados = [];\n"
            "const fallidos   = [];\n\n"
            "for (const item of items) {\n"
            "  try {\n"
            "    // Lógica de transformación/sincronización\n"
            "    const transformado = {\n"
            "      id: item.id,\n"
            "      nombre: item.name,\n"
            "      ultimo_cambio: item.write_date,\n"
            "      estado: 'sincronizado'\n"
            "    };\n"
            "    procesados.push(transformado);\n"
            "  } catch (e) {\n"
            "    fallidos.push({ id: item.id, error: e.message });\n"
            "  }\n"
            "}\n\n"
            "return [{ json: { procesados, fallidos, total: items.length,\n"
            "                   exitosos: procesados.length, errores: fallidos.length } }];"
        )
        accion_odoo_write = "write masivo en los registros sincronizados + message_post con resultado"
        modelo_escritura = modelo_lectura
        campo_escritura = 'write'

    else:
        modelo_lectura = modelos[0].split('/')[0].strip() if modelos else 'project.task'
        campos_lectura = "['id','name','description','active']"
        dominio_lectura = "[['active','=',True]]"
        logica_codigo = (
            f"// ── {accion.title()} ────────────────────────────────────\n"
            "const data = $input.first().json;\n"
            "const payload = Array.isArray(data) ? data : [data];\n\n"
            "const resultados = payload.map(item => ({\n"
            "  id: item.id,\n"
            "  nombre: item.name || item.display_name || '',\n"
            "  procesado: true,\n"
            "  timestamp: new Date().toISOString()\n"
            "}));\n\n"
            "const reporte = `✅ Procesados: ${resultados.length} registros.`;\n"
            "return [{ json: { resultados, reporte, total: resultados.length } }];"
        )
        accion_odoo_write = "message_post con el resultado del procesamiento"
        modelo_escritura = modelo_lectura
        campo_escritura = 'message_post'

    # ── Nodo trigger según tipo ────────────────────────────────────────────────
    if trigger == 'cron':
        nodo_trigger = {
            "parameters": {"rule": {"interval": [{"field": "hours", "minutesInterval": 6}]}},
            "id": "node-trigger", "name": "Schedule — Cada 6 horas",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1, "position": [240, 300]
        }
    else:
        nodo_trigger = {
            "parameters": {"httpMethod": "POST", "path": slug,
                           "responseMode": "responseNode", "options": {}},
            "id": "node-trigger", "name": f"Webhook — {nombre[:35]}",
            "type": "n8n-nodes-base.webhook", "typeVersion": 2,
            "position": [240, 300], "webhookId": f"odoo-{slug}"
        }

    # ── XML-RPC de lectura ─────────────────────────────────────────────────────
    xml_lectura = (
        f'<?xml version="1.0"?><methodCall><methodName>execute_kw</methodName><params>'
        f'<param><value><string>UisepFinal</string></value></param>'
        f'<param><value><int>5064</int></value></param>'
        f'<param><value><string>${ODOO_RPC_PASSWORD}</string></value></param>'
        f'<param><value><string>{modelo_lectura}</string></value></param>'
        f'<param><value><string>search_read</string></value></param>'
        f'<param><value><array><data><value><array><data>'
        f'<value><array><data>{dominio_lectura}</data></array></value>'
        f'</data></array></value></data></array></value></param>'
        f'<param><value><struct>'
        f'<member><name>fields</name><value><array><data>{campos_lectura}</data></array></value></member>'
        f'<member><name>limit</name><value><int>100</int></value></member>'
        f'</struct></value></param>'
        f'</params></methodCall>'
    )

    # ── XML-RPC de escritura ───────────────────────────────────────────────────
    xml_escritura = (
        f'<?xml version="1.0"?><methodCall><methodName>execute_kw</methodName><params>'
        f'<param><value><string>UisepFinal</string></value></param>'
        f'<param><value><int>5064</int></value></param>'
        f'<param><value><string>${ODOO_RPC_PASSWORD}</string></value></param>'
        f'<param><value><string>{modelo_escritura}</string></value></param>'
        f'<param><value><string>message_post</string></value></param>'
        f'<param><value><array><data>'
        f'<value><array><data><value><int>1</int></data></array></value>'
        f'</data></array></value></param>'
        f'<param><value><struct>'
        f'<member><name>body</name><value><string>{{{{$json.reporte}}}}</string></value></member>'
        f'<member><name>message_type</name><value><string>comment</string></value></member>'
        f'<member><name>subtype_xmlid</name><value><string>mail.mt_note</string></value></member>'
        f'</struct></value></param>'
        f'</params></methodCall>'
    )

    workflow = {
        "name": nombre,
        "nodes": [
            nodo_trigger,
            {
                "parameters": {
                    "method": "POST",
                    "url": "https://app.universidadisep.com/xmlrpc/2/object",
                    "sendHeaders": True,
                    "headerParameters": {"parameters": [
                        {"name": "Content-Type", "value": "application/xml"}
                    ]},
                    "sendBody": True,
                    "contentType": "raw",
                    "rawContentType": "application/xml",
                    "body": xml_lectura,
                    "options": {}
                },
                "id": "node-odoo-read", "name": f"Leer {modelo_lectura} desde Odoo",
                "type": "n8n-nodes-base.httpRequest", "typeVersion": 4,
                "position": [500, 300]
            },
            {
                "parameters": {"jsCode": logica_codigo},
                "id": "node-logic", "name": f"Procesar — {accion.title()}",
                "type": "n8n-nodes-base.code", "typeVersion": 2,
                "position": [760, 300]
            },
            {
                "parameters": {
                    "conditions": {"options": {"caseSensitive": False},
                                   "conditions": [{"leftValue": "={{$json.alerta || $json.hayErrores || $json.errores}}",
                                                   "operator": {"type": "boolean", "operation": "true"}}]},
                    "options": {}
                },
                "id": "node-if", "name": "¿Hay alertas o errores?",
                "type": "n8n-nodes-base.if", "typeVersion": 2,
                "position": [1020, 300]
            },
            {
                "parameters": {
                    "method": "POST",
                    "url": "https://app.universidadisep.com/xmlrpc/2/object",
                    "sendHeaders": True,
                    "headerParameters": {"parameters": [
                        {"name": "Content-Type", "value": "application/xml"}
                    ]},
                    "sendBody": True,
                    "contentType": "raw",
                    "rawContentType": "application/xml",
                    "body": xml_escritura,
                    "options": {}
                },
                "id": "node-odoo-write", "name": f"Escribir en Odoo — {accion_odoo_write[:40]}",
                "type": "n8n-nodes-base.httpRequest", "typeVersion": 4,
                "position": [1280, 200]
            },
            {
                "parameters": {
                    "respondWith": "json",
                    "responseBody": '={"status":"ok","reporte":"{{$json.reporte}}","total":{{$json.total || 0}}}',
                    "options": {}
                },
                "id": "node-response", "name": "Respuesta OK a Odoo",
                "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1,
                "position": [1540, 200]
            },
            {
                "parameters": {
                    "respondWith": "json",
                    "responseBody": '={"status":"sin_cambios","mensaje":"Sin registros que procesar"}',
                    "options": {}
                },
                "id": "node-noop", "name": "Sin cambios — responder OK",
                "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1,
                "position": [1280, 440]
            }
        ],
        "connections": {
            nodo_trigger["name"]: {
                "main": [[{"node": f"Leer {modelo_lectura} desde Odoo", "type": "main", "index": 0}]]
            },
            f"Leer {modelo_lectura} desde Odoo": {
                "main": [[{"node": f"Procesar — {accion.title()}", "type": "main", "index": 0}]]
            },
            f"Procesar — {accion.title()}": {
                "main": [[{"node": "¿Hay alertas o errores?", "type": "main", "index": 0}]]
            },
            "¿Hay alertas o errores?": {
                "main": [
                    [{"node": f"Escribir en Odoo — {accion_odoo_write[:40]}", "type": "main", "index": 0}],
                    [{"node": "Sin cambios — responder OK", "type": "main", "index": 0}]
                ]
            },
            f"Escribir en Odoo — {accion_odoo_write[:40]}": {
                "main": [[{"node": "Respuesta OK a Odoo", "type": "main", "index": 0}]]
            }
        },
        "settings": {
            "executionOrder": "v1",
            "saveManualExecutions": True,
            "errorWorkflow": ""
        },
        "meta": {
            "generatedBy": "Dev Project Architect",
            "project": nombre,
            "accion": accion,
            "trigger": trigger,
            "modeloOdoo": modelos,
            "patron": "Odoo → n8n → Odoo XML-RPC",
            "createdAt": datetime.now().isoformat()
        }
    }
    return json.dumps(workflow, ensure_ascii=False, indent=2)



def crear_subtarea_prompt(models, project_id, nombre, herramienta, prompt_texto, json_n8n=None):
    """Crea la subtarea 'Prompt de desarrollo IA' y adjunta el JSON si aplica."""
    db, uid, pwd = ODOO_DB, ODOO_UID, ODOO_PASS

    # Buscar tarea padre: "Análisis de requerimientos y alcance"
    padre = models.execute_kw(db, uid, pwd, 'project.task', 'search_read',
        [[['project_id', '=', project_id],
          ['name', '=', 'Análisis de requerimientos y alcance']]],
        {'fields': ['id'], 'limit': 1})
    parent_id = padre[0]['id'] if padre else False

    # Buscar el stage "Análisis" del proyecto
    stages = models.execute_kw(db, uid, pwd, 'project.task.type', 'search_read',
        [[['project_ids', 'in', [project_id]], ['name', '=', 'Análisis']]],
        {'fields': ['id'], 'limit': 1})
    stage_id = stages[0]['id'] if stages else False

    emoji = TOOL_EMOJIS.get(herramienta, '🔌')
    subtask_name = f"{emoji} Prompt de desarrollo IA — {herramienta.upper()}"

    subtask_vals = {
        'name': subtask_name,
        'project_id': project_id,
        'description': f'<pre>{prompt_texto}</pre>',
        'user_ids': [(4, uid)],
        'priority': '1',
    }
    if parent_id:
        subtask_vals['parent_id'] = parent_id
    if stage_id:
        subtask_vals['stage_id'] = stage_id

    subtask_id = models.execute_kw(db, uid, pwd, 'project.task', 'create', [subtask_vals])

    # Adjuntar JSON n8n si aplica
    if json_n8n:
        filename = re.sub(r'[^a-z0-9]+', '_', nombre.lower())[:40].strip('_')
        models.execute_kw(db, uid, pwd, 'ir.attachment', 'create', [{
            'name': f'workflow_n8n_{filename}.json',
            'res_model': 'project.task',
            'res_id': subtask_id,
            'type': 'binary',
            'mimetype': 'application/json',
            'datas': base64.b64encode(json_n8n.encode('utf-8')).decode('ascii'),
        }])

    return subtask_id


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

    # Leer tarea de análisis; si no existe, crearla a partir del nombre del proyecto
    tarea = models.execute_kw(db, uid, pwd, 'project.task', 'search_read',
        [[['project_id','=',project_id],
          ['name','=','Análisis de requerimientos y alcance']]],
        {'fields': ['id','description']})

    if not tarea:
        # Buscar el primer stage disponible del proyecto (o ninguno)
        stages_p = models.execute_kw(db, uid, pwd, 'project.task.type', 'search_read',
            [[['project_ids', 'in', [project_id]]]],
            {'fields': ['id','name'], 'order': 'sequence asc', 'limit': 1})
        stage_fallback = stages_p[0]['id'] if stages_p else False

        task_vals = {
            'name': 'Análisis de requerimientos y alcance',
            'project_id': project_id,
            'description': (
                f'<p><b>Proyecto:</b> {nombre}</p>'
                f'<p>Tarea creada automáticamente por Dev Project Architect. '
                f'Pendiente de levantamiento de requerimientos detallado.</p>'
            ),
        }
        if stage_fallback:
            task_vals['stage_id'] = stage_fallback

        new_task_id = models.execute_kw(db, uid, pwd, 'project.task', 'create', [task_vals])
        log(f"  ℹ️  Tarea 'Análisis de requerimientos y alcance' creada (ID:{new_task_id})")
        desc_tarea = ''
    else:
        desc_tarea = tarea[0].get('description', '') or ''

    desc_completa = strip_html((proj.get('description') or '') + ' ' + desc_tarea)

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

    # Paso 4 — Asignar etiqueta (con verificación post-write y reintento)
    models.execute_kw(db, uid, pwd, 'project.project', 'write',
        [[project_id], {'tag_ids': [(4, tag_id, 0)]}])
    tags_check = models.execute_kw(db, uid, pwd, 'project.project', 'read',
        [[project_id]], {'fields': ['tag_ids']})[0]['tag_ids']
    if tag_id not in tags_check:
        models.execute_kw(db, uid, pwd, 'project.project', 'write',
            [[project_id], {'tag_ids': [(4, tag_id, 0)]}])

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

    # Paso 6 — Crear subtarea con prompt de desarrollo IA
    prompt_texto = generar_prompt_ia(herramienta, nombre, desc_completa)
    json_n8n = generar_json_n8n(nombre, desc_completa) if herramienta == 'n8n' else None
    subtask_id = crear_subtarea_prompt(models, project_id, nombre, herramienta,
                                       prompt_texto, json_n8n)

    # Paso 7 — Nota de cierre en chatter con resumen
    resumen_subtarea = (
        f'<p>✅ <b>Análisis completado exitosamente.</b></p>'
        f'<p><b>Subtarea creada:</b> "{TOOL_EMOJIS.get(herramienta,"🔌")} Prompt de desarrollo IA — '
        f'{herramienta.upper()}" (ID: {subtask_id})</p>'
        f'<p>La subtarea contiene el prompt detallado para desarrollar este proyecto con IA '
        f'usando <b>{herramienta}</b>.'
        f'{"  Se adjunta el <b>JSON de workflow n8n</b> con el patrón Odoo → Webhook → n8n → Odoo." if json_n8n else ""}'
        f'</p>'
        f'<p><em>— Dev Project Architect 🏛️</em></p>'
    )
    models.execute_kw(db, uid, pwd, 'project.project', 'message_post',
        [[project_id]], {
            'body': resumen_subtarea,
            'message_type': 'comment',
            'subtype_xmlid': 'mail.mt_note'
        })

    log(f"  ✅ '{nombre}' (ID:{project_id}) → {herramienta} | subtarea #{subtask_id}"
        + (" + JSON n8n adjunto" if json_n8n else ""))

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
        'subtask_id': subtask_id,
        'json_n8n': bool(json_n8n),
    }


def enviar_email(resultados, errores, fecha_hora):
    if not resultados and not errores:
        return

    # Construir filas de la tabla HTML
    filas = ""
    for r in resultados:
        badge_json = (" &nbsp;<span style='background:#e8f5e9;color:#2e7d32;padding:2px 7px;"
                      "border-radius:10px;font-size:10px;font-weight:700'>📎 JSON n8n</span>"
                      if r.get('json_n8n') else "")
        filas += (
            f"<tr>"
            f"<td style='padding:10px;border-bottom:1px solid #e0e0e0;font-weight:600'>"
            f"  {r['name']}<br/>"
            f"  <span style='font-size:11px;color:#90a4ae;font-weight:400'>"
            f"  Subtarea #{r.get('subtask_id','?')}</span>"
            f"</td>"
            f"<td style='padding:10px;border-bottom:1px solid #e0e0e0;text-align:center'>"
            f"  <span style='background:#e3f2fd;color:#0d47a1;padding:3px 10px;"
            f"  border-radius:12px;font-weight:700;font-size:12px'>"
            f"  {r['emoji']} {r['herramienta']}</span>{badge_json}</td>"
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
