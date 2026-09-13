"""
Vistas del Módulo 3: Generador de Pedidos a Proveedores.
Unidades a Pedir = MAX(0, Stock Mínimo Deseado − Stock Actual Contado)
"""

import io
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, Spacer, SimpleDocTemplate, Table, TableStyle,
)

from inventario.models import ConteoStock, Producto
from pedidos.models import Pedido, PedidoLinea



@login_required
def pedido_list(request):
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '')
    pedidos = Pedido.objects.select_related('proveedor', 'conteo').annotate(
        total_lineas=Sum('lineas__unidades_a_pedir')
    )
    if q:
        pedidos = pedidos.filter(
            Q(proveedor__nombre__icontains=q) | Q(estado__icontains=q)
        )
    if estado:
        pedidos = pedidos.filter(estado=estado)
    pedidos = pedidos.order_by('-fecha', '-id')
    filtros = {}
    if q:
        filtros['q'] = q
    if estado:
        filtros['estado'] = estado
    page_obj = Paginator(pedidos, 5).get_page(request.GET.get('page'))
    return render(request, 'pedidos/pedido_list.html', {
        'page_obj': page_obj, 'filtros': filtros, 'q': q, 'estado': estado,
        'estados': Pedido.ESTADOS,
    })


@login_required
def pedido_generar(request, conteo_pk):
    """Genera los pedidos por proveedor a partir del conteo del domingo."""
    conteo = get_object_or_404(ConteoStock, pk=conteo_pk)
    lineas = conteo.lineas.select_related('producto', 'producto__proveedor')

    por_proveedor = {}
    for linea in lineas:
        p = linea.producto
        a_pedir = max(0, p.stock_minimo - linea.cantidad_contada)
        if a_pedir <= 0:
            continue
        por_proveedor.setdefault(p.proveedor, []).append((p, a_pedir))

    if not por_proveedor:
        messages.info(request, 'No hay productos por debajo del stock mínimo: no se genera pedido.')
        return redirect('inventario:conteo_detail', pk=conteo.pk)

    creados = []
    for proveedor, items in por_proveedor.items():
        pedido, created = Pedido.objects.get_or_create(
            fecha=date.today(), proveedor=proveedor, conteo=conteo,
            defaults={'estado': 'borrador', 'creado_por': request.user},
        )
        if not created:
            pedido.lineas.all().delete()
        for producto, unidades in items:
            PedidoLinea.objects.create(pedido=pedido, producto=producto, unidades_a_pedir=unidades)
        creados.append(pedido)

    messages.success(request, f'Se generaron {len(creados)} pedido(s) de proveedor.')
    return redirect('pedidos:pedido_list')


def _texto_pedido(pedido):
    lineas = '\n'.join(
        f'• {l.unidades_a_pedir} x {l.producto.nombre}'
        for l in pedido.lineas.all()
    )
    return (
        f'PEDIDO {pedido.fecha:%d/%m/%Y} - {pedido.proveedor.nombre}\n'
        f'{lineas}\nTotal unidades: {pedido.total_unidades}'
    )


