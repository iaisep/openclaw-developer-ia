# Reglas — Incidencias Odoo

1. SIEMPRE leer la descripción completa del ticket antes de actuar.
2. SIEMPRE hacer `search_read` para verificar datos antes de cualquier `write`.
3. NUNCA ejecutar `unlink` sin confirmación explícita del usuario.
4. Toda acción tomada debe quedar registrada en el chatter del ticket via `message_post`.
5. Si la resolución requiere código → mover a "Enviado a Proyecto" con nota técnica detallada.
6. NUNCA mover un ticket de "Enviado a Proyecto" de regreso a "Pendiente" sin autorización.
7. Procesar tickets en orden de prioridad (alta primero, luego media, luego baja).
8. Si no se puede resolver un ticket (error RPC, datos insuficientes), dejar nota en chatter y mantener en Pendiente.
9. Guardar en memory/ un log diario de tickets atendidos.
10. Las escrituras van a producción via XML-RPC (`app.universidadisep.com`). La réplica `.57` es solo lectura para diagnóstico.
11. **OBLIGATORIO:** Cada vez que se cambie el stage de un ticket, cargar y ejecutar la skill `notificacion-incidencia` para notificar al usuario por correo. Sin excepción — aplica a todos los stages: En Proceso (644), Listo (565), Enviado a Proyecto (703), En Revisión (567).
