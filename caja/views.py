"""
Vistas del Módulo 1: Cierre de Caja Diario y Gestión de Personal.
"""

import io

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.core.mail import send_mail
from django.views.decorators.http import require_POST

from openpyxl import Workbook

from .forms import CierreCajaForm, PagoPersonalFormSet
from .models import CierreCaja, PagoPersonal, Empleado


@login_required
def cierre_list(request):
    cierres = CierreCaja.objects.select_related().all()
    return render(request, 'caja/cierre_list.html', {'cierres': cierres})


@login_required
def cierre_create(request):
    if request.method == 'POST':
        form = CierreCajaForm(request.POST)
        formset = PagoPersonalFormSet(request.POST, prefix='pagos')
        if form.is_valid() and formset.is_valid():
            cierre = form.save(commit=False)
            cierre.creado_por = request.user
            cierre.save()
            formset.instance = cierre
            formset.save()
            _notificar_cierre(request, cierre)
            messages.success(request, 'Cierre de caja guardado correctamente.')
            return redirect('caja:cierre_detail', pk=cierre.pk)
    else:
        form = CierreCajaForm()
        formset = PagoPersonalFormSet(queryset=PagoPersonal.objects.none(), prefix='pagos')
    return render(request, 'caja/cierre_form.html', {
        'form': form, 'formset': formset, 'titulo': 'Nuevo cierre de caja', 'editar': False,
        'empleados': Empleado.objects.filter(activo=True),
    })


@login_required
def cierre_detail(request, pk):
    cierre = get_object_or_404(CierreCaja, pk=pk)
    return render(request, 'caja/cierre_detail.html', {'cierre': cierre})


@login_required
def cierre_edit(request, pk):
    cierre = get_object_or_404(CierreCaja, pk=pk)
    if request.method == 'POST':
        form = CierreCajaForm(request.POST, instance=cierre)
        formset = PagoPersonalFormSet(request.POST, instance=cierre, prefix='pagos')
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Cierre actualizado correctamente.')
            return redirect('caja:cierre_detail', pk=cierre.pk)
    else:
        form = CierreCajaForm(instance=cierre)
        formset = PagoPersonalFormSet(instance=cierre, prefix='pagos')
    return render(request, 'caja/cierre_form.html', {
        'form': form, 'formset': formset, 'titulo': f'Editar cierre {cierre.fecha}', 'editar': True,
        'empleados': Empleado.objects.filter(activo=True),
    })


@login_required
@require_POST
def cierre_delete(request, pk):
    cierre = get_object_or_404(CierreCaja, pk=pk)
    cierre.delete()
    messages.success(request, 'Cierre eliminado.')
    return redirect('caja:cierre_list')


@login_required
def cierre_whatsapp(request, pk):
    """Devuelve el resumen formateado para copiar al portapapeles."""
    cierre = get_object_or_404(CierreCaja, pk=pk)
    return HttpResponse(cierre.resumen_whatsapp, content_type='text/plain; charset=utf-8')


@login_required
def cierre_copiar_whatsapp(request, pk):
    """Redirige al detail con flag para copiar al clipboard por JS."""
    return redirect(f'/caja/{pk}/?copy=whatsapp')


@login_required
def empleado_list(request):
    empleados = Empleado.objects.all()
    return render(request, 'caja/empleado_list.html', {'empleados': empleados})


@login_required
def empleado_create(request):
    from django.forms import ModelForm

    class EmpleadoForm(ModelForm):
        class Meta:
            model = Empleado
            fields = ['nombre', 'activo']
            widgets = {
                'nombre': forms.TextInput(attrs={'class': 'form-control'}),
                'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            }

    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empleado creado.')
            return redirect('caja:empleado_list')
    else:
        form = EmpleadoForm()
    return render(request, 'generic_form.html', {'form': form, 'titulo': 'Nuevo empleado'})


@login_required
def cierre_excel(request):
    """Exporta cierres a Excel."""
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="cierres_caja_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    wb = Workbook()
    ws = wb.active
    ws.title = 'Cierres de Caja'
    headers = ['Fecha', 'Servicio', 'Fondo', 'Efectivo Total', 'TPV/Bizum',
               'Fact. Efectivo Neto', 'Fact. Total', 'Pagos Personal', 'Efectivo Final']
    ws.append(headers)
    for c in CierreCaja.objects.all().order_by('-fecha'):
        ws.append([
            c.fecha.isoformat(),
            c.get_servicio_display(),
            float(c.fondo_caja),
            float(c.efectivo_total_caja),
            float(c.total_tpv_bizum),
            float(c.facturacion_efectivo_neto),
            float(c.facturacion_total),
            float(c.total_pagos_personal),
            float(c.efectivo_final_requerido),
        ])
    wb.save(response)
    return response


def _notificar_cierre(request, cierre):
    send_mail(
        f'Cierre de caja guardado – {cierre.fecha:%d/%m/%Y}',
        (
            f'El usuario {request.user.username} guardó el cierre de caja del '
            f'{cierre.fecha:%d/%m/%Y} ({cierre.get_servicio_display()}).\n\n'
            f'Facturación Total: {cierre.facturacion_total}€\n'
            f'Facturación Efectivo Neto: {cierre.facturacion_efectivo_neto}€\n'
            f'TPV/Bizum: {cierre.total_tpv_bizum}€\n'
            f'Pagos al personal: {cierre.total_pagos_personal}€\n'
            f'Efectivo final requerido en caja: {cierre.efectivo_final_requerido}€'
        ),
        settings.DEFAULT_FROM_EMAIL,
        list(settings.EMAIL_NOTIFY_TO),
        fail_silently=True,
    )