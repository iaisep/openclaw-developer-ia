#!/usr/bin/env python3
"""
Dev Project Creator — Cron Runner
Ejecuta cada hora via crontab.
Lee tareas de Incidencias TI (proyecto 53, stage 703, solo Administrator id=2)
y de Pote (proyecto 36, activas), crea proyectos con estructura de software,
limpia las tareas fuente y notifica por email via AWS SES.
"""

import xmlrpc.client
import ssl
import subprocess
import smtplib
import re
import os
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

ARCHITECT_SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "dev-project-architect", "analizar_proyecto.py"
)

# ── Odoo RPC ──────────────────────────────────────────────────────────────────
ODOO_URL  = "https://app.universidadisep.com"
ODOO_DB   = "UisepFinal"
ODOO_UID  = 5064
ODOO_PASS = "${ODOO_RPC_PASSWORD}"

# ── SSH / réplica ─────────────────────────────────────────────────────────────
SSH_KEY    = "/.keys/odoo-dev.pem"
SSH_HOST   = "root@189.195.191.16"
PG_CONTAINER = "postgres-replica-i4s8o8000kc040cgwcwowwwc"

# ── AWS SES ───────────────────────────────────────────────────────────────────
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
    "mgaja@universidadisep.com",
]

# ── Rutas ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "email_template.html")
MEMORY_PATH   = os.path.join(SCRIPT_DIR, "..", "memory", "proyectos-creados.md")
LOG_PATH      = os.path.join(SCRIPT_DIR, "cron.log")

# ── Stages estándar de software con tarea placeholder por stage ───────────────
# (nombre_stage, secuencia, nombre_tarea_placeholder)
STAGES_CONFIG = [
    ("Análisis",     1, "Análisis de requerimientos y alcance"),
    ("Diseño",       2, "Diseño técnico del sistema"),
    ("Desarrollo",   3, "Desarrollo e implementación"),
    ("Pruebas / QA", 4, "Plan y ejecución de pruebas"),
    ("Producción",   5, "Despliegue a producción"),
    ("Cerrado",      6, "Cierre y documentación del proyecto"),
]


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")


def odoo_models():
    ctx = ssl.create_default_context()
    return xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object", context=ctx)


