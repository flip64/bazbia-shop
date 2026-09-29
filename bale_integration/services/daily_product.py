"""مسیر سازگار با نسخه‌های قبلی؛ منطق اصلی در سرویس مرکزی محصولات است."""

from products.services.social_product_post import (
    build_product_post,
    final_price,
    select_product_by_id,
    select_random_product,
)

from bale_integration.models import BaleProductPost


def select_daily_product(exclude_days=30, post_model=BaleProductPost):
    return select_random_product(post_model, exclude_days=exclude_days)


__all__ = [
    "build_product_post",
    "final_price",
    "select_daily_product",
    "select_product_by_id",
    "select_random_product",
]
