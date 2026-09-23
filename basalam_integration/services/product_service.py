from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import transaction
from django.utils import timezone

from basalam_integration.models import (
    BasalamProductMapping,
    BasalamVariationMapping,
)

from .category_service import get_basalam_category
from .client import BasalamClient
from .file_service import upload_product_images
from .price_service import calculate_variant_basalam_price
from .stock_service import calculate_variant_basalam_stock


BASALAM_STATUS_PUBLISHED = 2976
BASALAM_STATUS_UNPUBLISHED = 3790
BASALAM_UNIT_NUMERIC = 6304


@dataclass(frozen=True)
class ProductPublishResult:
    product_id: int
    basalam_product_id: int
    variation_count: int
    image_count: int
    published: bool


def _positive_setting(name: str) -> int:
    value = int(getattr(settings, name))
    if value <= 0:
        raise ImproperlyConfigured(
            f"تنظیم {name} باید بزرگ‌تر از صفر باشد."
        )
    return value


def _variant_properties(variant) -> list[dict[str, str]]:
    return [
        {
            "property": attribute_value.attribute.name,
            "value": attribute_value.value,
        }
        for attribute_value in variant.attributes.all()
    ]


def validate_product_for_basalam(product) -> list:
    if not product.is_active:
        raise ValidationError("محصول بازبیا غیرفعال است.")

    if BasalamProductMapping.objects.filter(product=product).exists():
        raise ValidationError(
            "این محصول قبلاً به یک محصول باسلام متصل شده است."
        )

    basalam_category = get_basalam_category(product)
    if basalam_category is None:
        raise ValidationError(
            "دسته محصول به دسته فعالی در باسلام نگاشت نشده است."
        )

    variants = list(
        product.variants.prefetch_related("attributes__attribute")
        .order_by("id")
    )
    if not variants:
        raise ValidationError("محصول هیچ واریانتی ندارد.")

    if len(variants) > 1:
        for variant in variants:
            if not _variant_properties(variant):
                raise ValidationError(
                    f"واریانت {variant.sku} ویژگی رنگ/سایز ندارد."
                )

    return variants


def build_product_payload(
    product,
    *,
    image_ids: list[int | str],
    published: bool = False,
) -> dict[str, Any]:
    variants = validate_product_for_basalam(product)
    basalam_category = get_basalam_category(product)

    if not image_ids:
        raise ValidationError(
            "برای ایجاد محصول حداقل یک تصویر باسلام لازم است."
        )

    image_ids = [int(image_id) for image_id in image_ids]
    keywords = list(
        product.tags.order_by("name").values_list("name", flat=True)
    )
    description = (product.description or product.name).strip()

    payload: dict[str, Any] = {
        "name": product.name.strip(),
        "description": description,
        "brief": description[:250],
        "category_id": basalam_category.basalam_category_id,
        "status": (
            BASALAM_STATUS_PUBLISHED
            if published
            else BASALAM_STATUS_UNPUBLISHED
        ),
        "preparation_days": _positive_setting(
            "BASALAM_DEFAULT_PREPARATION_DAYS"
        ),
        "weight": _positive_setting("BASALAM_DEFAULT_WEIGHT"),
        "package_weight": _positive_setting(
            "BASALAM_DEFAULT_PACKAGE_WEIGHT"
        ),
        "photo": image_ids[0],
        "photos": image_ids,
        "keywords": keywords or None,
        "unit_quantity": 1,
        "unit_type": BASALAM_UNIT_NUMERIC,
        "is_wholesale": False,
    }

    if len(variants) == 1:
        variant = variants[0]
        payload.update(
            {
                "primary_price": calculate_variant_basalam_price(variant),
                "stock": calculate_variant_basalam_stock(variant),
                "sku": variant.sku,
            }
        )
    else:
        payload["variants"] = [
            {
                "primary_price": calculate_variant_basalam_price(variant),
                "stock": calculate_variant_basalam_stock(variant),
                "sku": variant.sku,
                "properties": _variant_properties(variant),
            }
            for variant in variants
        ]

    return {key: value for key, value in payload.items() if value is not None}


def _response_data(response: dict[str, Any]) -> dict[str, Any]:
    for key in ("data", "result"):
        nested = response.get(key)
        if isinstance(nested, dict):
            return nested
    return response


def _save_variation_mappings(product_mapping, variants, response_data):
    response_variants = response_data.get("variants") or []
    by_sku = {
        str(item.get("sku")): item
        for item in response_variants
        if isinstance(item, dict) and item.get("sku")
    }

    for variant in variants:
        item = by_sku.get(str(variant.sku))
        if not item or not item.get("id"):
            continue
        BasalamVariationMapping.objects.update_or_create(
            variant=variant,
            defaults={
                "product_mapping": product_mapping,
                "basalam_variation_id": int(item["id"]),
                "last_synced_price": calculate_variant_basalam_price(variant),
                "last_synced_stock": calculate_variant_basalam_stock(variant),
                "last_synced_at": timezone.now(),
                "last_error": "",
            },
        )


def publish_product_to_basalam(
    product,
    *,
    published: bool = False,
    client: BasalamClient | None = None,
) -> ProductPublishResult:
    if not settings.BASALAM_SYNC_ENABLED:
        raise ImproperlyConfigured(
            "برای ارسال واقعی، BASALAM_SYNC_ENABLED=True تنظیم شود."
        )

    vendor_id = str(settings.BASALAM_VENDOR_ID).strip()
    if not vendor_id.isdigit():
        raise ImproperlyConfigured(
            "BASALAM_VENDOR_ID باید یک شناسه عددی معتبر باشد."
        )

    variants = validate_product_for_basalam(product)
    uploaded_images = upload_product_images(product)
    payload = build_product_payload(
        product,
        image_ids=[item.basalam_file_id for item in uploaded_images],
        published=published,
    )
    client = client or BasalamClient()
    response_data = _response_data(
        client.create_product(
            vendor_id=int(vendor_id),
            payload=payload,
        )
    )
    basalam_product_id = response_data.get("id")
    if not basalam_product_id:
        raise ValidationError(
            "پاسخ ایجاد محصول باسلام فاقد شناسه محصول است."
        )

    with transaction.atomic():
        product_mapping = BasalamProductMapping.objects.create(
            product=product,
            basalam_product_id=int(basalam_product_id),
            is_active=True,
            last_synced_at=timezone.now(),
            last_error="",
        )
        _save_variation_mappings(
            product_mapping,
            variants,
            response_data,
        )

    return ProductPublishResult(
        product_id=product.pk,
        basalam_product_id=int(basalam_product_id),
        variation_count=len(variants),
        image_count=len(uploaded_images),
        published=published,
    )
