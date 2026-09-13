"""Test de humo: vistas 200 + admin restringido + trazabilidad automática."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from datetime import date
from caja.models import CierreCaja, Empleado, PagoPersonal
from inventario.models import Categoria, Proveedor, Producto, ConteoStock, ConteoStockLinea
from pedidos.models import Pedido, PedidoLinea

# Limpieza de datos de prueba previos
Pedido.objects.all().delete()
ConteoStock.objects.all().delete()
CierreCaja.objects.all().delete()

c = Client()
USER = 'admin'
PW = 'admin12345'
ok = 0
fail = []

# 1) Sin login -> redirección al login
r = c.get('/')
assert r.status_code == 302, r.status_code
ok += 1

# 2) Usuario staff pero NO superuser: /admin/ debe bloquearse
staff_u, _ = User.objects.get_or_create(username='staff_no_su')
if staff_u.password == '':
    staff_u.set_password('staff12345')
    staff_u.is_staff = True
    staff_u.is_superuser = False
    staff_u.save()
c2 = Client()
c2.login(username='staff_no_su', password='staff12345')
r = c2.get('/admin/')
# El admin no debe listar el índice: debe redirigir al login o dar 302/403
bloqueado = r.status_code in (302, 403) and 'login' in (r.get('Location', '') or '')
if bloqueado:
    ok += 1
else:
    fail.append(('admin bloqueado para staff', r.status_code))

# 3) Superuser logueado
assert c.login(username=USER, password=PW)
r = c.get('/admin/')
if r.status_code == 200 and 'Chill Out' in (r.content.decode('utf-8', 'ignore')):
    ok += 1
else:
    fail.append(('admin superuser', r.status_code))

# 4) Vistas 200
URLS = ['/', '/caja/', '/caja/empleados/', '/inventario/', '/inventario/conteos/',
        '/inventario/conteo/nuevo/', '/inventario/proveedores/', '/registro/', '/actividad/']
for u in URLS:
    r = c.get(u)
    if r.status_code == 200:
        ok += 1
    else:
        fail.append((u, r.status_code))

# 5) CRUD crea registros de auditoría
antes = __import__('core.models', fromlist=['RegistroAuditoria']).RegistroAuditoria.objects.count()

emp = Empleado.objects.first()
cierre = CierreCaja.objects.create(
    fecha=date(2026,9,12), servicio='viernes', fondo_caja=200, efectivo_total_caja=1000,
    total_tpv_bizum=800, creado_por=User.objects.get(username=USER),
)
PagoPersonal.objects.create(cierre=cierre, empleado=emp, importe=150)

cierre.fondo_caja = 250
cierre.save()

despues_crear = __import__('core.models', fromlist=['RegistroAuditoria']).RegistroAuditoria.objects.count()
if despues_crear - antes >= 3:  # cierre creacion + pago creacion + cierre modificacion
    ok += 1
else:
    fail.append((f'auditoria count {despues_crear - antes}', 0))

# 6) Eliminación registrada
cierre.delete()
despues_del = __import__('core.models', fromlist=['RegistroAuditoria']).RegistroAuditoria.objects.count()
if despues_del > despues_crear:
    ok += 1
else:
    fail.append(('auditoria delete', 0))

# 7) Conteo + pedido (flujo completo)
cat = Categoria.objects.first()
prov, _ = Proveedor.objects.get_or_create(nombre='Proveedor Test')
p1, _ = Producto.objects.get_or_create(
    nombre='Test Alcohol', defaults=dict(categoria=cat, proveedor=prov, unidad='botella',
                                         stock_minimo=10, stock_actual=5, es_alcohol=True,
                                         precio_medio_copa=8))
conteo = ConteoStock.objects.create(fecha=date(2026,9,13), creado_por=User.objects.get(username=USER))
ConteoStockLinea.objects.create(conteo=conteo, producto=p1, cantidad_contada=2)
r = c.get(f'/pedidos/generar/{conteo.pk}/')
if r.status_code == 302 and Pedido.objects.exists():
    ok += 1
else:
    fail.append((f'/pedidos/generar/{conteo.pk}/', r.status_code))

pedido = Pedido.objects.first()
if pedido:
    for u in [f'/pedidos/{pedido.pk}/', f'/pedidos/{pedido.pk}/texto/', f'/pedidos/{pedido.pk}/pdf/']:
        r = c.get(u)
        if r.status_code == 200:
            ok += 1
        else:
            fail.append((u, r.status_code))
else:
    fail.append(('pedido', 0))

print(f'Total OK: {ok} | Fallos: {len(fail)}')
if fail:
    print('Fallos:', fail)
else:
    print('Todos los chequeos pasaron OK')