def sql_replica(query):
    """Ejecuta una query en la réplica PostgreSQL via SSH y devuelve filas."""
    cmd = (
        f'ssh -o StrictHostKeyChecking=no -i {SSH_KEY} {SSH_HOST} '
        f'"docker exec {PG_CONTAINER} psql -U odoo -d {ODOO_DB} -t -A -F\'|\' -c \\"{query}\\""'
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    rows = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line and not line.startswith("--"):
            rows.append(line.split("|"))
    return rows


def leer_incidencias(models):
    """Tareas en Incidencias TI, stage 703, asignadas SOLO a Administrator (id=2).
    Lee directo desde RPC de producción para evitar lag de la réplica."""
    db, uid, pwd = ODOO_DB, ODOO_UID, ODOO_PASS
    candidatas = models.execute_kw(db, uid, pwd, 'project.task', 'search_read',
        [[['project_id', '=', 53], ['stage_id', '=', 703], ['active', '=', True]]],
        {'fields': ['id', 'name', 'description', 'user_ids']})
    tasks = []
    for t in candidatas:
        # Regla de oro: ÚNICAMENTE Administrator (id=2), sin otros asignados
        if t['user_ids'] == [2]:
            tasks.append({
                "id": t['id'],
                "name": t['name'],
                "description": t.get('description') or "",
                "source": "incidencias",
            })
    return tasks


def leer_pote(models):
    """Tareas activas del proyecto Pote (id=36).
    Lee directo desde RPC de producción para evitar lag de la réplica."""
    db, uid, pwd = ODOO_DB, ODOO_UID, ODOO_PASS
    # Excluir la tarea de migración histórica (#742)
    rows = models.execute_kw(db, uid, pwd, 'project.task', 'search_read',
        [[['project_id', '=', 36], ['active', '=', True], ['id', '!=', 742]]],
        {'fields': ['id', 'name', 'description']})
    tasks = []
    for t in rows:
        tasks.append({
            "id": t['id'],
            "name": t['name'],
            "description": t.get('description') or "",
            "source": "pote",
        })
    return tasks


def crear_proyecto(models, task):
    """Crea el proyecto, sus stages y la tarea inicial. Retorna project_id o None."""
    db, uid, pwd = ODOO_DB, ODOO_UID, ODOO_PASS
    name = task["name"]
    desc = task["description"] or f'[Sin descripción — revisar tarea fuente ID: {task["id"]}]'

    # Anti-duplicados
    count = models.execute_kw(db, uid, pwd, "project.project", "search_count",
        [[["name", "=", name], ["active", "in", [True, False]]]])
    if count > 0:
        log(f"  SKIP duplicado: '{name}'")
        return None, None

    # Crear proyecto
    project_id = models.execute_kw(db, uid, pwd, "project.project", "create", [{
        "name": name,
        "description": desc,
        "user_id": uid,
        "privacy_visibility": "employees",
        "tag_ids": [(4, 1)],   # Etiqueta: Tecnología (id=1)
        "stage_id": 1,         # Etapa: To Do / Por hacer (id=1)
    }])

    # Crear stages y una tarea por cada uno
    stage_ids = []
    for s_name, s_seq, _ in STAGES_CONFIG:
        sid = models.execute_kw(db, uid, pwd, "project.task.type", "create", [{
            "name": s_name,
            "sequence": s_seq,
            "project_ids": [(4, project_id)],
        }])
        stage_ids.append(sid)

    # Crear tarea en cada stage; el primero (Análisis) lleva la descripción original
    analysis_id = None
    for i, (s_name, s_seq, task_name) in enumerate(STAGES_CONFIG):
        task_vals = {
            "name": task_name,
            "project_id": project_id,
            "stage_id": stage_ids[i],
            "user_ids": [(4, uid)],
            "priority": "1" if i == 0 else "0",
        }
        if i == 0:
            task_vals["description"] = desc  # Descripción original solo en Análisis
        tid = models.execute_kw(db, uid, pwd, "project.task", "create", [task_vals])
        if i == 0:
            analysis_id = tid

    return project_id, analysis_id


def limpiar_fuente(models, task, project_id, analysis_id):
    db, uid, pwd = ODOO_DB, ODOO_UID, ODOO_PASS
    tid = task["id"]
    name = task["name"]
    nota = (
        f'<p>✅ <b>Proyecto creado por Dev Project Creator</b></p>'
        f'<p><b>Proyecto:</b> {name} (ID: {project_id})</p>'
        f'<p><b>Primera tarea:</b> "Análisis de requerimientos y alcance" (ID: {analysis_id})</p>'
    )

    if task["source"] == "incidencias":
        nota += "<p>Asignado cambiado a Maikel Guzman (anti-reprocesamiento).</p>"
        models.execute_kw(db, uid, pwd, "project.task", "write",
            [[tid], {"user_ids": [(6, 0, [uid])]}])
        models.execute_kw(db, uid, pwd, "project.task", "message_post",
            [[tid]], {"body": nota, "message_type": "comment",
                      "subtype_xmlid": "mail.mt_note"})
    elif task["source"] == "pote":
        nota += "<p>Tarea archivada. El trabajo continúa en el nuevo proyecto.</p>"
        models.execute_kw(db, uid, pwd, "project.task", "message_post",
            [[tid]], {"body": nota, "message_type": "comment",
                      "subtype_xmlid": "mail.mt_note"})
        nueva_desc = (task["description"] or "") + "\n\n---\n✅ creado como proyecto"
        models.execute_kw(db, uid, pwd, "project.task", "write",
            [[tid], {"active": False, "description": nueva_desc}])


def guardar_log(creados):
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "a") as f:
        for r in creados:
            f.write(
                f"- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] "
                f"Proyecto: \"{r['name']}\" (ID: {r['project_id']}) | "
                f"Fuente: {r['source']} tarea #{r['source_task_id']}\n"
            )


# ── HTML ──────────────────────────────────────────────────────────────────────

def build_project_card(r):
    badge_cls  = "badge-incidencias" if r["source"] == "incidencias" else "badge-pote"
    badge_txt  = "Incidencias TI" if r["source"] == "incidencias" else "Pote / Innovación"
    card_cls   = "" if r["source"] == "incidencias" else "from-pote"
    accion_txt = "Asignado reasignado a Maikel Guzman" if r["source"] == "incidencias" else "Tarea archivada con mensaje 'creado como proyecto'"
    tasks_html = "".join(
        f'<li>{task_name} <em style="color:#90a4ae;">— {s_name}</em></li>'
        for s_name, _, task_name in STAGES_CONFIG
    )
    return f"""
    <div class="project-card {card_cls}">
      <span class="badge-source {badge_cls}">{badge_txt}</span>
      <div class="proj-name">{r['name']}</div>
      <div class="meta">ID Odoo: <span>{r['project_id']}</span></div>
      <div class="meta">Tarea fuente: <span>#{r['source_task_id']}</span></div>
      <div class="meta">Tarea análisis: <span>#{r['analysis_id']}</span></div>
      <div class="meta">Tarea fuente: {accion_txt}</div>
      <ul class="task-list">{tasks_html}</ul>
    </div>"""


