from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Núcleo (seguridad y trazabilidad)'

    def ready(self):
        # Activa las señales de auditoría sobre todos los CRUDs
        import core.signals  # noqa: F401