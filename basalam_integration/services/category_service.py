# basalam_integration/services/category_service.py

from decimal import Decimal

from django.conf import settings

from basalam_integration.models import (
    BasalamCategoryMapping,
)


def get_product_category_mapping(product):
    """
    نگاشت فعال دسته محصول بازبیا به دسته باسلام.
    """

    if product.category_id is None:
        return None

    return (
        BasalamCategoryMapping.objects
        .select_related("basalam_category")
        .filter(
            bazbia_category_id=product.category_id,
            is_active=True,
            basalam_category__is_active=True,
        )
        .first()
    )


def get_basalam_category(product):
    """
    دریافت دسته باسلام متناظر با محصول.
    """

    mapping = get_product_category_mapping(product)

    if mapping is None:
        return None

    return mapping.basalam_category


def get_commission_percent(product) -> Decimal:
    """
    دریافت کارمزد دسته محصول.

    اگر نگاشت دسته وجود نداشته باشد، نرخ پیش‌فرض
    تنظیم‌شده در settings استفاده می‌شود.
    """

    basalam_category = get_basalam_category(product)

    if basalam_category is None:
        return Decimal(
            str(
                settings
                .BASALAM_DEFAULT_COMMISSION_PERCENT
            )
        )

    return basalam_category.commission_percent
