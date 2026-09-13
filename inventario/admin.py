from django.contrib.admin import ModelAdmin, TabularInline, display
from django.contrib.admin.decorators import register

from core.sites import admin_site

from inventario.models import Categoria, ConteoStock, ConteoStockLinea, Producto, Proveedor


class ConteoStockLineaInline(TabularInline):
    model = ConteoStockLinea
    extra = 0
    autocomplete_fields = ['producto']


@register(Proveedor, site=admin_site)
class ProveedorAdmin(ModelAdmin):
    list_display = ('nombre', 'contacto', 'productos_count')
    search_fields = ('nombre', 'contacto')

    @display(description='Productos')
    def productos_count(self, obj):
        return obj.productos.count()


@register(Categoria, site=admin_site)
class CategoriaAdmin(ModelAdmin):
    list_display = ('nombre', 'orden', 'productos_count')
    ordering = ('orden',)

    @display(description='Productos')
    def productos_count(self, obj):
        return obj.productos.count()


@register(Producto, site=admin_site)
class ProductoAdmin(ModelAdmin):
    list_display = ('nombre', 'categoria', 'proveedor', 'unidad', 'stock_actual',
                    'stock_minimo', 'es_alcohol', 'activo')
    list_filter = ('categoria', 'proveedor', 'es_alcohol', 'activo')
    search_fields = ('nombre',)
    autocomplete_fields = []


@register(ConteoStock, site=admin_site)
class ConteoStockAdmin(ModelAdmin):
    list_display = ('fecha', 'creado_por', 'creado')
    inlines = [ConteoStockLineaInline]