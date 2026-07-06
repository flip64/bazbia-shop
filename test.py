import os
import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "bazbia_shop.settings"
)

django.setup()


from suppliers.fetchers.pakhshabdi.sync_product_abdi import  sync_products
sync_products()
