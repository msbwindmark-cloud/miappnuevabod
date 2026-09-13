from django.contrib.admin import ModelAdmin
from django.contrib.admin.decorators import register

from core.sites import admin_site

from .models import LoginAttempt, RegistroAuditoria, SessionActivity


@register(RegistroAuditoria, site=admin_site)
class RegistroAuditoriaAdmin(ModelAdmin):
    list_display = ('timestamp', 'usuario', 'accion', 'modelo', 'objeto', 'ip_address')
    list_filter = ('accion', 'modelo', 'usuario')
    search_fields = ('objeto', 'modelo', 'usuario__username', 'ip_address')
    readonly_fields = ('usuario', 'accion', 'modelo', 'objeto_id', 'objeto', 'cambios',
                       'ip_address', 'user_agent', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@register(LoginAttempt, site=admin_site)
class LoginAttemptAdmin(ModelAdmin):
    list_display = ('username', 'success', 'ip_address', 'timestamp')
    list_filter = ('success',)
    search_fields = ('username', 'ip_address')
    ordering = ('-timestamp',)


@register(SessionActivity, site=admin_site)
class SessionActivityAdmin(ModelAdmin):
    list_display = ('usuario', 'evento', 'ip_address', 'timestamp')
    list_filter = ('evento',)
    search_fields = ('usuario__username', 'ip_address')
    ordering = ('-timestamp',)