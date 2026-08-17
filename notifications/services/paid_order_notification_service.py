import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from notifications.models import NotificationDelivery
from notifications.services.email.order_email_service import (
    send_paid_order_email,
)
from notifications.services.sms import send_paid_order_sms
from orders.models import Order
from payments.models import Payment


logger = logging.getLogger(__name__)


def _customer_phone(order: Order) -> str:
    try:
        phone = order.user.customer_profile.phone
    except Exception:
        phone = ""

    if phone:
        return str(phone).strip()

    snapshot = order.shipping_address_snapshot or {}
    return str(snapshot.get("recipient_phone", "")).strip()


def _customer_name(order: Order) -> str:
    full_name = order.user.get_full_name().strip()
    if full_name:
        return full_name

    snapshot = order.shipping_address_snapshot or {}
    recipient_name = str(
        snapshot.get("recipient_name", "")
    ).strip()
    if recipient_name:
        return recipient_name

    return str(order.user.get_username()).strip() or "مشتری"


def _delivery(
    *,
    order: Order,
    payment: Payment,
    channel: str,
    recipient: str,
) -> NotificationDelivery:
    delivery, _ = NotificationDelivery.objects.get_or_create(
        payment=payment,
        event=NotificationDelivery.Event.ORDER_PAID,
        channel=channel,
        defaults={
            "order": order,
            "recipient": recipient,
        },
    )

    if delivery.recipient != recipient:
        delivery.recipient = recipient
        delivery.save(update_fields=["recipient", "updated_at"])

    return delivery


def _mark_attempt(delivery: NotificationDelivery) -> None:
    delivery.status = NotificationDelivery.Status.PENDING
    delivery.attempt_count += 1
    delivery.last_error = ""
    delivery.save(
        update_fields=[
            "status",
            "attempt_count",
            "last_error",
            "updated_at",
        ]
    )


def _mark_sent(
    delivery: NotificationDelivery,
    provider_response=None,
) -> None:
    delivery.status = NotificationDelivery.Status.SENT
    delivery.provider_response = provider_response or {}
    delivery.last_error = ""
    delivery.sent_at = timezone.now()
    delivery.save(
        update_fields=[
            "status",
            "provider_response",
            "last_error",
            "sent_at",
            "updated_at",
        ]
    )


def _mark_failed(
    delivery: NotificationDelivery,
    error,
) -> None:
    delivery.status = NotificationDelivery.Status.FAILED
    delivery.last_error = str(error)
    delivery.save(
        update_fields=[
            "status",
            "last_error",
            "updated_at",
        ]
    )


def notify_paid_order(*, order_id: int, payment_id: int) -> dict:
    """ارسال اعلان‌های پرداخت موفق، با قابلیت تلاش مجدد امن."""

    order = (
        Order.objects
        .select_related("user", "user__customer_profile")
        .get(pk=order_id)
    )
    payment = Payment.objects.get(pk=payment_id)

    if payment.order_id != order.id:
        raise ValueError("پرداخت متعلق به این سفارش نیست.")

    if (
        payment.status != Payment.Status.SUCCESSFUL
        or order.status != Order.STATUS_PAID
    ):
        logger.warning(
            "Paid notification skipped for unpaid order/payment. "
            "order_id=%s payment_id=%s",
            order_id,
            payment_id,
        )
        return {"sms": False, "admin_email": False}

    results = {"sms": False, "admin_email": False}

    phone = _customer_phone(order)
    sms_delivery = _delivery(
        order=order,
        payment=payment,
        channel=NotificationDelivery.Channel.SMS,
        recipient=phone,
    )

    if sms_delivery.status == NotificationDelivery.Status.SENT:
        results["sms"] = True
    elif not phone:
        _mark_failed(sms_delivery, "شماره موبایل مشتری موجود نیست.")
    else:
        _mark_attempt(sms_delivery)
        try:
            response = send_paid_order_sms(
                phone=phone,
                customer_name=_customer_name(order),
                order_id=order.id,
            )
        except Exception as error:
            logger.exception(
                "Failed to send paid order SMS. order_id=%s",
                order.id,
            )
            _mark_failed(sms_delivery, error)
        else:
            _mark_sent(sms_delivery, response)
            results["sms"] = True

    admin_recipient = str(
        getattr(settings, "DEFAULT_FROM_EMAIL", "") or ""
    ).strip()
    email_delivery = _delivery(
        order=order,
        payment=payment,
        channel=NotificationDelivery.Channel.ADMIN_EMAIL,
        recipient=admin_recipient,
    )

    if email_delivery.status == NotificationDelivery.Status.SENT:
        results["admin_email"] = True
    elif not admin_recipient:
        _mark_failed(email_delivery, "ایمیل مدیر تنظیم نشده است.")
    else:
        _mark_attempt(email_delivery)
        if send_paid_order_email(order.id, payment.id):
            _mark_sent(email_delivery)
            results["admin_email"] = True
        else:
            _mark_failed(email_delivery, "ارسال ایمیل مدیر ناموفق بود.")

    return results
