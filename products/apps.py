from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'

    def ready(self):
        # اینجا سیگنال‌ها را بارگذاری می‌کنیم تا هنگام start سرور فعال شوند
        import products.signals
