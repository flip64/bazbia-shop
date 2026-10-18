from django.contrib import admin

# Register your models here.
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "status", "amount", "requires_review", "paid_at")
    list_filter = ("requires_review", "status", "gateway")
    search_fields = ("authority", "tracking_code", "reference_id")
    readonly_fields = tuple(field.name for field in Payment._meta.fields)
    list_select_related = ("order",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
