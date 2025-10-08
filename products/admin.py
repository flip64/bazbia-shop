from django.contrib import admin

from .models import Product,ProductImage,ProductSpecification,ProductVariant,ProductVideo 
from .models import  Category,SpecialProduct,AttributeValue,Attribute



admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(ProductSpecification)
admin.site.register(ProductVariant)
admin.site.register(ProductVideo)
admin.site.register(SpecialProduct)
admin.site.register(Category)
admin.site.register(Attribute)
admin.site.register(AttributeValue)



    
