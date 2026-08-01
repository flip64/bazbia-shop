from django.apps import AppConfig


class TorobIntegrationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "torob_integration"
    verbose_name = "اتصال به ترب"

    def ready(self):
        import torob_integration.signals  # noqa: F401
