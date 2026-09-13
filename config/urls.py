"""URL configuration for config project."""

from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from core.sites import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('core.urls')),
    path('caja/', include('caja.urls')),
    path('inventario/', include('inventario.urls')),
    path('pedidos/', include('pedidos.urls')),
    path('auditoria/', include('auditoria.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)