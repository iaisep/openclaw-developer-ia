# SKILL: revertir-devmain

## Descripción
Revierte la rama `DEVMain_Latest` al último commit de `main` en GitHub.
Se usa cuando hay commits incorrectos, no autorizados o problemáticos en `DEVMain_Latest` que deben eliminarse antes de continuar el pipeline de desarrollo.

## ⚠️ Invocación — SOLO HUMANO
Esta skill **NUNCA debe ejecutarse de forma automática** por heartbeat, cron, ni por invocación de otro agente.
Solo puede ejecutarse cuando un humano lo solicita explícitamente con frases como:
- "revertir DEVMain_Latest"
- "resetear la rama de dev a main"
- "limpiar DEVMain_Latest"
- "ejecutar skill revertir-devmain"

**Si no hay instrucción humana explícita → NO ejecutar.**

---

## Procedimiento

### Paso 1 — Confirmar con el usuario antes de ejecutar

Antes de cualquier acción, reportar al agente `main` para que el usuario confirme:

```bash
openclaw agent --agent main --message "⚠️ [devops-odoo] SKILL revertir-devmain — CONFIRMACIÓN REQUERIDA.

Voy a revertir DEVMain_Latest al último commit de main.
Esto eliminará TODOS los commits de DEVMain_Latest que no estén en main.

¿Confirmas? Responde 'sí, revertir' para proceder."
```

**DETENER y esperar confirmación. No continuar sin respuesta afirmativa.**

---

### Paso 2 — Obtener el último commit de main via GitHub API

```bash
curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
  "https://api.github.com/repos/Universidad-ISEP/Odoo16UISEP/branches/main" \
  | python3 -c "
import sys, json
d = json.loads(sys.stdin.read())
sha = d['commit']['sha']
msg = d['commit']['commit']['message'].splitlines()[0]
date = d['commit']['commit']['committer']['date']
print(f'SHA:  {sha}')
print(f'MSG:  {msg}')
print(f'DATE: {date}')
"
```

Reportar el SHA y mensaje al usuario antes de continuar.

---

### Paso 3 — Verificar commits que se perderán

```bash
curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
  "https://api.github.com/repos/Universidad-ISEP/Odoo16UISEP/compare/main...DEVMain_Latest" \
  | python3 -c "
import sys, json
d = json.loads(sys.stdin.read())
ahead = d['ahead_by']
if ahead == 0:
    print('DEVMain_Latest ya está al día con main. No hay nada que revertir.')
else:
    print(f'Commits que se eliminarán ({ahead}):')
    for c in d['commits']:
        sha = c['sha'][:7]
        msg = c['commit']['message'].splitlines()[0]
        print(f'  - {sha} {msg}')
"
```

Si `ahead_by == 0` → informar que no hay nada que hacer y terminar.

---

### Paso 4 — Ejecutar el reset en el servidor .57

```bash
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "cd /home/maikel/github/Odoo16UISEP_DEVMain && \
   git fetch origin && \
   git checkout DEVMain_Latest && \
   git reset --hard origin/main && \
   echo 'Reset local OK' && \
   git log --oneline -3"
```

---

### Paso 5 — Force push

```bash
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "cd /home/maikel/github/Odoo16UISEP_DEVMain && \
   git push --force origin DEVMain_Latest && \
   echo 'Force push OK' && \
   git log --oneline origin/DEVMain_Latest -3"
```

---

### Paso 6 — Verificar resultado via API

```bash
curl -s -H "Authorization: token ${GITHUB_TOKEN}" \
  "https://api.github.com/repos/Universidad-ISEP/Odoo16UISEP/compare/main...DEVMain_Latest" \
  | python3 -c "
import sys, json
d = json.loads(sys.stdin.read())
print('ahead_by:', d['ahead_by'])
print('behind_by:', d['behind_by'])
if d['ahead_by'] == 0:
    print('✅ DEVMain_Latest está sincronizada con main.')
else:
    print('⚠️ Aún hay diferencias — verificar manualmente.')
"
```

---

### Paso 7 — Registrar en memoria y notificar

Guardar entrada en `memory/YYYY-MM-DD.md`:

```markdown
### HH:MM — SKILL revertir-devmain ejecutada
- **Motivo:** <motivo indicado por el usuario>
- **Commits eliminados:** <lista sha + mensaje>
- **SHA destino (main):** <sha>
- **Resultado:** ✅ DEVMain_Latest sincronizada con main
```

Notificar resultado al agente `main`:

```bash
openclaw agent --agent main --message "✅ [devops-odoo] SKILL revertir-devmain completada.

DEVMain_Latest fue revertida al commit de main: <sha_corto> — <mensaje>
Commits eliminados: <N>
  <lista de commits eliminados>

La rama está limpia y lista para nuevos desarrollos."
```

---

## Errores comunes

| Error | Causa probable | Acción |
|-------|---------------|--------|
| `Permission denied` en SSH | Llave `/.keys/odoo-dev.pem` sin permisos | `chmod 400 /.keys/odoo-dev.pem` |
| `! [rejected]` en force push | GitHub tiene protección de rama | Verificar si `DEVMain_Latest` tiene branch protection |
| `ahead_by` sigue > 0 después del push | El push no se aplicó | Verificar el remote con `git log origin/DEVMain_Latest` |
| SSH timeout | Servidor .57 no disponible | Verificar conectividad con `ping 189.195.191.16` |
