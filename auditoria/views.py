"""
Módulo 4: Auditoría de Rendimiento Teórico de Botellas (€ vs. Consumos).
Regla local: 8 copas por botella de alcohol. 1 copa = 1 refresco.
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from caja.models import CierreCaja
from inventario.models import ConteoStock, Categoria


def _es_importante(c):
    return c.nombre.casefold() in ('rones', 'whiskys', 'ginebras', 'licores y otros destilados',
                                   'licores')


def auditoria_por_semanas():
    """Cruza conteos consecutivos para calcular consumos teóricos."""
    resultados = []
    conteos = list(ConteoStock.objects.all().order_by('fecha'))
    prev = None
    for conteo in conteos:
        if prev is None:
            prev = conteo
            continue
        r = _auditoria_semana(prev, conteo)
        if r is not None:
            resultados.append(r)
        prev = conteo
    return resultados


def _auditoria_semana(conteo_ini, conteo_fin):
    """Δ botellas entre dos domingos; cruza con la facturación de la semana."""

    valores_ini = {l.producto_id: l.cantidad_contada for l in conteo_ini.lineas.all()}
    valores_fin = {l.producto_id: l.cantidad_contada for l in conteo_fin.lineas.all()}
    productos = {l.producto_id: l.producto for l in conteo_fin.lineas.select_related('producto')}

    # Facturación real entre el sábado anterior y este conteo
    cierres = CierreCaja.objects.filter(fecha__range=[conteo_ini.fecha, conteo_fin.fecha])
    facturacion_real = sum((c.facturacion_total for c in cierres), 0)
    pagos = sum((c.total_pagos_personal for c in cierres), 0)

    diff_alcohol = []
    diff_refrescos = []
    copas_total = 0
    facturacion_teorica = 0

    ids = set(valores_ini) | set(valores_fin)

    for pid in sorted(ids):
        inicial = valores_ini.get(pid)
        final = valores_fin.get(pid)
        if inicial is None or final is None:
            continue
        delta = inicial - final
        if delta <= 0:
            continue
        prod = productos.get(pid)
        if prod is None:
            continue
        if prod.es_alcohol:
            copas = prod.copas_por_botella or settings.COPAS_POR_BOTELLA
            copas_prod = delta * copas
            copas_total += copas_prod
            facturacion_teorica += copas_prod * (prod.precio_medio_copa or 0)
            diff_alcohol.append({'producto': prod.nombre, 'unidad': delta,
                                 'copas_teoricas': copas_prod,
                                 'precio_copa': prod.precio_medio_copa})
        else:
            diff_refrescos.append({'producto': prod.nombre, 'unidad': delta})

    refrescos_consumidos = sum(x['unidad'] for x in diff_refrescos)
    botellas_alcohol = sum(x['unidad'] for x in diff_alcohol)

    return {
        'conteo_ini': conteo_ini,
        'conteo_fin': conteo_fin,
        'diff_alcohol': diff_alcohol,
        'diff_refrescos': diff_refrescos,
        'botellas_alcohol': botellas_alcohol,
        'copas_total': copas_total,
        'facturacion_teorica': facturacion_teorica,
        'facturacion_real': facturacion_real,
        'desviacion': facturacion_teorica - facturacion_real,
        'refrescos_consumidos': refrescos_consumidos,
        'ratio_refresco_copa': (refrescos_consumidos / copas_total if copas_total else 0),
        'pagos': pagos,
        'cierres': cierres,
    }


@login_required
def auditoria_view(request):
    resultados = auditoria_por_semanas()
    return render(request, 'auditoria/auditoria.html', {
        'resultados': resultados,
        'copas_por_botella': settings.COPAS_POR_BOTELLA,
    })


@login_required
def auditoria_excel(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="auditoria_rendimiento.xlsx"'
    wb = Workbook()
    ws = wb.active
    ws.title = 'Auditoría'
    ws.merge_cells('A1:F1')
    ws['A1'] = 'Auditoría de rendimiento teórico (8 copas/botella)'
    ws['A1'].font = Font(bold=True, size=13)

    fila = 3
    for r in auditoria_por_semanas():
        ws.cell(fila, 1, f'Semana {r["conteo_ini"].fecha} → {r["conteo_fin"].fecha}')
        ws.cell(fila, 1).font = Font(bold=True, color='FFFFFF')
        ws.cell(fila, 1).fill = PatternFill('solid', fgColor='1D3557')
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=6)
        fila += 1
        headers = ['Producto', 'Δ Unidades', 'Copas teóricas', 'Precio/copa', 'Importe teórico', '']
        for col, h in enumerate(headers, 1):
            ws.cell(fila, col, h).font = Font(bold=True)
        fila += 1
        for t in r['diff_alcohol']:
            ws.append([])
            ws.cell(fila, 1, t['producto'])
            ws.cell(fila, 2, t['unidad'])
            ws.cell(fila, 3, t['copas_teoricas'])
            ws.cell(fila, 4, float(t['precio_copa'] or 0))
            ws.cell(fila, 5, round(float(t['copas_teoricas'] * (t['precio_copa'] or 0)), 2))
            fila += 1
        ws.cell(fila, 1, 'TOTAL FACTURACIÓN TEÓRICA')
        ws.cell(fila, 1).font = Font(bold=True)
        ws.cell(fila, 5, round(float(r['facturacion_teorica']), 2))
        ws.cell(fila, 5).font = Font(bold=True)
        fila += 1
        ws.cell(fila, 1, 'Facturación real (cierre de caja)')
        ws.cell(fila, 5, round(float(r['facturacion_real']), 2))
        fila += 1
        ws.cell(fila, 1, 'Desviación')
        ws.cell(fila, 5, round(float(r['desviacion']), 2))
        fila += 2

    wb.save(response)
    return response