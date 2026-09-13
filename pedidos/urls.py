from django.urls import path
from . import views

app_name = 'pedidos'

urlpatterns = [
    path('', views.pedido_list, name='pedido_list'),
    path('generar/<int:conteo_pk>/', views.pedido_generar, name='pedido_generar'),
    path('<int:pk>/', views.pedido_detail, name='pedido_detail'),
    path('<int:pk>/estado/', views.pedido_estado, name='pedido_estado'),
    path('<int:pk>/texto/', views.pedido_texto, name='pedido_texto'),
    path('<int:pk>/pdf/', views.pedido_pdf, name='pedido_pdf'),
    path('excel/', views.pedido_excel, name='pedido_excel'),
]