"""
Seed de datos para Chill Out La Bodeguita.

Uso:
    python seed.py                 # Catálogo base + datos de demostración
    python seed.py --solo-catalogo # Solo catálogo (productos, proveedores, empleados, admin)

Es idempotente: se puede ejecutar tantas veces como se quiera sin duplicar datos.
Los datos demo (cierres, conteos, pedidos) se regeneran con fechas relativas al día actual.
"""

import os
import sys
from datetime import date, timedelta
from decimal import Decimal

sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from caja.models import CierreCaja, Empleado, PagoPersonal
from inventario.models import Categoria, ConteoStock, ConteoStockLinea, Producto, Proveedor
from pedidos.models import Pedido, PedidoLinea

User = get_user_model()

SOLO_CATALOGO = '--solo-catalogo' in sys.argv

# ---------------------------------------------------------------- catálogo base
CATEGORIAS = [
    ('Rones', 1), ('Whiskys', 2), ('Ginebras', 3), ('Licores y Otros', 4),
    ('Refrescos y Mezcladores', 5), ('Cachimbas / Shishas', 6), ('Mojitos y Varios', 7),
]

PROVEEDORES = [
    ('Distribución de Bebidas', 'Tel: 957 000 001 · comercial@distribuciones.es'),
    ('Tabacos y Cachimbas', 'Tel: 957 000 002 · compras@tabacoscabra.es'),
    ('Hielo y Varios', 'Tel: 957 000 003 · pedidos@hielovarios.es'),
]

PRODUCTOS = [
    # (nombre, categoria, proveedor, unidad, stock_minimo, stock_actual, es_alcohol, precio_copa, copas)
    ('Ron Barceló', 'Rones', 0, 'botella', 12, 20, True, 8.00, 8),
    ('Ron Legendario', 'Rones', 0, 'botella', 8, 10, True, 8.00, 8),
    ('Ron Negrita', 'Rones', 0, 'botella', 8, 6, True, 7.00, 8),
    ('Ron Brugal', 'Rones', 0, 'botella', 6, 9, True, 8.00, 8),
    ('Ron Havana Club 7', 'Rones', 0, 'botella', 6, 10, True, 9.00, 8),
    ('Johnnie Walker Red Label', 'Whiskys', 0, 'botella', 8, 12, True, 8.00, 8),
    ('Johnnie Walker Black Label', 'Whiskys', 0, 'botella', 6, 8, True, 9.00, 8),
    ("J&B", 'Whiskys', 0, 'botella', 8, 5, True, 8.00, 8),
    ("Ballantine's", 'Whiskys', 0, 'botella', 8, 11, True, 8.00, 8),
    ("Cutty Sark", 'Whiskys', 0, 'botella', 6, 7, True, 8.00, 8),
    ('Beefeater', 'Ginebras', 0, 'botella', 10, 15, True, 8.00, 8),
    ('Larios', 'Ginebras', 0, 'botella', 12, 9, True, 8.00, 8),
    ('Larios 12', 'Ginebras', 0, 'botella', 8, 13, True, 9.00, 8),
    ("Seagram's", 'Ginebras', 0, 'botella', 6, 4, True, 8.00, 8),
    ('Tanqueray', 'Ginebras', 0, 'botella', 6, 8, True, 9.00, 8),
    ('Puerto de Indias', 'Ginebras', 0, 'botella', 10, 16, True, 8.00, 8),
    ('Licor 43', 'Licores y Otros', 0, 'botella', 6, 7, True, 8.00, 8),
    ('Vodka', 'Licores y Otros', 0, 'botella', 8, 10, True, 8.00, 8),
    ('Vodka Caramelo', 'Licores y Otros', 0, 'botella', 6, 4, True, 8.00, 8),
    ('Jägermeister', 'Licores y Otros', 0, 'botella', 6, 5, True, 8.00, 8),
    ('Tequila de Fresa', 'Licores y Otros', 0, 'botella', 4, 3, True, 8.00, 8),
    ('Coca-Cola', 'Refrescos y Mezcladores', 0, 'botellin', 100, 80, False, None, 0),
    ('Coca-Cola Zero', 'Refrescos y Mezcladores', 0, 'botellin', 50, 60, False, None, 0),
    ('Fanta Limón', 'Refrescos y Mezcladores', 0, 'botellin', 40, 20, False, None, 0),
    ('Fanta Naranja', 'Refrescos y Mezcladores', 0, 'botellin', 40, 30, False, None, 0),
    ('Aquarius Limón', 'Refrescos y Mezcladores', 0, 'botellin', 30, 15, False, None, 0),
    ('Aquarius Naranja', 'Refrescos y Mezcladores', 0, 'botellin', 30, 28, False, None, 0),
    ('Nestea', 'Refrescos y Mezcladores', 0, 'botellin', 30, 12, False, None, 0),
    ('Nestea Maracuyá', 'Refrescos y Mezcladores', 0, 'botellin', 20, 22, False, None, 0),
    ('Zumo de Piña', 'Refrescos y Mezcladores', 0, 'botellin', 20, 10, False, None, 0),
    ('Agua Mineral', 'Refrescos y Mezcladores', 0, 'botellin', 60, 45, False, None, 0),
    ('Tónica Tradicional', 'Refrescos y Mezcladores', 0, 'botellin', 50, 30, False, None, 0),
    ('Tónica de Fresa', 'Refrescos y Mezcladores', 0, 'botellin', 20, 8, False, None, 0),
    ('Cachimba (10 sabores)', 'Cachimbas / Shishas', 1, 'cazoleta', 10, 6, False, None, 0),
    ('Paquete de Tabaco (cachimbas)', 'Cachimbas / Shishas', 1, 'paquete', 20, 14, False, None, 0),
    ('Concentrado de Mojito', 'Mojitos y Varios', 0, 'botella', 10, 12, False, None, 0),
    ('Azúcar', 'Mojitos y Varios', 2, 'paquete', 5, 3, False, None, 0),
    ('Menta / Hierbabuena', 'Mojitos y Varios', 2, 'paquete', 10, 7, False, None, 0),
    ('Vasos', 'Mojitos y Varios', 2, 'paquete', 100, 60, False, None, 0),
    ('Pajitas', 'Mojitos y Varios', 2, 'paquete', 50, 25, False, None, 0),
]

