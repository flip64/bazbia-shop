from django.contrib import admin
from customers import models


admin.site.register(models.Customer)
admin.site.register(models.CustomerLevel)
admin.site.register(models.CustomerGuarantee)
admin.site.register(models.Status)
admin.site.register(models.CustomerState)