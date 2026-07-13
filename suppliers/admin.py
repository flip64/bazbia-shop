from django.contrib import admin
from suppliers.models import Supplier, SupplierOffer, SupplierPriceHistory

admin.site.register(Supplier)
admin.site.register(SupplierOffer)
admin.site.register(SupplierPriceHistory)
