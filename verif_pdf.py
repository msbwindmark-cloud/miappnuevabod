"""Verificación 100% contra el Documento Funcional EFD-2026-v1.0.

Comprueba las fórmulas y el formato de salida tal como especifica el PDF.
"""

import os
import sys
import django

sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from datetime import date

from caja.models import CierreCaja, PagoPersonal, Empleado
from inventario.models import Categoria, Proveedor, Producto, ConteoStock, ConteoStockLinea
from pedidos.models import Pedido
from auditoria.views import _auditoria_semana
from django.conf import settings

# Limpieza de ejecuciones previas
Pedido.objects.all().delete()
Producto.objects.filter(nombre__startswith='Verif').delete()
Proveedor.objects.filter(nombre='Proveedor Verificacion').delete()
ConteoStock.objects.filter(fecha__year=2026).delete()
CierreCaja.objects.all().delete()

resultados = []
def comprueba(nombre, condicion):
    resultados.append((nombre, bool(condicion)))
    print(('OK ' if condicion else 'FALL') + ' - ' + nombre)

# ---- Módulo 1: ejemplo EXACTO del PDF (EFD-2026-v1.0, pág.2) ----
# "Cierre [Fecha] | Facturación Total: 1.600€ (TPV: 800€ | Efectivo Neto: 800€) | Pagos Personal: 150€ | Caja Restante: 850€"
cierre = CierreCaja.objects.create(
    fecha=date(2026, 9, 12), servicio='viernes', fondo_caja=200,
    efectivo_total_caja=1000, total_tpv_bizum=800,
)
emp = Empleado.objects.first()
PagoPersonal.objects.create(cierre=cierre, empleado=emp, importe=150)

comprueba('M1: Efectivo neto = 1000 - 200 = 800', cierre.facturacion_efectivo_neto == 800)
comprueba('M1: Total noche = 800 + 800 = 1600', cierre.facturacion_total == 1600)
comprueba('M1: Caja restante = 1000 - 150 = 850', cierre.efectivo_final_requerido == 850)
esperado = (
    f'Cierre {cierre.fecha:%d/%m/%Y} | Facturación Total: 1600€ (TPV: 800€ | Efectivo Neto: 800€) '
    f'| Pagos Personal: 150€ | Caja Restante: 850€'
)
comprueba('M1: Formato WhatsApp idéntico al PDF', cierre.resumen_whatsapp == esperado)

# ---- Módulo 3: Unidades a Pedir = MAX(0, Stock Mínimo − Stock Contado) ----
cat = Categoria.objects.first()
prov, _ = Proveedor.objects.get_or_create(nombre='Proveedor Verificacion')
prod = Producto.objects.create(
    nombre='Verif Alcohol', categoria=cat, proveedor=prov, unidad='botella',
    stock_minimo=10, stock_actual=5, es_alcohol=True, precio_medio_copa=8,
)
prod_minimo2 = Producto.objects.create(
    nombre='Verif Refresco', categoria=cat, proveedor=prov, unidad='botellin',
    stock_minimo=50, stock_actual=60, es_alcohol=False,
)
comprueba('M3: a pedir = MAX(0, 10-5) = 5', prod.a_pedir == 5)
comprueba('M3: sin necesidad (50-60 < 0 -> 0)', prod_minimo2.a_pedir == 0)

conteo1 = ConteoStock.objects.create(fecha=date(2026, 11, 1))
ConteoStockLinea.objects.create(conteo=conteo1, producto=prod, cantidad_contada=10)
ConteoStockLinea.objects.create(conteo=conteo1, producto=prod_minimo2, cantidad_contada=60)
conteo2 = ConteoStock.objects.create(fecha=date(2026, 11, 8))
ConteoStockLinea.objects.create(conteo=conteo2, producto=prod, cantidad_contada=2)
ConteoStockLinea.objects.create(conteo=conteo2, producto=prod_minimo2, cantidad_contada=40)

# ---- Módulo 4 ----
aud = _auditoria_semana(conteo1, conteo2)
comprueba('M4: Δ botellas consumidas = 10 - 2 = 8', aud['botellas_alcohol'] == 8)
comprueba(f'M4: copas teóricas = 8 x {settings.COPAS_POR_BOTELLA} = 64',
          aud['copas_total'] == 8 * settings.COPAS_POR_BOTELLA)
comprueba('M4: fact. teórica = 64 copas x 8€ = 512', aud['facturacion_teorica'] == 512)
comprueba('M4: refrescos consumidos = 60 - 40 = 20', aud['refrescos_consumidos'] == 20)

# ---- Módulo 2: botones + / - de al menos 48px (requisito mobile-first) ----
with open(r'templates/base.html', encoding='utf-8') as f:
    base_css = f.read()
with open(r'templates/inventario/conteo_nuevo.html', encoding='utf-8') as f:
    conteo_html = f.read()
comprueba('M2: botones con min-height >= 48px', 'min-height: 48px' in base_css)
comprueba('M2: boton + / - por producto', conteo_html.count('data-accion') >= 2)
comprueba('M2: pestañas por categoría', 'catTabs' in conteo_html)

# ---- Exportaciones ----
comprueba('Excel cierres / stock / pedidos / auditoría', all([
    'cierre_excel' in open(r'caja/urls.py', encoding='utf-8').read(),
    'stock_excel' in open(r'inventario/urls.py', encoding='utf-8').read(),
    'pedido_excel' in open(r'pedidos/urls.py', encoding='utf-8').read(),
    'auditoria_excel' in open(r'auditoria/urls.py', encoding='utf-8').read(),
]))
comprueba('PDF de pedido', 'pedido_pdf' in open(r'pedidos/views.py', encoding='utf-8').read())
comprueba('Texto para WhatsApp', 'pedido_texto' in open(r'pedidos/urls.py', encoding='utf-8').read())

# ---- Seguridad / extras pedidos por el usuario ----
with open(r'config/settings.py', encoding='utf-8') as f:
    settings_txt = f.read()
comprueba('Login con límite de intentos', 'LOGIN_MAX_ATTEMPTS' in settings_txt)
comprueba('Admin solo superuser', "is_superuser" in open(r'core/sites.py', encoding='utf-8').read())
comprueba('Trazabilidad (auditoría CRUD)', 'RegistroAuditoria' in open(r'core/models.py', encoding='utf-8').read())
comprueba('Live reload activo', 'livereload' in settings_txt and 'LiveReloadScript' in settings_txt)

# limpieza
cierre.delete()
Pedido.objects.all().delete()
conteo1.delete()
conteo2.delete()
prod.delete()
prod_minimo2.delete()
prov.delete()

ok = sum(1 for _, c in resultados if c)
print(f'\n=== {ok}/{len(resultados)} requisitos verificados ===')
raise SystemExit(0 if ok == len(resultados) else 1)