
from django.contrib import admin
from orders import  models


admin.site.register(models.Order)
admin.site.register(models.OrderItem)
admin.site.register(models.SalesSummary)
admin.site.register(models.Cart)
admin.site.register(models.CartItem)

