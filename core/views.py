"""
Vistas de Core: login potente con bloqueo temporal, dashboard, seguridad de sesión
y envío de notificaciones por email.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.views import LogoutView
from django.db.models import Count, Sum
from django.dispatch import receiver
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import LoginForm, PasswordChangeForm
from .models import LoginAttempt, RegistroAuditoria, SessionActivity

from caja.models import CierreCaja, Empleado
from inventario.models import Producto, Proveedor, ConteoStock


def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or None


def _registrar_intento(request, username, success):
    LoginAttempt.objects.create(
        username=username,
        ip_address=_get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        success=success,
    )


def _registrar_actividad(request, usuario, evento='login'):
    SessionActivity.objects.create(
        usuario=usuario,
        ip_address=_get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        evento=evento,
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    ip = _get_client_ip(request)
    form = LoginForm(request, data=request.POST or None)
    lock = False

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        if username and LoginAttempt.is_locked(username, ip):
            lock = True
            messages.error(
                request,
                f'Demasiados intentos fallidos. Cuenta bloqueada '
                f'{settings.LOGIN_LOCK_MINUTES} minutos.'
            )
        elif form.is_valid():
            user = form.get_user()
            login(request, user)
            _registrar_intento(request, username, success=True)
            _registrar_actividad(request, user, 'login')
            RegistroAuditoria.objects.create(
                usuario=user, accion='login', modelo='core.SessionActivity',
                objeto_id=user.pk, objeto=f'Acceso de {user.username}',
                ip_address=ip, user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            )
            if request.POST.get('remember'):
                request.session.set_expiry(60 * 60 * 24 * 30)  # 30 días
            send_mail(
                'Nuevo acceso al sistema',
                f'Se ha registrado un acceso exitoso a "{settings.EMPRESA}" '
                f'con el usuario {user.username} el {timezone.now():%d/%m/%Y %H:%M} '
                f'desde la IP {ip}.',
                settings.DEFAULT_FROM_EMAIL,
                list(settings.EMAIL_NOTIFY_TO),
                fail_silently=True,
            )
            messages.success(request, f'Bienvenido de nuevo, {user.get_full_name() or user.username}.')
            return redirect('core:home')
        else:
            _registrar_intento(request, username or request.POST.get('username', ''), success=False)
            messages.error(request, 'Usuario o contraseña incorrectos.')

    context = {
        'form': form,
        'logo': '🍹',
        'lock': lock,
        'max_attempts': settings.LOGIN_MAX_ATTEMPTS,
    }
    return render(request, 'core/login.html', context)


def logout_view(request):
    if request.user.is_authenticated:
        _registrar_actividad(request, request.user, 'logout')
        RegistroAuditoria.objects.create(
            usuario=request.user, accion='logout', modelo='core.SessionActivity',
            objeto_id=request.user.pk, objeto=f'Salida de {request.user.username}',
            ip_address=_get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('core:login')


@login_required
def home(request):
    user = request.user
    ultimo_cierre = CierreCaja.objects.first()
    cierres_mes = CierreCaja.objects.filter(
        fecha__year=timezone.now().year, fecha__month=timezone.now().month
    )

    total_ventas = sum((c.facturacion_total for c in cierres_mes), 0)
    total_efectivo = sum((c.facturacion_efectivo_neto for c in cierres_mes), 0)
    total_tpv = sum((c.total_tpv_bizum for c in cierres_mes), 0)
    pagos_personal = sum((c.total_pagos_personal for c in cierres_mes), 0)

    productos_bajo = Producto.objects.filter(activo=True).order_by('stock_actual', 'stock_minimo')[:8]
    conteos = ConteoStock.objects.all()[:8]
    cierres = CierreCaja.objects.all()[:8]
    proveedores = Proveedor.objects.annotate(num_productos=Count('productos'))
    empleados = Empleado.objects.filter(activo=True)

    context = {
        'ultimo_cierre': ultimo_cierre,
        'num_cierres': cierres_mes.count(),
        'total_ventas': total_ventas,
        'total_efectivo': total_efectivo,
        'total_tpv': total_tpv,
        'pagos_personal': pagos_personal,
        'productos_bajo': productos_bajo,
        'conteos': conteos,
        'cierres': cierres,
        'proveedores': proveedores,
        'empleados': empleados,
        'num_productos': Producto.objects.filter(activo=True).count(),
        'num_proveedores': Proveedor.objects.count(),
    }
    return render(request, 'core/home.html', context)


@login_required
def cambiar_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            send_mail(
                'Contraseña cambiada',
                f'La contraseña de tu usuario {user.username} en "{settings.EMPRESA}" '
                f'se cambió correctamente el {timezone.now():%d/%m/%Y %H:%M}.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
            messages.success(request, 'Contraseña actualizada correctamente.')
            return redirect('core:home')
    else:
        form = PasswordChangeForm(request.user)
    for nombre, campo in form.fields.items():
        campo.widget.attrs.update({'class': 'form-control'})
    return render(request, 'core/cambiar_password.html', {'form': form})


@login_required
def actividad(request):
    registros = SessionActivity.objects.filter(usuario=request.user)[:60]
    return render(request, 'core/actividad.html', {'registros': registros})


@login_required
def cerrar_sesion_todos(request):
    """Invalida todas las sesiones del usuario excepto la actual."""
    if not request.method == 'POST':
        return redirect('core:home')
    sesiones = __import__('django.contrib.sessions.models', fromlist=['Session']).Session.objects
    count = 0
    sesion_actual = request.session.session_key
    for s in sesiones.all():
        try:
            data = s.get_decoded()
        except Exception:
            continue
        if data.get('_auth_user_id') == str(request.user.id) and s.session_key != sesion_actual:
            s.delete()
            count += 1
    messages.success(request, f'Sesiones cerradas en {count} dispositivos.')
    return redirect('core:home')


@login_required
def auditoria_log(request):
    """Trazabilidad completa de todas las operaciones. Solo superusuarios."""
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para ver la trazabilidad.')
        return redirect('core:home')

    registros = RegistroAuditoria.objects.select_related('usuario')

    accion = request.GET.get('accion', '')
    modelo = request.GET.get('modelo', '')
    usuario = request.GET.get('usuario', '')

    if accion:
        registros = registros.filter(accion=accion)
    if modelo:
        registros = registros.filter(modelo__icontains=modelo)
    if usuario:
        registros = registros.filter(usuario__username__icontains=usuario)

    num_registros = registros.count()
    registros = registros.order_by('-timestamp')
    filtros = {}
    if accion:
        filtros['accion'] = accion
    if modelo:
        filtros['modelo'] = modelo
    if usuario:
        filtros['usuario'] = usuario
    page_obj = Paginator(registros, 5).get_page(request.GET.get('page'))

    # Modelos con actividad para el filtro desplegable
    modelos = (RegistroAuditoria.objects
               .order_by('modelo').values_list('modelo', flat=True).distinct())

    return render(request, 'core/auditoria_log.html', {
        'page_obj': page_obj,
        'num_registros': num_registros,
        'accion': accion,
        'modelo': modelo,
        'usuario': usuario,
        'modelos': modelos,
        'acciones': RegistroAuditoria.ACCIONES,
        'filtros': filtros,
    })