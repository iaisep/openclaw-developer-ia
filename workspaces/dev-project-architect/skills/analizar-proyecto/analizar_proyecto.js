#!/usr/bin/env node
/**
 * analizar_proyecto.js — Dev Project Architect (Node.js version)
 * Analiza proyectos y asigna etiqueta de herramienta.
 */
const https = require('https');
const fs = require('fs');
const path = require('path');

// Configuración
const ODOO_URL = "app.universidadisep.com";
const ODOO_DB = "UisepFinal";
const ODOO_UID = 5064;
const ODOO_PASS = "${ODOO_RPC_PASSWORD}";

const SMTP_HOST = "email-smtp.us-east-1.amazonaws.com";
const SMTP_PORT = 587;
const SMTP_USER = "AKIA5TSAYHSG3OD7XYK3";
const SMTP_PASS = "BPMhIBG4+f4qfob+msLNNH9pYBlB74ERNi/cKXL1N+WI";
const FROM_EMAIL = "mguzman@universidadisep.com";
const RECIPIENTS = [
    "iallamadas@universidadisep.com",
    "automatizacion02@universidadisep.com",
    "automatizacion03@universidadisep.com",
    "automatizacion04@universidadisep.com",
    "automatizacion05@universidadisep.com",
    "automatizacion06@universidadisep.com",
    "automatizacion07@universidadisep.com",
    "automatizacion08@universidadisep.com",
    "automatizacion09@universidadisep.com",
];

const TOOL_TAGS = {
    'n8n': 24, 'odoo': 25, 'chatwoot': 26,
    'mautic': 27, 'wordpress': 28, 'desarrollos-apis': 29
};
const TOOL_TAG_IDS = new Set(Object.values(TOOL_TAGS));

const TOOL_EMOJIS = {
    'n8n': '🔄', 'odoo': '🟣', 'chatwoot': '💬',
    'mautic': '📧', 'wordpress': '🌐', 'desarrollos-apis': '🔌'
};

const ODOO_WARNINGS = "Odoo 16 presenta: OOM Kill por alta presión de memoria, workers idle bloqueados sin liberación, procesos en fallo ejecutándose recursivamente, sobrecarga por módulos slide/mail/livechat, y memoria compartida entre Postgres, Redis y Odoo sin aislamiento.";

// Utilidades
const log = (msg) => {
    const ts = new Date().toISOString().replace('T', ' ').substring(0, 19);
    console.log(`[${ts}] ${msg}`);
};

const stripHtml = (html) => html ? html.replace(/<[^>]+>/g, ' ').trim() : '';

// Llamadas a Odoo
const odooCall = (model, method, args, kwargs = {}) => {
    return new Promise((resolve, reject) => {
        const payload = JSON.stringify({
            jsonrpc: "2.0",
            method: "call",
            params: { model, method, args, kwargs },
            id: Math.floor(Math.random() * 1000000)
        });

        const options = {
            hostname: ODOO_URL,
            path: "/xmlrpc/2/object",
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Content-Length": Buffer.byteLength(payload)
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const json = JSON.parse(data);
                    if (json.error) reject(new Error(json.error.message || JSON.stringify(json.error)));
                    else resolve(json.result);
                } catch (e) { reject(e); }
            });
        });

        req.on('error', reject);
        req.write(payload);
        req.end();
    });
};

// Decidir herramienta
const decidirHerramienta = (nombre, descTexto) => {
    const texto = (nombre + ' ' + descTexto).toLowerCase();

    const n8n_keywords = ['automatiz', 'sincroniz', 'integrac', 'flujo', 'webhook', 'trigger', 'pipeline', 'cron', 'notificac', 'programad', 'n8n', 'schedule', 'procesamiento', 'batch', 'masiv', 'importar', 'exportar', 'log', 'monitoreo'];
    const odoo_keywords = ['formulario odoo', 'vista odoo', 'módulo odoo', 'modelo odoo', 'campo odoo', 'reporte odoo', 'factura', 'inventario', 'venta', 'compra', 'contabilidad', 'nómina', 'rh odoo', 'erp'];
    const chatwoot_keywords = ['chat', 'conversac', 'bandeja', 'whatsapp', 'soporte', 'atencion', 'ticket soporte', 'bot atencion', 'agente'];
    const mautic_keywords = ['campaña', 'email marketing', 'lead', 'embudo', 'nutricion', 'nutrición', 'segmentac', 'scoring', 'marketing', 'captacion', 'mautic'];
    const wordpress_keywords = ['sitio web', 'landing', 'portal', 'wordpress', 'pagina web', 'página web', 'blog', 'contenido público', 'formulario captacion'];

    const scores = { n8n: 0, odoo: 0, chatwoot: 0, mautic: 0, wordpress: 0, 'desarrollos-apis': 0 };

    n8n_keywords.forEach(kw => { if (texto.includes(kw)) scores.n8n += 2; });
    odoo_keywords.forEach(kw => { if (texto.includes(kw)) scores.odoo += 1; });
    chatwoot_keywords.forEach(kw => { if (texto.includes(kw)) scores.chatwoot += 2; });
    mautic_keywords.forEach(kw => { if (texto.includes(kw)) scores.mautic += 2; });
    wordpress_keywords.forEach(kw => { if (texto.includes(kw)) scores.wordpress += 2; });

    // Penalizar odoo si hay señales de automatización
    if (scores.n8n > 0 && scores.odoo > 0) scores.odoo = Math.max(0, scores.odoo - scores.n8n);

    let ganador = Object.keys(scores).reduce((a, b) => scores[a] > scores[b] ? a : b);
    if (scores[ganador] === 0) ganador = 'desarrollos-apis';

    const justificaciones = {
        n8n: "La descripción indica un flujo de automatización, sincronización o integración entre sistemas. n8n permite modelar este tipo de lógica como nodos visuales, con menor consumo de recursos que implementarlo dentro de Odoo.",
        odoo: "La funcionalidad requiere acceso directo a modelos de datos de Odoo con transacciones ACID y no puede desacoplarse del ERP.",
        chatwoot: "La descripción involucra gestión de conversaciones, atención al cliente o canales de comunicación. Chatwoot es la herramienta especializada del stack.",
        mautic: "La descripción corresponde a automatizaciones de marketing, campañas de email, embudos de leads o segmentación de contactos.",
        wordpress: "La descripción menciona contenido web, landing pages o portales públicos. WordPress es la herramienta adecuada.",
        'desarrollos-apis': "La descripción no encaja claramente en ninguna herramienta específica del stack, o requiere una integración personalizada."
    };

    const nota_odoo_map = {
        n8n: "Se descarta implementar en Odoo: el flujo añadiría carga de CPU/memoria a workers ya presionados.",
        odoo: `⚠️ Se asignó Odoo por necesidad. ${ODOO_WARNINGS}`,
        chatwoot: "Se descarta Odoo: añadiría dependencia del módulo im_livechat, conocido por su alto consumo de memoria.",
        mautic: "Se descarta Odoo: la lógica de marketing masivo generaría colas de email que sobrecargarían el módulo mail.",
        wordpress: "Se descarta Odoo: gestionar contenido web dentro del ERP no es su dominio.",
        'desarrollos-apis': "Se descarta Odoo como primera opción: una API independiente permite escalar sin afectar el entorno monolítico."
    };

    return { herramienta: ganador, justificacion: justificaciones[ganador], nota_odoo: nota_odoo_map[ganador] };
};