cats = {}
for nombre, orden in CATEGORIAS:
    c, _ = Categoria.objects.get_or_create(nombre=nombre, defaults={'orden': orden})
    cats[nombre] = c

provs = []
for nombre, contacto in PROVEEDORES:
    p, _ = Proveedor.objects.get_or_create(nombre=nombre, defaults={'contacto': contacto})
    provs.append(p)

for nombre, cat, idx_prov, unidad, minimo, actual, alcohol, precio, copas in PRODUCTOS:
    Producto.objects.get_or_create(
        nombre=nombre,
        defaults=dict(
            categoria=cats[cat], proveedor=provs[idx_prov], unidad=unidad,
            stock_minimo=minimo, stock_actual=actual, es_alcohol=alcohol,
            precio_medio_copa=precio, copas_por_botella=copas,
        ),
    )

for nombre in ['Antonio', 'Lucía', 'María']:
    Empleado.objects.get_or_create(nombre=nombre)

admin, created = User.objects.get_or_create(
    username='admin', defaults={'is_staff': True, 'is_superuser': True}
)
if created:
    admin.set_password('admin12345')
    admin.save()

# Nuevo superusuario opcional definido aquí si se quiere
usuario_nuevo, creado_u = User.objects.get_or_create(
    username='jefe',
    defaults={
        'is_staff': True, 'is_superuser': True, 'email': 'msb.duck@gmail.com',
    },
)
if creado_u:
    usuario_nuevo.set_password('jefe12345')
    usuario_nuevo.save()

print(f'Catálogo listo: {Categoria.objects.count()} categorías, '
      f'{Proveedor.objects.count()} proveedores, '
      f'{Producto.objects.count()} productos, '
      f'{Empleado.objects.count()} empleados, '
      f'{User.objects.filter(is_superuser=True).count()} superusuarios.')

if SOLO_CATALOGO:
    print('Modo --solo-catalogo: no se añaden datos de demostración.')
    raise SystemExit(0)

# --------------------------------------------------------------- datos demo
empleados = list(Empleado.objects.all())
hoy = date.today()

# Tres domingos consecutivos (actual, -7d, -14d) para la auditoría semanal
c3_fecha = hoy
c2_fecha = hoy - timedelta(days=7)
c1_fecha = hoy - timedelta(days=14)

