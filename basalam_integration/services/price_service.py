# basalam_integration/services/price_service.py

from decimal import Decimal, ROUND_CEILING

from django.conf import settings

from .category_service import get_commission_percent


def calculate_price_with_commission(
    price,
    commission_percent,
    *,
    rounding: int | None = None,
) -> int:
    """
    محاسبه قیمتی که پس از کسر کارمزد باسلام،
    تقریباً برابر قیمت فروش بازبیا باقی بماند.
    """

    price = Decimal(str(price))
    commission_percent = Decimal(
        str(commission_percent)
    )

    if rounding is None:
        rounding = settings.BASALAM_PRICE_ROUNDING

    rounding = int(rounding)

    if price < 0:
        raise ValueError(
            "قیمت نمی‌تواند منفی باشد."
        )

    if not (
        Decimal("0")
        <= commission_percent
        < Decimal("100")
    ):
        raise ValueError(
            "درصد کارمزد باید بین صفر "
            "و کمتر از صد باشد."
        )

    if rounding <= 0:
        raise ValueError(
            "مقدار گردکردن باید بیشتر از صفر باشد."
        )

    commission_rate = (
        commission_percent / Decimal("100")
    )

    calculated_price = (
        price
        / (
            Decimal("1")
            - commission_rate
        )
    )

    rounding_decimal = Decimal(str(rounding))

    rounded_price = (
        calculated_price / rounding_decimal
    ).quantize(
        Decimal("1"),
        rounding=ROUND_CEILING,
    ) * rounding_decimal

    return int(rounded_price)


def get_variant_bazbia_price(variant) -> Decimal:
    """
    دریافت قیمت فعال واریانت بازبیا.
    """

    if variant.discount_price is not None:
        return variant.discount_price

    return variant.price


def calculate_variant_basalam_price(variant) -> int:
    """
    محاسبه قیمت باسلام برای واریانت.
    """

    bazbia_price = get_variant_bazbia_price(
        variant
    )

    commission_percent = get_commission_percent(
        variant.product
    )

    return calculate_price_with_commission(
        bazbia_price,
        commission_percent,
    )
