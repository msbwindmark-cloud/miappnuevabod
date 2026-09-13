"""Context processors globales para exponer ajustes en las plantillas."""

from django.conf import settings


def global_settings(request):
    return {'settings': settings}