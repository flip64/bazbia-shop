

from suppliers.models import Supplier
from products.models import Product
from products.services.create_product_from_url import create_product_from_url
import os
import sys
import django

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../")
)
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazbia_shop.settings")
django.setup()

supplier = Supplier.objects.create(
            name="پخش عبدی",
        )
url = "https://pakhshabdi.com/product/..."  # آدرس واقعی یک محصول
product = create_product_from_url(url)
