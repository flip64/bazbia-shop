import random
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Prefetch
from django.utils import timezone
from django.utils.html import strip_tags

from products.models import Product, ProductVariant
from products.services.variant_stock import VariantStockService

from bale_integration.models import BaleProductPost


def final_price(variant):
    if (
        variant.discount_price is not None
        and Decimal("0") < variant.discount_price < variant.price
    ):
        return variant.discount_price
    return variant.price


def select_daily_product(exclude_days=30):
    cutoff = timezone.localdate() - timedelta(days=exclude_days)
    recent_product_ids = BaleProductPost.objects.filter(
        is_successful=True,
        publication_date__gte=cutoff,
    ).values_list("product_id", flat=True)

    available_variants = VariantStockService.filter_available(
        ProductVariant.objects.filter(price__gt=0)
    ).order_by("price", "id")

    candidates = list(
        Product.objects.filter(is_active=True, variants__isnull=False)
        .exclude(id__in=recent_product_ids)
        .prefetch_related(
            "images",
            Prefetch(
                "variants",
                queryset=available_variants,
                to_attr="available_bale_variants",
            ),
        )
        .distinct()
    )
    random.shuffle(candidates)

    for product in candidates:
        variants = product.available_bale_variants
        images = list(product.images.all())
        image = next((item for item in images if item.is_main), None)
        image = image or (images[0] if images else None)
        if variants and image and (image.image or image.source_url):
            return product, variants, image

    return None, [], None


def build_product_post(product, variants, image):
    lowest_price = min(final_price(variant) for variant in variants)
    has_discount = any(final_price(variant) < variant.price for variant in variants)

    description = strip_tags(product.description or "")
    description = " ".join(description.split())
    if len(description) > 220:
        description = f"{description[:217].rstrip()}..."

    frontend_url = settings.BALE_FRONTEND_URL.rstrip("/")
    product_url = f"{frontend_url}/product/{product.slug}"
    if image.image:
        backend_url = settings.BALE_BACKEND_URL.rstrip("/")
        photo_url = f"{backend_url}{image.image.url}"
    else:
        photo_url = image.source_url

    lines = ["🛍 پیشنهاد امروز بازبیا", "", product.name]
    if description:
        lines.extend(["", description])
    lines.extend([
        "",
        f"💰 از {int(lowest_price):,} تومان",
        "🔥 دارای تخفیف" if has_discount else "✅ موجود در فروشگاه",
        "",
        "بازبیا؛ انتخابی که تکرار می‌کنید",
    ])
    return photo_url, "\n".join(lines), product_url
