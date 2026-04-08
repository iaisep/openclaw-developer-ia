#!/usr/bin/env python3
import xmlrpc.client, ssl

ODOO_URL  = "https://dev.odoo.universidadisep.com"
ODOO_DB   = "final"
ODOO_USER = "iallamadas@universidadisep.com"
ODOO_PASS = "${ODOO_RPC_PASSWORD}"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common", context=ctx)
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object", context=ctx)

# Buscar el modulo
modulos = models.execute_kw(ODOO_DB, uid, ODOO_PASS,
    'ir.module.module', 'search_read',
    [[['name', '=', 'isep_enfas_isep_enfas_adicional']]],
    {'fields': ['id', 'name', 'state', 'installed_version']}
)

print("=== Resultado busqueda exacta ===")
print(modulos)

# Si no encontrado, buscar con ilike
if not modulos:
    modulos2 = models.execute_kw(ODOO_DB, uid, ODOO_PASS,
        'ir.module.module', 'search_read',
        [[['name', 'ilike', 'enfas']]],
        {'fields': ['id', 'name', 'state', 'installed_version'], 'limit': 10}
    )
    print("\n=== Resultado busqueda ilike enfas ===")
    print(modulos2)