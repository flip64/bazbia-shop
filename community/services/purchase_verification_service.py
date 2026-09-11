from orders.models import Order, OrderItem


class PurchaseVerificationService:
    """
    سرویس تشخیص خرید واقعی یک محصول توسط کاربر.

    خرید معتبر سفارشی است که حداقل به یکی از وضعیت‌های:
    paid / shipped / completed
    رسیده باشد.
    """

    VALID_ORDER_STATUSES = (
        Order.STATUS_PAID,
        Order.STATUS_SHIPPED,
        Order.STATUS_COMPLETED,
    )

    @classmethod
    def has_user_purchased_product(cls, *, user, product) -> bool:
        """
        بررسی می‌کند آیا کاربر محصول موردنظر را
        در یک سفارش معتبر خریداری کرده است یا خیر.
        """

        if not user:
            return False

        if not getattr(user, "is_authenticated", False):
            return False

        if not product:
            return False

        return OrderItem.objects.filter(
            order__user=user,
            order__status__in=cls.VALID_ORDER_STATUSES,
            variant__product=product,
        ).exists()