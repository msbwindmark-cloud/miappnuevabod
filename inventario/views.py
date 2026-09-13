"""
Vistas del Módulo 2: Control de Stock e Inventario (domingo por la mañana).
Interfaz móvil táctil con botones +/- por categorías.
"""

import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from openpyxl import Workbook

from .forms import ProductoForm, ProveedorForm, CategoriaForm
from .models import Categoria, ConteoStock, ConteoStockLinea, Producto, Proveedor


_SESSION_KEY = 'conteo_en_curso'


# ---------------------------------------------------------------- catálogo

@login_required
def producto_list(request):
    q = request.GET.get('q', '')
    cat = request.GET.get('categoria', '')
    productos = Producto.objects.select_related('categoria', 'proveedor').all()
    if q:
        productos = productos.filter(nombre__icontains=q)
    if cat:
        productos = productos.filter(categoria_id=cat)
    categorias = Categoria.objects.all()
    return render(request, 'inventario/producto_list.html', {
        'productos': productos, 'categorias': categorias, 'q': q, 'cat': cat,
    })


@login_required
def producto_create(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado.')
            return redirect('inventario:producto_list')
    else:
        form = ProductoForm()
    return render(request, 'generic_form.html', {'form': form, 'titulo': 'Nuevo producto'})


@login_required
def producto_edit(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado.')
            return redirect('inventario:producto_list')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'generic_form.html', {'form': form, 'titulo': f'Editar {producto.nombre}'})


@login_required
@require_POST
def producto_delete(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    try:
        producto.delete()
        messages.success(request, 'Producto eliminado.')
    except Exception:
        messages.error(request, 'No se puede eliminar: tiene movimientos asociados.')
    return redirect('inventario:producto_list')


@login_required
def proveedor_list(request):
    proveedores = Proveedor.objects.annotate(num_productos=Count('productos'))
    return render(request, 'inventario/proveedor_list.html', {'proveedores': proveedores})


@login_required
def proveedor_create(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor creado.')
            return redirect('inventario:proveedor_list')
    else:
        form = ProveedorForm()
    return render(request, 'generic_form.html', {'form': form, 'titulo': 'Nuevo proveedor'})


@login_required
def categoria_create(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoría creada.')
            return redirect('inventario:producto_list')
    else:
        form = CategoriaForm()
    return render(request, 'generic_form.html', {'form': form, 'titulo': 'Nueva categoría'})


# ---------------------------------------------------------------- conteo táctil

@login_required
def conteo_list(request):
    conteos = ConteoStock.objects.all()
    return render(request, 'inventario/conteo_list.html', {'conteos': conteos})


def _valores_actuales(request, fecha=None):
    """Devuelve contadores de la sesión o por defecto el stock actual."""
    datos = request.session.get(_SESSION_KEY, {})
    valores = {}
    for p in Producto.objects.filter(activo=True):
        valores[p.id] = datos.get(str(p.id), p.stock_actual)
    return valores


@login_required
def conteo_nuevo(request):
    """Pantalla táctil de recuento: pestañas por categoría y botones +/-."""
    if request.method == 'POST':
        fecha = request.POST.get('fecha') or timezone.localdate().isoformat()
        try:
            fecha = timezone.datetime.strptime(fecha, '%Y-%m-%d').date()
        except ValueError:
            fecha = timezone.localdate()
        stock_final = json.loads(request.POST.get('stock_final', '{}'))

        conteo, _created = ConteoStock.objects.get_or_create(
            fecha=fecha, defaults={'creado_por': request.user}
        )
        conteo.lineas.all().delete()
        productos = Producto.objects.filter(activo=True)
        for p in productos:
            cantidad = int(stock_final.get(str(p.id), p.stock_actual) or 0)
            ConteoStockLinea.objects.create(
                conteo=conteo, producto=p, cantidad_contada=cantidad
            )
            p.stock_actual = cantidad
            p.save(update_fields=['stock_actual'])
        request.session.pop(_SESSION_KEY, None)
        messages.success(request, f'Conteo {conteo.fecha:%d/%m/%Y} guardado. '
                                  f'Stocks actualizados. Pulsa "Generar pedidos".')
        return redirect('inventario:conteo_detail', pk=conteo.pk)

    categorias = Categoria.objects.prefetch_related('productos').annotate(
        n=Count('productos')
    ).filter(n__gt=0).all()
    valores = _valores_actuales(request)
    return render(request, 'inventario/conteo_nuevo.html', {
        'categorias': categorias,
        'valores': valores,
        'fecha_hoy': timezone.localdate().isoformat(),
        'total_inicial': sum(valores.values()) if valores else 0,
    })


@login_required
@require_POST
def conteo_ajustar(request, producto_id, delta):
    """AJAX: incrementa/decrementa el contador de sesión. -1 o +1 o valores mayores."""
    try:
        producto = Producto.objects.get(pk=producto_id, activo=True)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    datos = request.session.get(_SESSION_KEY, {})
    valor = int(datos.get(str(producto.id), producto.stock_actual))
    valor = max(0, valor + int(delta))
    datos[str(producto.id)] = valor
    request.session[_SESSION_KEY] = datos
    return JsonResponse({'id': producto.id, 'valor': valor})


@login_required
@require_POST
def conteo_set(request, producto_id):
    """AJAX: fija un valor concreto para el contador (modo manual)."""
    try:
        producto = Producto.objects.get(pk=producto_id, activo=True)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    valor = max(0, int(request.POST.get('valor', 0)))
    datos = request.session.get(_SESSION_KEY, {})
    datos[str(producto.id)] = valor
    request.session[_SESSION_KEY] = datos
    return JsonResponse({'id': producto.id, 'valor': valor})


@login_required
def conteo_detail(request, pk):
    conteo = get_object_or_404(ConteoStock, pk=pk)
    return render(request, 'inventario/conteo_detail.html', {'conteo': conteo})


# ---------------------------------------------------------------- exportaciones

@login_required
def stock_excel(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="stock_productos.xlsx"'
    wb = Workbook()
    ws = wb.active
    ws.title = 'Stock'
    ws.append(['Producto', 'Categoría', 'Proveedor', 'Unidad', 'Stock actual', 'Stock mínimo', 'A pedir'])
    for p in Producto.objects.filter(activo=True).select_related('categoria', 'proveedor'):
        ws.append([
            p.nombre, p.categoria.nombre, p.proveedor.nombre, p.get_unidad_display(),
            p.stock_actual, p.stock_minimo, max(0, p.stock_minimo - p.stock_actual),
        ])
    wb.save(response)
    return response