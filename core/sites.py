"""
Sitio de administración personalizado de Chill Out La Bodeguita.

Registrado en 'core.sites.admin_site' y usado por cada app en su 'admin.py'.
Acceso restringido a usuarios superadmin (is_superuser=True).
"""

from django.contrib.admin import AdminSite
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User


class ChillOutAdminSite(AdminSite):
    site_header = 'Chill Out La Bodeguita'
    site_title = 'Administración'
    index_title = 'Panel de administración'

    def has_permission(self, request):
        return bool(request.user.is_active and request.user.is_superuser)


admin_site = ChillOutAdminSite(name='admin')

# Los usuarios y grupos están registrados en el sitio admin predeterminado
# de Django; hay que registrarlos también en el sitio personalizado.
admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)