// Analizar proyecto
const analizarProyecto = async (projectId) => {
    log(`Analizando proyecto ID=${projectId}...`);

    // Leer proyecto
    const proj = await odooCall('project.project', 'read', [[projectId], ['id', 'name', 'description', 'tag_ids']]);
    if (!proj || proj.length === 0) throw new Error(`Proyecto ${projectId} no encontrado`);
    const nombre = proj[0].name;
    const tagIds = proj[0].tag_ids || [];

    // Verificar que no tenga etiqueta de herramienta
    if ([...tagIds].some(id => TOOL_TAG_IDS.has(id))) {
        log(`  SKIP ${projectId}: ya tiene etiqueta de herramienta`);
        return null;
    }

    // Leer tarea de análisis
    const tareas = await odooCall('project.task', 'search_read', [[['project_id', '=', projectId], ['name', '=', 'Análisis de requerimientos y alcance']], ['description']]);
    const descTarea = tareas.length > 0 ? stripHtml(tareas[0].description) : '';
    const descCompleta = stripHtml(proj[0].description || '') + ' ' + descTarea;

    // Notificar inicio
    await odooCall('project.project', 'message_post', [[projectId], { body: '<p>🏛️ <b>Dev Project Architect</b> — Iniciando análisis de herramienta tecnológica...</p>', message_type: 'comment', subtype_xmlid: 'mail.mt_note' }]);

    // Decidir
    const { herramienta, justificacion, nota_odoo } = decidirHerramienta(nombre, descCompleta);
    const tagId = TOOL_TAGS[herramienta];
    const emoji = TOOL_EMOJIS[herramienta];

    // Asignar etiqueta
    await odooCall('project.project', 'write', [[projectId], { tag_ids: [[4, tagId]] }]);

    // Documentar decisión
    await odooCall('project.project', 'message_post', [[projectId], {
        body: `<p>${emoji} <b>Herramienta recomendada: ${herramienta.toUpperCase()}</b></p><hr/><p><b>Justificación técnica:</b><br/>${justificacion}</p><br/><p><b>Consideraciones Odoo 16:</b><br/><em>${nota_odoo}</em></p>`,
        message_type: 'comment', subtype_xmlid: 'mail.mt_note'
    }]);

    log(`  ✅ '${nombre}' (ID:${projectId}) → ${herramienta}`);
    return { project_id: projectId, name: nombre, herramienta, emoji, justificacion, nota_odoo };
};

// Main
(async () => {
    const fechaHora = new Date().toLocaleString('es-CO', { timeZone: 'America/Bogota' });
    log("=".repeat(60));
    log(`Dev Project Architect — inicio de ronda ${fechaHora}`);

    try {
        // Buscar proyectos pendientes
        const todos = await odooCall('project.project', 'search_read', [[['active', '=', true], ['tag_ids', 'in', [1]]], ['id', 'tag_ids']]);
        const pendientes = todos.filter(p => ![...p.tag_ids || []].some(id => TOOL_TAG_IDS.has(id)));
        const ids = pendientes.map(p => p.id);

        log(`Proyectos pendientes encontrados: ${ids.length}`);

        const resultados = [];
        const errores = [];

        for (const pid of ids) {
            try {
                const r = await analizarProyecto(pid);
                if (r) resultados.push(r);
            } catch (e) {
                log(`  ERROR proyecto ${pid}: ${e.message}`);
                errores.push({ project_id: pid, error: e.message });
            }
        }

        log(`Ronda finalizada: ${resultados.length} analizados, ${errores.length} errores`);
        // Nota: enviar email requiere paquete smtp adicional, omitido en esta versión

    } catch (e) {
        log(`Error fatal: ${e.message}`);
    }

    log("=".repeat(60));
})();