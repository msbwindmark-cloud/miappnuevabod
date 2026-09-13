"""Middleware de trazabilidad: guarda la request actual en un contexto por hilo
para que las señales de auditoría puedan conocer usuario e IP sin tocar cada vista.
"""

import contextvars
import threading

_request = contextvars.ContextVar('request_actual', default=None)
_lock = threading.Lock()


class AuditoriaRequestMiddleware:
    """Almacena la request actual en un ContextVar accesible desde las señales."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _request.set(request)
        try:
            return self.get_response(request)
        finally:
            _request.reset(token)


def get_request():
    """Devuelve la request actual (o None fuera de una petición HTTP)."""
    return _request.get()


def get_client_ip(request):
    if request is None:
        return None
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or None


def get_user_agent(request):
    if request is None:
        return ''
    return request.META.get('HTTP_USER_AGENT', '')[:500]