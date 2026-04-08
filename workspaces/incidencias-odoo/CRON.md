# CRON — Incidencias Odoo

## Cron activo: `incidencias-autonomas`

- **ID:** `525ef564-9e1e-4a91-868c-102180bb06bc`
- **Frecuencia:** cada 30 minutos
- **Modelo:** `minimax-portal/MiniMax-M2.5`
- **Sesión:** aislada (no contamina el chat principal)
- **Entrega:** silenciosa (sin anuncio al chat)

## Qué procesa este cron

Solo atiende tickets del proyecto 53 en stage **Pendiente (564)** que coincidan con:

| Tipo | Palabras clave en la descripción |
|---|---|
| **FUSIÓN DE DUPLICADOS** | duplicado, dos perfiles, dos cuentas, dos usuarios, no puede ver, perfil incorrecto, datos divididos |
| **CORRECCIÓN DE CREDENCIAL** | credencial, programa incorrecto, muestra programa antiguo, carnet, diploma incorrecto |

Tickets de otro tipo se dejan en Pendiente sin tocar.

## Qué hace con cada ticket clasificado

1. Cambia stage a **En Proceso (644)**
2. Carga la skill correspondiente y ejecuta el procedimiento completo
3. Nota en chatter con el resultado
4. Envía correo al usuario (email extraído de la descripción)
5. Mueve a **Listo (565)** o **Enviado a Proyecto (703)** según resultado

## Cómo ejecutarlo bajo demanda (desde el agente main)

El agente `main` puede disparar este cron inmediatamente sin esperar los 30 minutos:

```bash
# Desde el agente main via tool exec:
docker exec openclaw-developer-ia openclaw cron run 525ef564-9e1e-4a91-868c-102180bb06bc \
  --url ws://127.0.0.1:18789 \
  --token dfd6c9d67514ecaefbcd80bd81dd8c39f18eb172cbefeed5b87211b39673b0bc
```

O delegando directamente al agente `incidencias-odoo` via `sessions_send`.

## Cómo agregar nuevos tipos de ticket

Cuando se agreguen nuevas skills al agente, actualizar el mensaje del cron:

```bash
docker exec openclaw-developer-ia openclaw cron edit 525ef564-9e1e-4a91-868c-102180bb06bc \
  --message "<nuevo prompt con tipos adicionales>" \
  --url ws://127.0.0.1:18789 \
  --token dfd6c9d67514ecaefbcd80bd81dd8c39f18eb172cbefeed5b87211b39673b0bc
```

## Ver historial de ejecuciones

```bash
docker exec openclaw-developer-ia openclaw cron runs 525ef564-9e1e-4a91-868c-102180bb06bc \
  --url ws://127.0.0.1:18789 \
  --token dfd6c9d67514ecaefbcd80bd81dd8c39f18eb172cbefeed5b87211b39673b0bc
```
