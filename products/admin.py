from django.contrib import admin

from .models import Product,ProductImage,ProductSpecification,ProductVariant,ProductVideo


admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ProductSpecification)
admin.site.register(ProductVariant)
admin.site.register(ProductVideo)

