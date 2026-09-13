from django.contrib.admin import ModelAdmin, TabularInline
from django.contrib.admin.decorators import register

from core.sites import admin_site

from .models import CierreCaja, Empleado, PagoPersonal


class PagoPersonalInline(TabularInline):
    model = PagoPersonal
    extra = 0


@register(Empleado, site=admin_site)
class EmpleadoAdmin(ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)


@register(CierreCaja, site=admin_site)
class CierreCajaAdmin(ModelAdmin):
    list_display = ('fecha', 'servicio', 'fondo_caja', 'efectivo_total_caja',
                    'total_tpv_bizum', 'facturacion_total', 'efectivo_final_requerido')
    list_filter = ('servicio', 'fecha')
    search_fields = ('servicio',)
    readonly_fields = ('facturacion_efectivo_neto', 'facturacion_total',
                       'total_pagos_personal', 'efectivo_final_requerido')
    inlines = [PagoPersonalInline]