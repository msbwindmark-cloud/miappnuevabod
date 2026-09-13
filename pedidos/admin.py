from django.contrib.admin import ModelAdmin, TabularInline
from django.contrib.admin.decorators import register

from core.sites import admin_site

from .models import Pedido, PedidoLinea


class PedidoLineaInline(TabularInline):
    model = PedidoLinea
    extra = 0
    autocomplete_fields = ['producto']


@register(Pedido, site=admin_site)
class PedidoAdmin(ModelAdmin):
    list_display = ('id', 'fecha', 'proveedor', 'estado', 'total_unidades', 'creado_por')
    list_filter = ('estado', 'proveedor')
    search_fields = ('proveedor__nombre',)
    inlines = [PedidoLineaInline]