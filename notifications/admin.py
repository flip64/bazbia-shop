from django.contrib import admin

from notifications.models import (
    NotificationDelivery,
)


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(
    admin.ModelAdmin
):
    list_display = (
        "id",
        "order",
        "payment",
        "event",
        "channel",
        "recipient",
        "status",
        "attempt_count",
        "sent_at",
    )

    list_filter = (
        "event",
        "channel",
        "status",
    )

    search_fields = (
        "recipient",
        "=order__id",
        "=payment__id",
        "payment__authority",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "sent_at",
        "provider_response",
        "last_error",
    )

    actions = (
        "retry_paid_order_notifications",
    )

    @admin.action(
        description=(
            "تلاش مجدد برای اعلان‌های انتخاب‌شده"
        )
    )
    def retry_paid_order_notifications(
        self,
        request,
        queryset,
    ):
        from notifications.services.paid_order_notification_service import (
            notify_paid_order,
        )

        payments = queryset.values_list(
            "order_id",
            "payment_id",
        ).distinct()

        retried = 0

        for order_id, payment_id in payments:
            notify_paid_order(
                order_id=order_id,
                payment_id=payment_id,
            )

            retried += 1

        self.message_user(
            request,
            (
                f"اعلان‌های {retried} پرداخت "
                "دوباره بررسی شدند."
            ),
        )
