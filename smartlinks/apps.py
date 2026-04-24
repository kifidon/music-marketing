from django.apps import AppConfig


class SmartlinksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "smartlinks"
    verbose_name = "Smart links"

    def ready(self):
        from smartlinks import signals  # noqa: F401
