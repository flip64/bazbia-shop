from datetime import timedelta
from uuid import uuid4

from django.utils import timezone


class FixedShippingQuoteService:
    """
    سرویس موقت محاسبه هزینه ارسال فروشگاه بازبیا.

    فعلاً برای تمام سفارش‌ها یک هزینه ثابت برمی‌گرداند.
    بعداً منطق این سرویس با موتور بسته‌بندی و محاسبه
    واقعی هزینه ارسال جایگزین خواهد شد.

    تمام مبلغ‌ها در API به تومان هستند.
    """

    SHIPPING_COST_TOMAN = 195_000
    QUOTE_EXPIRATION_MINUTES = 30

    METHOD_CODE = "fixed_standard"
    METHOD_TITLE = "ارسال استاندارد"
    METHOD_DESCRIPTION = (
        "هزینه ارسال  و یسته بندی فعلاً به‌صورت ثابت محاسبه می‌شود."
    )

    ESTIMATED_MIN_DAYS = 3
    ESTIMATED_MAX_DAYS = 7

    def __init__(self, cart, address):
        self.cart = cart
        self.address = address

    def calculate(self) -> dict:
        expires_at = timezone.now() + timedelta(
            minutes=self.QUOTE_EXPIRATION_MINUTES
        )

        return {
            "quote_id": str(uuid4()),

            "address": {
                "id": self.address.id,
                "province": self.address.province,
                "city": self.address.city,
            },

            "packing": {
                "status": "temporary_fixed_rate",
                "package_count": 1,
                "total_items_weight": None,
                "total_carton_weight": None,
                "chargeable_weight": None,
            },

            "methods": [
                {
                    "code": self.METHOD_CODE,
                    "title": self.METHOD_TITLE,
                    "description": (
                        self.METHOD_DESCRIPTION
                    ),
                    "cost": self.SHIPPING_COST_TOMAN,
                    "currency": "IRR",
                    "estimated_days": {
                        "min": self.ESTIMATED_MIN_DAYS,
                        "max": self.ESTIMATED_MAX_DAYS,
                    },
                }
            ],

            "expires_at": expires_at.isoformat(),
        }
