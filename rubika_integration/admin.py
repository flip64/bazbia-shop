from django.contrib import admin

from .models import RubikaProductPost


@admin.register(RubikaProductPost)
class RubikaProductPostAdmin(admin.ModelAdmin):
    list_display = (
        "publication_date",
        "cron_date",
        "product",
        "channel_id",
        "trigger",
        "is_successful",
        "attempt_count",
        "message_id",
    )
    list_filter = ("trigger", "is_successful", "publication_date")
    search_fields = ("product__name", "product__slug", "channel_id")
    readonly_fields = (
        "product",
        "publication_date",
        "cron_date",
        "channel_id",
        "trigger",
        "message_id",
        "is_successful",
        "attempt_count",
        "error_message",
        "created_at",
        "updated_at",
    )
