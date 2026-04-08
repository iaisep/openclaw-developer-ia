# RULES — Dev Project Creator

1. **SIEMPRE** leer la descripción completa de la tarea fuente antes de crear el proyecto.
2. **Incidencias TI:** Solo procesar tareas en stage 703 donde el asignado sea **exclusivamente** el usuario Administrator (id=2). Si hay otros asignados o ninguno, omitir.
3. **NUNCA** crear un proyecto duplicado. Antes de crear, verificar que no exista ya un proyecto con el mismo nombre via `search_count`.
4. El primer stage de cada proyecto nuevo siempre es **"Análisis"** y la primera tarea siempre es **"Análisis de requerimientos y alcance"**.
5. La descripción de la tarea "Análisis de requerimientos y alcance" debe ser **idéntica** a la descripción de la tarea fuente, sin modificaciones.
6. **Incidencias TI:** Después de crear el proyecto, reasignar la tarea fuente a Maikel Guzman (id=5064). Esto evita que la misma tarea sea procesada en futuras rondas.
7. **Pote:** Después de crear el proyecto, archivar la tarea fuente (`active=False`) y agregar el texto `creado como proyecto` a su descripción.
8. **SIEMPRE** dejar nota en el chatter de la tarea fuente (Incidencias TI o Pote) indicando qué proyecto fue creado y con qué ID.
9. **NUNCA** modificar ni borrar la tarea fuente sin antes haber creado el proyecto exitosamente.
10. Si la creación del proyecto falla (error RPC), NO modificar la tarea fuente. Registrar el error y omitir esa tarea.
11. Los stages del proyecto nuevo deben crearse siempre en este orden: Análisis → Diseño → Desarrollo → Pruebas / QA → Producción → Cerrado.
12. El PM del proyecto nuevo es siempre Maikel Guzman (id=5064).
13. Guardar en `memory/` un log de proyectos creados en cada ronda de ejecución.
