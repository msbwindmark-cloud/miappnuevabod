from django.urls import path, register_converter

from . import views
from .converters import SignedIntConverter

register_converter(SignedIntConverter, 'sint')

app_name = 'inventario'

urlpatterns = [
    path('', views.producto_list, name='producto_list'),
    path('productos/nuevo/', views.producto_create, name='producto_create'),
    path('productos/<int:pk>/editar/', views.producto_edit, name='producto_edit'),
    path('productos/<int:pk>/eliminar/', views.producto_delete, name='producto_delete'),
    path('proveedores/', views.proveedor_list, name='proveedor_list'),
    path('proveedores/nuevo/', views.proveedor_create, name='proveedor_create'),
    path('proveedores/<int:pk>/editar/', views.proveedor_edit, name='proveedor_edit'),
    path('proveedores/<int:pk>/eliminar/', views.proveedor_delete, name='proveedor_delete'),
    path('categorias/nueva/', views.categoria_create, name='categoria_create'),
    path('conteos/', views.conteo_list, name='conteo_list'),
    path('conteo/nuevo/', views.conteo_nuevo, name='conteo_nuevo'),
    path('conteos/<int:pk>/', views.conteo_detail, name='conteo_detail'),
    path('api/ajustar/<int:producto_id>/<sint:delta>/', views.conteo_ajustar, name='conteo_ajustar'),
    path('api/set/<int:producto_id>/', views.conteo_set, name='conteo_set'),
    path('stock/excel/', views.stock_excel, name='stock_excel'),
]