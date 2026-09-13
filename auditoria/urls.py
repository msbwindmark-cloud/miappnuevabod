from django.urls import path
from . import views

app_name = 'auditoria'

urlpatterns = [
    path('', views.auditoria_view, name='auditoria'),
    path('excel/', views.auditoria_excel, name='auditoria_excel'),
]