from django.contrib import admin

from contact.models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "phone",
        "subject_display",
        "order_number",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "subject",
        "created_at",
    )

    search_fields = (
        "name",
        "phone",
        "email",
        "message",
        "order_number",
    )

    readonly_fields = (
        "user",
        "name",
        "phone",
        "email",
        "subject",
        "order_number",
        "message",
        "ip_address",
        "user_agent",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 30

    fieldsets = (
        (
            "اطلاعات پیام",
            {
                "fields": (
                    "name",
                    "phone",
                    "email",
                    "subject",
                    "order_number",
                    "message",
                ),
            },
        ),
        (
            "مدیریت",
            {
                "fields": (
                    "status",
                    "admin_note",
                ),
            },
        ),
        (
            "اطلاعات سیستمی",
            {
                "classes": (
                    "collapse",
                ),
                "fields": (
                    "user",
                    "ip_address",
                    "user_agent",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(
        description="موضوع"
    )
    def subject_display(self, obj):
        return obj.get_subject_display()
