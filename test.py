import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazbia_shop.settings")
django.setup()

from suppliers.models import Supplier
from products.services.create_product_from_url import create_product_from_url

supplier = Supplier.objects.get(name="پخش عبدی")
url = "https://pakhshabdi.com/product/%da%86%d8%b3%d8%a8-%d8%a2%d9%84%d9%88%d9%85%db%8c%d9%86%db%8c%d9%88%d9%85%db%8c-%d8%af%d9%88%d8%b1-%da%af%d8%a7%d8%b2-5-%d8%b3%d8%a7%d9%86%d8%aa/"  # آدرس واقعی محصول

product = create_product_from_url(url, supplier)

print("=" * 50)
print("Product ID:", product.id)
print("Product Name:", product.name)
print("=" * 50)
