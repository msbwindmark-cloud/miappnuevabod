from django.urls import path
from . import views

app_name = 'caja'

urlpatterns = [
    path('', views.cierre_list, name='cierre_list'),
    path('nuevo/', views.cierre_create, name='cierre_create'),
    path('<int:pk>/', views.cierre_detail, name='cierre_detail'),
    path('<int:pk>/editar/', views.cierre_edit, name='cierre_edit'),
    path('<int:pk>/eliminar/', views.cierre_delete, name='cierre_delete'),
    path('<int:pk>/whatsapp/', views.cierre_whatsapp, name='cierre_whatsapp'),
    path('<int:pk>/copiar-whatsapp/', views.cierre_copiar_whatsapp, name='cierre_copiar_whatsapp'),
    path('empleados/', views.empleado_list, name='empleado_list'),
    path('empleados/nuevo/', views.empleado_create, name='empleado_create'),
    path('excel/', views.cierre_excel, name='cierre_excel'),
]