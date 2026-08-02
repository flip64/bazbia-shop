import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazbia_shop.settings")
django.setup()



from suppliers.fetchers.pakhshabdi.sync.json_loader  import load_available_products 
from suppliers.fetchers.pakhshabdi.sync.find_offer import find_offer_by_url
from suppliers.fetchers.pakhshabdi.sync.json_loader import load_available_products 
from suppliers.fetchers.pakhshabdi.sync.find_offer import find_offer_by_url
from suppliers.fetchers.pakhshabdi.sync.create_product_from_url import create_product_from_url
from suppliers.fetchers.pakhshabdi.sync.updater import update_offer




products = load_available_products()

for item in products:
    offer = find_offer_by_url(item["url"])

    if offer:
        update_offer(
            offer,
            price=item["price"],
            stock=item["stock"],
        )
    else:
        create_product_from_url(item["url"])