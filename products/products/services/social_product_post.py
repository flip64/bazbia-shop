import random
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Prefetch
from django.utils import timezone
from django.utils.html import strip_tags

from products.models import Product, ProductVariant
from products.services.variant_stock import VariantStockService


def final_price(variant):
    if (
        variant.discount_price is not None
        and Decimal("0") < variant.discount_price < variant.price
    ):
        return variant.discount_price
    return variant.price


def _available_variants():
    return VariantStockService.filter_available(
        ProductVariant.objects.filter(price__gt=0)
    ).order_by("price", "id")


def _product_payload(product):
    variants = product.available_social_variants
    images = list(product.images.all())
    image = next((item for item in images if item.is_main), None)
    image = image or (images[0] if images else None)
    if not variants or not image or not (image.image or image.source_url):
        return None, [], None
    return product, variants, image


def select_random_product(post_model, exclude_days=30):
    """انتخاب تصادفی با سابقه مستقل شبکه‌ای که مدل آن ارسال شده است."""
    cutoff = timezone.localdate() - timedelta(days=exclude_days)
    recent_product_ids = post_model.objects.filter(
        is_successful=True,
        trigger=post_model.TRIGGER_CRON,
        publication_date__gte=cutoff,
    ).values_list("product_id", flat=True)

    candidates = list(
        Product.objects.filter(is_active=True, variants__isnull=False)
        .exclude(id__in=recent_product_ids)
        .prefetch_related(
            "images",
            Prefetch(
                "variants",
                queryset=_available_variants(),
                to_attr="available_social_variants",
            ),
        )
        .distinct()
    )
    random.shuffle(candidates)
    for product in candidates:
        payload = _product_payload(product)
        if payload[0] is not None:
            return payload
    return None, [], None


def select_random_product_without_daily_limit(post_model, exclude_days=30):
    """انتخاب تصادفی دستی بدون سقف روزانه، با جلوگیری از تکرار محصول."""
    cutoff = timezone.localdate() - timedelta(days=exclude_days)
    recent_product_ids = post_model.objects.filter(
        is_successful=True,
        publication_date__gte=cutoff,
    ).values_list("product_id", flat=True)

    candidates = list(
        Product.objects.filter(is_active=True, variants__isnull=False)
        .exclude(id__in=recent_product_ids)
        .prefetch_related(
            "images",
            Prefetch(
                "variants",
                queryset=_available_variants(),
                to_attr="available_social_variants",
            ),
        )
        .distinct()
    )
    random.shuffle(candidates)
    for product in candidates:
        payload = _product_payload(product)
        if payload[0] is not None:
            return payload
    return None, [], None


def select_product_by_id(product_id):
    """دریافت محصول مشخص برای ارسال دستی، بدون بررسی سابقه زمانی."""
    try:
        product = (
            Product.objects.filter(is_active=True)
            .prefetch_related(
                "images",
                Prefetch(
                    "variants",
                    queryset=_available_variants(),
                    to_attr="available_social_variants",
                ),
            )
            .get(pk=product_id)
        )
    except Product.DoesNotExist:
        return None, [], None
    return _product_payload(product)


def build_product_post(product, variants, image):
    lowest_price = min(final_price(variant) for variant in variants)
    has_discount = any(final_price(variant) < variant.price for variant in variants)

    description = strip_tags(product.description or "")
    description = " ".join(description.split())
    if len(description) > 220:
        description = f"{description[:217].rstrip()}..."

    frontend_url = settings.SOCIAL_FRONTEND_URL.rstrip("/")
    product_url = f"{frontend_url}/product/{product.slug}"
    if image.image:
        backend_url = settings.SOCIAL_BACKEND_URL.rstrip("/")
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
