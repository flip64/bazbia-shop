from django.contrib import admin

from .models import BaleProductPost


@admin.register(BaleProductPost)
class BaleProductPostAdmin(admin.ModelAdmin):
    list_display = (
        "publication_date",
        "product",
        "channel_id",
        "is_successful",
        "attempt_count",
        "message_id",
    )
    list_filter = ("is_successful", "publication_date")
    search_fields = ("product__name", "product__slug", "channel_id")
    readonly_fields = (
        "product",
        "publication_date",
        "channel_id",
        "message_id",
        "is_successful",
        "attempt_count",
        "error_message",
        "created_at",
        "updated_at",
    )