def build_error_card(e):
    return f"""
    <div class="project-card error">
      <div class="proj-name">Error — Tarea #{e['source_task_id']}</div>
      <div class="meta">Fuente: <span>{e['source']}</span></div>
      <div class="meta">Nombre: {e['name']}</div>
      <div class="meta" style="color:#c62828;">{e['error']}</div>
    </div>"""


def build_html(creados, errores, fecha_hora):
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # Bloque proyectos
    if creados:
        proyectos_bloque = "".join(build_project_card(r) for r in creados)
    else:
        proyectos_bloque = """
        <div class="empty-state">
          <span class="big">📭</span>
          No se encontraron tareas para convertir en proyectos en esta ronda.
        </div>"""

    # Bloque errores
    if errores:
        errores_bloque = f"""
        <div class="section-title" style="color:#c62828;">Errores en esta ronda</div>
        {"".join(build_error_card(e) for e in errores)}"""
    else:
        errores_bloque = ""

    html = html.replace("{{FECHA_HORA}}", fecha_hora)
    html = html.replace("{{TOTAL_CREADOS}}", str(len(creados)))
    html = html.replace("{{TOTAL_INCIDENCIAS}}", str(sum(1 for r in creados if r["source"] == "incidencias")))
    html = html.replace("{{TOTAL_POTE}}", str(sum(1 for r in creados if r["source"] == "pote")))
    html = html.replace("{{TOTAL_ERRORES}}", str(len(errores)))
    html = html.replace("{{PROYECTOS_BLOQUE}}", proyectos_bloque)
    html = html.replace("{{ERRORES_BLOQUE}}", errores_bloque)
    return html


def enviar_email(html, creados, errores, fecha_hora):
    total = len(creados)
    if total > 0:
        asunto = f"🏗️ Dev Project Creator — {total} proyecto(s) creado(s) · {fecha_hora}"
    elif errores:
        asunto = f"⚠️ Dev Project Creator — {len(errores)} error(es) · {fecha_hora}"
    else:
        asunto = f"✅ Dev Project Creator — Sin tareas pendientes · {fecha_hora}"

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
        return True
    except Exception as e:
        log(f"  ERROR al enviar email: {e}")
        return False


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    log("=" * 60)
    log(f"Dev Project Creator — inicio de ronda {fecha_hora}")

    models = odoo_models()
    creados = []
    errores = []

    # Leer ambas fuentes (directo via RPC — sin lag de réplica)
    log("Leyendo Incidencias TI (project=53, stage=703, usuario=Administrator)...")
    tareas_incidencias = leer_incidencias(models)
    log(f"  {len(tareas_incidencias)} tarea(s) encontrada(s)")

    log("Leyendo Pote (project=36, activas)...")
    tareas_pote = leer_pote(models)
    log(f"  {len(tareas_pote)} tarea(s) encontrada(s)")

    todas = tareas_incidencias + tareas_pote

    for task in todas:
        log(f"Procesando: [{task['source']}] #{task['id']} — {task['name']}")
        try:
            project_id, analysis_id = crear_proyecto(models, task)
            if project_id is None:
                continue  # Duplicado, ya logueado
            limpiar_fuente(models, task, project_id, analysis_id)
            result = {
                "name": task["name"],
                "project_id": project_id,
                "analysis_id": analysis_id,
                "source": task["source"],
                "source_task_id": task["id"],
            }
            creados.append(result)
            log(f"  ✅ Proyecto ID={project_id} creado")
        except Exception as e:
            log(f"  ❌ Error: {e}")
            errores.append({
                "source_task_id": task["id"],
                "name": task["name"],
                "source": task["source"],
                "error": str(e),
            })

    if creados:
        guardar_log(creados)

    log(f"Ronda finalizada: {len(creados)} creados, {len(errores)} errores")

    # Construir y enviar email del creator
    html = build_html(creados, errores, fecha_hora)
    enviar_email(html, creados, errores, fecha_hora)

    # ── Pasar testigo a dev-project-architect ────────────────────────────────
    if creados:
        project_ids = [str(r["project_id"]) for r in creados]
        log(f"Pasando testigo a dev-project-architect: proyectos {project_ids}")
        architect_path = os.path.normpath(ARCHITECT_SCRIPT)
        cmd = [sys.executable, architect_path] + project_ids
        try:
            subprocess.run(cmd, timeout=120)
            log("  ✅ dev-project-architect ejecutado")
        except Exception as e:
            log(f"  ⚠️  Error al invocar dev-project-architect: {e}")

    log("=" * 60)


if __name__ == "__main__":
    main()