@login_required
def pedido_detail(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    return render(request, 'pedidos/pedido_detail.html', {
        'pedido': pedido, 'texto_wa': _texto_pedido(pedido),
    })


@login_required
@require_POST
def pedido_estado(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    estado = request.POST.get('estado')
    if estado in dict(Pedido.ESTADOS):
        pedido.estado = estado
        pedido.save(update_fields=['estado'])
        if estado == 'enviado':
            _email_pedido(request, pedido)
        messages.success(request, f'Pedido marcado como "{dict(Pedido.ESTADOS)[estado]}".')
    return redirect('pedidos:pedido_detail', pk=pedido.pk)


@login_required
def pedido_texto(request, pk):
    """Listado en texto claro para enviar por WhatsApp al comercial."""
    pedido = get_object_or_404(Pedido, pk=pk)
    return HttpResponse(_texto_pedido(pedido), content_type='text/plain; charset=utf-8')


@login_required
def pedido_pdf(request, pk):
    """Genera un PDF formateado del pedido para enviar al proveedor."""
    pedido = get_object_or_404(Pedido, pk=pk)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="pedido_{pedido.pk}_{pedido.proveedor.nombre}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
    )

    doc = SimpleDocTemplate(response, pagesize=A4,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            leftMargin=15 * mm, rightMargin=15 * mm)
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle('Titulo', parent=estilos['Title'], fontSize=18, alignment=TA_CENTER,
                            textColor=colors.HexColor('#ff4800'))
    sub = ParagraphStyle('Sub', parent=estilos['Normal'], alignment=TA_CENTER, fontSize=11,
                         textColor=colors.grey)
    h3 = ParagraphStyle('H3', parent=estilos['Heading3'], textColor=colors.HexColor('#1d3557'))

    elementos = [Paragraph(settings.EMPRESA, titulo), Spacer(1, 4)]
    elementos.append(Paragraph(f'{settings.EMPRESA_CIUDAD} · Pedido nº {pedido.pk}', sub))
    elementos.append(Paragraph(f'Fecha: {pedido.fecha:%d/%m/%Y} · Proveedor: {pedido.proveedor.nombre}', sub))
    elementos.append(Spacer(1, 6 * mm))
    elementos.append(Paragraph('Detalle del pedido', h3))

    data = [['#', 'Producto', 'Unidades', '']]
    for i, l in enumerate(pedido.lineas.all(), start=1):
        data.append([str(i), l.producto.nombre, str(l.unidades_a_pedir), ''])
    data.append(['', 'TOTAL', str(pedido.total_unidades), ''])

    tabla = Table(data, colWidths=[12 * mm, 110 * mm, 30 * mm, 30 * mm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1d3557')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f1f3f5')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#adb5bd')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e9ecef')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 6 * mm))
    if pedido.notas:
        elementos.append(Paragraph(f'Notas: {pedido.notas}', estilos['Normal']))

    doc.build(elementos)
    return response


@login_required
def pedido_excel(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="pedidos_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    wb = Workbook()
    ws = wb.active
    ws.title = 'Pedidos'
    ws.append(['Pedido', 'Fecha', 'Proveedor', 'Estado', 'Producto', 'Unidades'])
    for pedido in Pedido.objects.all().order_by('-fecha'):
        if not pedido.lineas.exists():
            ws.append([pedido.id, pedido.fecha.isoformat(), pedido.proveedor.nombre,
                       pedido.get_estado_display(), '-', 0])
        for l in pedido.lineas.all():
            ws.append([pedido.id, pedido.fecha.isoformat(), pedido.proveedor.nombre,
                       pedido.get_estado_display(), l.producto.nombre, l.unidades_a_pedir])
    wb.save(response)
    return response


def _email_pedido(request, pedido):
    lineas = '\n'.join(
        f'- {l.unidades_a_pedir} x {l.producto.nombre}' for l in pedido.lineas.all()
    )
    asunto = f'Pedido {pedido.pk} para {pedido.proveedor.nombre}'
    cuerpo = (
        f'Pedido generado por {request.user.username} el {timezone.now():%d/%m/%Y %H:%M}.\n\n'
        f'{lineas}\n\nTotal unidades: {pedido.total_unidades}\n\n'
        f'Contacto proveedor: {pedido.proveedor.contacto}'
    )
    dest = ', '.join(settings.EMAIL_NOTIFY_TO)
    print('=== EMAIL SEND ===')
    print('to:', dest)
    print('from:', settings.DEFAULT_FROM_EMAIL)
    print('host:', settings.EMAIL_HOST, 'port:', settings.EMAIL_PORT, 'tls:', settings.EMAIL_USE_TLS)
    print('user:', settings.EMAIL_HOST_USER)
    print('assunto:', asunto)
    try:
        send_mail(
            asunto, cuerpo, settings.DEFAULT_FROM_EMAIL,
            list(settings.EMAIL_NOTIFY_TO), fail_silently=False,
        )
        print('EMAIL SENT OK')
        messages.success(request, f'Pedido marcado como "Enviado". Email de notificación enviado a: {dest}')
    except Exception as e:
        print('EMAIL ERROR:', type(e).__name__, str(e))
        messages.error(request, f'No se pudo enviar el email: {e}')
    print('=== END EMAIL ===')