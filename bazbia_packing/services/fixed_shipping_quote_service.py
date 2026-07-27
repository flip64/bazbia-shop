from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.utils import timezone


class FixedShippingQuoteService:
    """
    سرویس موقت محاسبه هزینه ارسال.

    این سرویس بعداً با موتور واقعی بسته‌بندی و
    محاسبه هزینه پستی جایگزین می‌شود.

    مبلغ‌ها در API به ریال هستند.
    """

    DEFAULT_COST_RIAL = 850_000
    DEFAULT_EXPIRATION_MINUTES = 30

    METHOD_CODE = "fixed_standard"
    METHOD_TITLE = "ارسال استاندارد"
    METHOD_DESCRIPTION = (
        "هزینه ارسال فعلاً به‌صورت ثابت محاسبه می‌شود."
    )

    def __init__(self, cart, address):
        self.cart = cart
        self.address = address

    def calculate(self) -> dict:
        cost = getattr(
            settings,
            "BAZBIA_FIXED_SHIPPING_COST_RIAL",
            self.DEFAULT_COST_RIAL,
        )

        expires_at = timezone.now() + timedelta(
            minutes=self.DEFAULT_EXPIRATION_MINUTES
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
                    "cost": int(cost),
                    "currency": "IRR",
                    "estimated_days": {
                        "min": 3,
                        "max": 7,
                    },
                }
            ],
            "expires_at": expires_at.isoformat(),
        }
