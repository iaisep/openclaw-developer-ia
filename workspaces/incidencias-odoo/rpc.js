const https = require('https');

const URL = 'app.universidadisep.com';
const DB = 'UisepFinal';
const UID = 5064;
const PWD = '${ODOO_RPC_PASSWORD}';

function rpc(method, model, methodName, args) {
  const xml = `<?xml version="1.0"?>
<methodCall>
  <methodName>${method}</methodName>
  <params>
    <param><value><string>${DB}</string></value></param>
    <param><value><int>${UID}</int></value></param>
    <param><value><string>${PWD}</string></value></param>
    <param><value><string>${model}</string></value></param>
    <param><value><string>${methodName}</string></value></param>
    ${args}
  </params>
</methodCall>`;

  return new Promise((resolve, reject) => {
    const req = https.request({
      hostname: URL,
      path: '/xmlrpc/2/object',
      method: 'POST',
      headers: { 'Content-Type': 'application/xml', 'Content-Length': Buffer.byteLength(xml) }
    }, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve(data));
    });
    req.on('error', reject);
    req.write(xml);
    req.end();
  });
}

async function main() {
  const task_id = 1287;
  
  // 1. Cambiar a En Proceso (644)
  let res = await rpc('execute_kw', 'project.task', 'write', 
    `<param><value><array><data><value><array><data><value><int>${task_id}</int></value></data></array></value></data></array></param><param><value><struct><member><name>stage_id</name><value><int>644</int></value></member></struct></value></param>`);
  console.log('Stage 644:', res.slice(0, 200));

  // 2. Nota chatter
  res = await rpc('execute_kw', 'project.task', 'message_post',
    `<param><value><array><data><value><array><data><value><int>${task_id}</int></value></data></array></value></data></array></param><param><value><struct><member><name>body</name><value><string>&lt;p&gt;&lt;b&gt;Análisis (IA):&lt;/b&gt; Spam excesivo a alumnos. Requiere revisión de flujos n8n/desarrollo. Se escala a "Enviado a Proyecto".&lt;/p&gt;</value></member><member><name>message_type</name><value><string>comment</string></member><member><name>subtype_xmlid</name><value><string>mail.mt_note</string></member></struct></value></param>`);
  console.log('Chatter:', res.slice(0, 200));

  // 3. Cambiar a Enviado a Proyecto (703)
  res = await rpc('execute_kw', 'project.task', 'write',
    `<param><value><array><data><value><array><data><value><int>${task_id}</int></value></data></array></value></data></array></param><param><value><struct><member><name>stage_id</name><value><int>703</int></value></member></struct></value></param>`);
  console.log('Stage 703:', res.slice(0, 200));
}

main().catch(console.error);