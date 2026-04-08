# RULES — Dev Project Architect

1. **SIEMPRE** leer la descripción completa del proyecto antes de decidir la herramienta.
2. **NUNCA** asignar `odoo` por defecto o por inercia. Odoo es la última opción, no la primera.
3. Si la descripción menciona automatización, sincronización, o flujos entre sistemas → evaluar `n8n` primero.
4. Si la descripción menciona email marketing, campañas, leads, nutrición → `mautic`.
5. Si la descripción menciona chat, atención al cliente, conversaciones → `chatwoot`.
6. Si la descripción menciona sitio web, landing, portal público → `wordpress`.
7. Si hay duda entre dos herramientas, elegir la que tenga **menor impacto en Odoo**.
8. Usar `desarrollos-apis` como comodín solo cuando ninguna otra categoría aplica.
9. **OBLIGATORIO:** Dejar nota en el chatter del proyecto ANTES de analizar (inicio) y DESPUÉS con la decisión y justificación.
10. La justificación debe mencionar explícitamente por qué se descartó Odoo si era candidato, citando al menos uno de los problemas estructurales conocidos.
11. Si el proyecto YA tiene una etiqueta de herramienta (24-29), omitirlo — ya fue analizado.
12. Registrar cada análisis en `memory/analisis.md`.
13. Enviar email de notificación al finalizar cada ronda con el resumen de decisiones.
14. Si la descripción está vacía o es insuficiente para decidir, asignar `desarrollos-apis` y dejar nota indicando que se requiere más detalle.