fechas_conteo = [c1_fecha, c2_fecha, c3_fecha]

# Limpieza idempotente de los datos demo previos (fechas demo)
CierreCaja.objects.filter(fecha__in=[
    d - timedelta(days=3) for d in fechas_conteo
] + [d - timedelta(days=4) for d in fechas_conteo]).delete()
Pedido.objects.filter(conteo__fecha__in=fechas_conteo).delete()
ConteoStock.objects.filter(fecha__in=fechas_conteo).delete()

# ---- Cierres de caja de los últimos fines de semana (viernes y sábado)
cierres_demo = [
    (c1_fecha - timedelta(days=2), 'viernes', 1100, 950),
    (c1_fecha - timedelta(days=1), 'sabado',  1650, 1250),
    (c2_fecha - timedelta(days=2), 'viernes', 1275, 1010),
    (c2_fecha - timedelta(days=1), 'sabado',  1725, 1380),
    (c3_fecha - timedelta(days=2), 'viernes', 1190, 990),
    (c3_fecha - timedelta(days=1), 'sabado',  1800, 1440),
]
n_pagos = 0
for idx, (fecha, servicio, efectivo, tpv) in enumerate(cierres_demo):
    cierre = CierreCaja.objects.create(
        fecha=fecha, servicio=servicio,
        fondo_caja=Decimal('200.00'),
        efectivo_total_caja=Decimal(efectivo),
        total_tpv_bizum=Decimal(tpv),
        creado_por=admin,
        observaciones='Datos de demostración',
    )
    emp = empleados[idx % len(empleados)]
    importe = Decimal('150.00' if idx % 2 == 0 else '120.00')
    PagoPersonal.objects.create(cierre=cierre, empleado=emp, importe=importe)
    n_pagos += 1

# ---- Conteos de stock de los domingos (el recuento baja de semana en semana)
def consumo_demo(idx, producto):
    """Botellas/botellines 'consumidos' cada semana, determinista."""
    if producto.es_alcohol:
        return (2, 3, 4)[idx % 3]
    if producto.unidad == 'botellin':
        return (12, 18, 24)[idx % 3]
    return (2, 3, 4)[idx % 3]

n_lineas = 0
conteos = []
for base_extra, fecha in ((2, c1_fecha), (1, c2_fecha), (0, c3_fecha)):
    conteo = ConteoStock.objects.create(
        fecha=fecha, creado_por=admin, nota='Conteo de demostración'
    )
    conteos.append(conteo)
    for idx, prod in enumerate(Producto.objects.all()):
        cons = consumo_demo(idx, prod)
        ConteoStockLinea.objects.create(
            conteo=conteo, producto=prod,
            cantidad_contada=prod.stock_actual + cons * base_extra,
        )
        n_lineas += 1

# ---- Pedidos derivados del último conteo (misma lógica que la web)
conteo_actual = conteos[-1]
por_proveedor = {}
for linea in conteo_actual.lineas.select_related('producto', 'producto__proveedor'):
    prod = linea.producto
    a_pedir = max(0, prod.stock_minimo - linea.cantidad_contada)
    if a_pedir > 0:
        por_proveedor.setdefault(prod.proveedor, []).append((prod, a_pedir))

n_pedidos = 0
n_lineas_pedido = 0
for i, (proveedor, items) in enumerate(por_proveedor.items()):
    pedido = Pedido.objects.create(
        fecha=hoy, proveedor=proveedor, conteo=conteo_actual,
        estado='enviado' if i == 0 else 'borrador',
        creado_por=admin, notas='Pedido de demostración',
    )
    for prod, unidades in items:
        PedidoLinea.objects.create(pedido=pedido, producto=prod, unidades_a_pedir=unidades)
        n_lineas_pedido += 1
    n_pedidos += 1

if n_pedidos == 0:
    print('Aviso: ningún producto está por debajo del stock mínimo actual,'
          ' así que no se generó ningún pedido demo.')

print(f'Datos demo creados: {len(cierres_demo)} cierres de caja, {n_pagos} pagos, '
      f'{len(conteos)} conteos con {n_lineas} líneas, '
      f'{n_pedidos} pedidos con {n_lineas_pedido} líneas.')

print('Listo. Superusuario: admin / admin12345 · jefe / jefe12345')