"""
Señales de trazabilidad: registran automáticamente TODA operación CRUD
sobre los modelos de negocio (creación, modificación, eliminación).
Requiere el middleware AuditoriaRequestMiddleware para conocer el autor.
"""

from django.apps import apps
from django.db import models
from django.db.models.signals import post_save, pre_delete, pre_save

from .models import RegistroAuditoria
from .middleware import get_client_ip, get_request, get_user_agent


def _modelos_auditables():
    """Modelos de negocio + usuario/grupo de autenticación."""
    modelos = []
    for app_label, nombre in [
        ('caja', 'CierreCaja'), ('caja', 'PagoPersonal'), ('caja', 'Empleado'),
        ('inventario', 'Categoria'), ('inventario', 'Proveedor'),
        ('inventario', 'Producto'), ('inventario', 'ConteoStock'),
        ('inventario', 'ConteoStockLinea'),
        ('pedidos', 'Pedido'), ('pedidos', 'PedidoLinea'),
        ('core', 'LoginAttempt'),
        ('auth', 'User'), ('auth', 'Group'),
    ]:
        try:
            modelos.append(apps.get_model(app_label, nombre))
        except LookupError:
            pass
    return modelos


MODELOS_AUDITAR = _modelos_auditables()


def _etiqueta_modelo(sender):
    return f'{sender._meta.app_label}.{sender._meta.model_name}'


def _registrar(request, accion, sender, instance, cambios=''):
    try:
        objeto = str(instance)[:200]
    except Exception:
        objeto = f'{_etiqueta_modelo(sender)} #{instance.pk}'
    RegistroAuditoria.objects.create(
        usuario=request.user if (request and request.user.is_authenticated) else None,
        accion=accion,
        modelo=_etiqueta_modelo(sender),
        objeto_id=instance.pk,
        objeto=objeto,
        cambios=cambios,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )


def auditar_pre_save(sender, instance, **kwargs):
    """Snapshot en pre_save para saber qué campos cambian realmente."""
    if sender not in MODELOS_AUDITAR or isinstance(instance, RegistroAuditoria):
        return
    cambios = None  # None => objeto nuevo (sin pk)
    if instance.pk:
        try:
            anterior = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            anterior = None
        if anterior is not None:
            cambios = {}
            for f in sender._meta.fields:
                nombre = f.name
                nuevo = getattr(instance, nombre)
                previo = getattr(anterior, nombre)
                if isinstance(nuevo, models.Model):
                    nuevo = nuevo.pk
                if isinstance(previo, models.Model):
                    previo = previo.pk
                if nuevo != previo:
                    cambios[f.verbose_name or nombre] = (previo, nuevo)
    setattr(instance, '_audit_cambios', cambios)


def auditar_post_save(sender, instance, created, **kwargs):
    if sender not in MODELOS_AUDITAR or isinstance(instance, RegistroAuditoria):
        return
    request = get_request()
    if created:
        _registrar(request, 'creacion', sender, instance)
        return
    cambios = getattr(instance, '_audit_cambios', None)
    if cambios is None:
        return
    if not cambios:
        return  # sin cambios reales: evita ruido
    detalle = '\n'.join(
        f'• {campo}: {previo} → {nuevo}' for campo, (previo, nuevo) in cambios.items()
    )
    _registrar(request, 'modificacion', sender, instance, detalle)


def auditar_pre_delete(sender, instance, **kwargs):
    if sender not in MODELOS_AUDITAR or isinstance(instance, RegistroAuditoria):
        return
    request = get_request()
    _registrar(request, 'eliminacion', sender, instance)


for _sender in MODELOS_AUDITAR:
    pre_save.connect(auditar_pre_save, sender=_sender, weak=False)
    post_save.connect(auditar_post_save, sender=_sender, weak=False)
    pre_delete.connect(auditar_pre_delete, sender=_sender, weak=False)