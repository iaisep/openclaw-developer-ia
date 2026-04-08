# Tools — Dev Distrib Local

## Carpeta de entrada (acceso directo en el container)

```
/mnt/cambios-odoo-local/          ← /home/maikel/cambios_odoo_local en el host
```

## Repo Git en servidor DEV

```
Servidor:   189.195.191.16
SSH key:    /.keys/odoo-dev.pem
Repo:       /home/maikel/github/Odoo16UISEP_DEVMain
Addons:     /home/maikel/github/Odoo16UISEP_DEVMain/addons-extra/addons_uisep
Rama:       DEVMain_Latest
```

## GitHub

```
Token:      ${GITHUB_TOKEN}
Repo:       Universidad-ISEP/Odoo16UISEP
Rama:       DEVMain_Latest
Remote URL: https://${GITHUB_TOKEN}@github.com/Universidad-ISEP/Odoo16UISEP.git
```

## Comandos frecuentes

```bash
# Listar módulos pendientes en la carpeta de entrada
ls /mnt/cambios-odoo-local/

# Leer CAMBIOS.md de un módulo
cat /mnt/cambios-odoo-local/<modulo>/CAMBIOS.md

# SSH al servidor DEV
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 "<cmd>"

# Sincronizar repo DEV antes de copiar
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "cd /home/maikel/github/Odoo16UISEP_DEVMain && git fetch origin DEVMain_Latest && git pull origin DEVMain_Latest"

# Copiar archivo al repo DEV
scp -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem \
  /mnt/cambios-odoo-local/<modulo>/<ruta>/<archivo> \
  root@189.195.191.16:/home/maikel/github/Odoo16UISEP_DEVMain/addons-extra/addons_uisep/<modulo>/<ruta>/<archivo>

# Ver diff antes del commit
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "cd /home/maikel/github/Odoo16UISEP_DEVMain && git diff --stat"

# Commit y push
ssh -o StrictHostKeyChecking=no -i /.keys/odoo-dev.pem root@189.195.191.16 \
  "cd /home/maikel/github/Odoo16UISEP_DEVMain && \
   git config user.email 'dev-distrib@universidadisep.com' && \
   git config user.name 'Dev Distrib Local' && \
   git add addons-extra/addons_uisep/<modulo>/ && \
   git commit -m '<mensaje>' && \
   git push https://${GITHUB_TOKEN}@github.com/Universidad-ISEP/Odoo16UISEP.git DEVMain_Latest"

# Mover módulo procesado
mkdir -p /mnt/cambios-odoo-local/_procesados/$(date +%Y-%m-%d_%H%M)
mv /mnt/cambios-odoo-local/<modulo> /mnt/cambios-odoo-local/_procesados/$(date +%Y-%m-%d_%H%M)/
```

## Git config (identidad para commits)

```
user.email  dev-distrib@universidadisep.com
user.name   Dev Distrib Local
```
