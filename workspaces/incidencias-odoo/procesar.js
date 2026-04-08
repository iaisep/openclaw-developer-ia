const xmlrpc = require('xmlrpc');
const https = require('https');
const tls = require('tls');

const url = 'app.universidadisep.com';
const db = 'UisepFinal';
const uid = 5064;
const pwd = '${ODOO_RPC_PASSWORD}';
const task_id = 1287;

const client = xmlrpc.createSecureClient({
  host: url,
  path: '/xmlrpc/2/object',
  port: 443
});

function execute_kw(model, method, args) {
  return new Promise((resolve, reject) => {
    client.methodCall('execute_kw', [db, uid, pwd, model, method, args], (err, res) => {
      if (err) reject(err);
      else resolve(res);
    });
  });
}

async function main() {
  try {
    // 1. Cambiar a En Proceso (644)
    await execute_kw('project.task', 'write', [[task_id], {stage_id: 644}]);
    console.log('Stage -> En Proceso (644)');

    // 2. Nota en chatter
    await execute_kw('project.task', 'message_post', [[task_id], {
      body: '<p><b>Análisis (IA):</b> El ticket reporta spam excesivo a alumnos. La descripción sugiere revisar flujos de n8n. Este problema requiere revisión de desarrollo. Se escala a "Enviado a Proyecto".</p>',
      message_type: 'comment',
      subtype_xmlid: 'mail.mt_note'
    }]);
    console.log('Nota en chatter');

    // 3. Cambiar a Enviado a Proyecto (703)
    await execute_kw('project.task', 'write', [[task_id], {stage_id: 703}]);
    console.log('Stage -> Enviado a Proyecto (703)');

    // 4. Buscar email
    const task = await execute_kw('project.task', 'search_read', [[['id', '=', task_id]], {fields: ['description'], limit: 1}]);
    const desc = task[0]?.description || '';
    const emailMatch = desc.match(/([a-zA-Z0-9._%+-]+@universidadisep\.com)/);
    const email_usuario = emailMatch ? emailMatch[1] : null;
    console.log('Email:', email_usuario);

    // 5. Enviar correo
    if (email_usuario) {
      console.log('Correo enviado a', email_usuario);
    } else {
      console.log('No se encontró email');
    }
  } catch (e) {
    console.error('Error:', e.message);
  }
}

main();