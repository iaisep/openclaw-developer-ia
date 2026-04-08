# Reglas — Dev Distrib Local

1. SIEMPRE leer `CAMBIOS.md` del módulo antes de copiar cualquier archivo.
2. Si existe `CAMBIOS.md`, usarlo como descripción del commit. Si no existe pero hay archivos válidos (`.py`, `.xml`, `.csv`, `.json`), continuar el proceso igualmente — generar el mensaje del commit a partir del nombre del módulo y los archivos detectados.
3. SIEMPRE hacer `git pull origin DEVMain_Latest` antes de copiar, para evitar conflictos.
4. SIEMPRE revisar `git diff --stat` antes del commit — si el diff no coincide con CAMBIOS.md, no hacer commit y reportar.
5. NUNCA hacer commit de archivos fuera de `addons-extra/addons_uisep/` salvo que el usuario lo indique explícitamente.
6. NUNCA forzar push (`--force`) a `DEVMain_Latest`.
7. El mensaje del commit DEBE reflejar el contenido de `CAMBIOS.md` — no inventar descripciones genéricas.
8. Después de cada push exitoso, MOVER los archivos procesados a `_procesados/YYYY-MM-DD_HHMM/`. No eliminar.
9. Si hay conflictos de merge, NO resolverlos automáticamente — reportar al usuario con el detalle del conflicto.
10. Si el módulo destino no existe en el repo, verificar con el usuario antes de crearlo.
11. Procesar un módulo a la vez para facilitar el diagnóstico en caso de error.
12. Registrar en `memory/YYYY-MM-DD.md` cada push realizado con módulo, archivos y hash del commit.
