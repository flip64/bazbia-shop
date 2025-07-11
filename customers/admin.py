from django.contrib import admin
from .models import Customer, CustomerLevel, CustomerGuarantee


admin.site.register(Customer)
admin.site.register(CustomerLevel)
admin.site.register(CustomerGuarantee)

