from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='core/password_reset.html',
        email_template_name='core/password_reset_email.html',
        subject_template_name='core/password_reset_subject.txt',
        success_url='/password-reset/enviado/',
    ), name='password_reset'),
    path('password-reset/enviado/', auth_views.PasswordResetDoneView.as_view(
        template_name='core/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='core/password_reset_confirm.html',
        success_url='/password-reset/completo/',
    ), name='password_reset_confirm'),
    path('password-reset/completo/', auth_views.PasswordResetCompleteView.as_view(
        template_name='core/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('actividad/', views.actividad, name='actividad'),
    path('registro/', views.auditoria_log, name='auditoria_log'),
    path('cerrar-sesion-todos/', views.cerrar_sesion_todos, name='cerrar_sesion_todos'),
]