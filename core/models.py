"""
Modelos de Core: registro de intentos de login (protección de fuerza bruta)
y actividades de sesión.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class LoginAttempt(models.Model):
    """Registro de cada intento de acceso para throttling y auditoría."""

    username = models.CharField(max_length=150, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Intento de login'
        verbose_name_plural = 'Intentos de login'

    @classmethod
    def recent_failures(cls, username, ip_address=None, minutes=settings.LOGIN_LOCK_MINUTES):
        """Nº de fallos recientes para el usuario + IP dado en la ventana indicada."""
        since = timezone.now() - timezone.timedelta(minutes=minutes)
        qs = cls.objects.filter(success=False, timestamp__gte=since, username__iexact=username)
        if ip_address:
            qs = qs.filter(ip_address=ip_address)
        else:
            qs = qs.filter(ip_address='')
        return qs.count()

    @classmethod
    def is_locked(cls, username, ip_address=None):
        return cls.recent_failures(username, ip_address) >= settings.LOGIN_MAX_ATTEMPTS


class SessionActivity(models.Model):
    """Registro de accesos exitosos y cierre de sesión de cada usuario."""

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='actividades')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    evento = models.CharField(max_length=20, default='login')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Actividad de sesión'
        verbose_name_plural = 'Actividades de sesión'


class RegistroAuditoria(models.Model):
    """Trazabilidad de TODAS las operaciones CRUD realizadas en el sistema."""

    ACCIONES = [
        ('creacion', 'Creación'),
        ('modificacion', 'Modificación'),
        ('eliminacion', 'Eliminación'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('exportacion', 'Exportación'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='auditorias'
    )
    accion = models.CharField(max_length=20, choices=ACCIONES, db_index=True)
    modelo = models.CharField('Modelo', max_length=80)
    objeto_id = models.PositiveBigIntegerField(null=True, blank=True)
    objeto = models.CharField('Objeto', max_length=200, blank=True)
    cambios = models.TextField(blank=True, help_text='Detalle de los campos modificados.')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Registro de auditoría'
        verbose_name_plural = 'Registro de auditoría'
        indexes = [models.Index(fields=['modelo', 'objeto_id'])]

    def __str__(self):
        return f'{self.get_accion_display()} · {self.modelo} #{self.objeto_id} · {self.usuario} · {self.timestamp:%d/%m/%Y %H:%M}'