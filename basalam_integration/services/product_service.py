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


@dataclass(frozen=True)
class ProductSyncPlan:
    product_id: int
    basalam_product_id: int
    new_variant_ids: tuple[int, ...]
    existing_variant_ids: tuple[int, ...]


@dataclass(frozen=True)
class ProductSyncResult:
    product_id: int
    basalam_product_id: int
    added_count: int
    updated_count: int


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


def _get_product_variants(product) -> list:
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


def _variant_payload(variant) -> dict[str, Any]:
    return {
        "primary_price": calculate_variant_basalam_price(variant),
        "stock": calculate_variant_basalam_stock(variant),
        "sku": variant.sku,
        "properties": _variant_properties(variant),
    }


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

    return _get_product_variants(product)


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
            _variant_payload(variant) for variant in variants
        ]

    return {key: value for key, value in payload.items() if value is not None}


def _response_data(response: dict[str, Any]) -> dict[str, Any]:
    for key in ("data", "result"):
        nested = response.get(key)
        if isinstance(nested, dict):
            return nested
    return response


def _save_variation_mappings(product_mapping, variants, response_data):
    response_variants = (
        response_data.get("variants")
        or response_data.get("variant")
        or []
    )
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


def build_product_sync_plan(product) -> ProductSyncPlan:
    if not product.is_active:
        raise ValidationError("محصول بازبیا غیرفعال است.")

    try:
        product_mapping = product.basalam_mapping
    except BasalamProductMapping.DoesNotExist as exc:
        raise ValidationError(
            "این محصول هنوز به محصولی در باسلام متصل نشده است."
        ) from exc

    if not product_mapping.is_active:
        raise ValidationError("اتصال این محصول به باسلام غیرفعال است.")

    variants = _get_product_variants(product)
    mapped_variant_ids = set(
        product_mapping.variation_mappings.values_list(
            "variant_id", flat=True
        )
    )
    new_ids = tuple(
        variant.pk
        for variant in variants
        if variant.pk not in mapped_variant_ids
    )
    existing_ids = tuple(
        variant.pk
        for variant in variants
        if variant.pk in mapped_variant_ids
    )
    return ProductSyncPlan(
        product_id=product.pk,
        basalam_product_id=product_mapping.basalam_product_id,
        new_variant_ids=new_ids,
        existing_variant_ids=existing_ids,
    )


def _response_variants(response_data):
    data = _response_data(response_data)
    return data.get("variants") or data.get("variant") or []


def sync_product_to_basalam(
    product,
    *,
    client: BasalamClient | None = None,
) -> ProductSyncResult:
    if not settings.BASALAM_SYNC_ENABLED:
        raise ImproperlyConfigured(
            "برای ارسال واقعی، BASALAM_SYNC_ENABLED=True تنظیم شود."
        )

    plan = build_product_sync_plan(product)
    product_mapping = product.basalam_mapping
    variants = _get_product_variants(product)
    variants_by_id = {variant.pk: variant for variant in variants}
    client = client or BasalamClient()

    if plan.new_variant_ids:
        response = client.update_product(
            product_id=plan.basalam_product_id,
            payload={
                "variants": [
                    _variant_payload(variant) for variant in variants
                ]
            },
        )
        response_variants = _response_variants(response)
        if not response_variants:
            response_variants = _response_variants(
                client.get_product(
                    product_id=plan.basalam_product_id,
                )
            )

        response_by_sku = {
            str(item.get("sku")): item
            for item in response_variants
            if isinstance(item, dict) and item.get("sku")
        }
        missing_skus = [
            variants_by_id[variant_id].sku
            for variant_id in plan.new_variant_ids
            if not response_by_sku.get(
                str(variants_by_id[variant_id].sku)
            )
            or not response_by_sku[
                str(variants_by_id[variant_id].sku)
            ].get("id")
        ]
        if missing_skus:
            raise ValidationError(
                "باسلام شناسه تنوع‌های جدید را برنگرداند: "
                + "، ".join(missing_skus)
            )

        with transaction.atomic():
            _save_variation_mappings(
                product_mapping,
                variants,
                {"variants": response_variants},
            )
            product_mapping.last_synced_at = timezone.now()
            product_mapping.last_error = ""
            product_mapping.save(
                update_fields=["last_synced_at", "last_error", "updated_at"]
            )
    else:
        now = timezone.now()
        for variant_id in plan.existing_variant_ids:
            variant = variants_by_id[variant_id]
            variation_mapping = variant.basalam_mapping
            payload = _variant_payload(variant)
            payload.pop("properties", None)
            client.update_product_variation(
                product_id=plan.basalam_product_id,
                variation_id=variation_mapping.basalam_variation_id,
                payload=payload,
            )
            variation_mapping.last_synced_price = payload["primary_price"]
            variation_mapping.last_synced_stock = payload["stock"]
            variation_mapping.last_synced_at = now
            variation_mapping.last_error = ""
            variation_mapping.save(
                update_fields=[
                    "last_synced_price",
                    "last_synced_stock",
                    "last_synced_at",
                    "last_error",
                    "updated_at",
                ]
            )
        product_mapping.last_synced_at = now
        product_mapping.last_error = ""
        product_mapping.save(
            update_fields=["last_synced_at", "last_error", "updated_at"]
        )

    return ProductSyncResult(
        product_id=plan.product_id,
        basalam_product_id=plan.basalam_product_id,
        added_count=len(plan.new_variant_ids),
        updated_count=len(plan.existing_variant_ids),
    )
