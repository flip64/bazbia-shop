from django.core.exceptions import ValidationError
from django.db import transaction
from . import models as m


def listing_for(variant_id):
    return (
        m.CoinSpecimen.objects.filter(variant_id=variant_id).first()
        or m.CoinPackVariant.objects.filter(variant_id=variant_id).first()
    )


def readiness_errors(listing):
    errors = []
    variant = listing.variant
    price = (
        variant.discount_price if variant.discount_price is not None else variant.price
    )
    if price <= 0:
        errors.append("قیمت فروش باید مثبت باشد.")
    if getattr(listing, "catalog_link", False):
        # Catalog connections can be published before variant photos are uploaded.
        return errors
    details = m.CoinImageDetail.objects.filter(image__variant_id=variant.pk).exclude(
        image__image="", image__source_url__isnull=True
    )
    # Blank source_url is also not usable.
    details = details.exclude(image__image="", image__source_url="")
    if isinstance(listing, m.CoinPackVariant):
        if not listing.pk:
            return errors + ["ابتدا نسخه پک را ذخیره و اجزا و تصاویر را ثبت کنید."]
        items = list(listing.items.select_related("issue__coin_type"))
        if not items:
            errors.append("پک فاقد اجزا است.")
        for item in items:
            try:
                item.validate_issue(item.issue)
            except ValidationError:
                errors.append("سال یا کشور یکی از اجزای پک ناسازگار است.")
        if not details.filter(view_type="pack").exists():
            errors.append("تصویر نمای کامل پک الزامی است.")
        # A full pack photograph is required; individual coin photos are optional.
    else:
        for side in ("obverse", "reverse"):
            if not details.filter(view_type=side).exists():
                errors.append("عکس رو و پشت نمونه الزامی است.")
    return errors


@transaction.atomic
def set_publication(listing, published):
    from products.models import ProductVariant

    ProductVariant.objects.select_for_update().get(pk=listing.variant_id)
    listing.is_published = published
    listing.save(update_fields=["is_published", "updated_at"])
    return listing


def assert_purchasable(variant, quantity):
    if not variant.is_sellable:
        raise ValidationError("فروش این واریانت متوقف شده است.")
    listing = listing_for(variant.pk)
    if listing is None:
        return
    if not listing.is_published or not variant.product.is_active:
        raise ValidationError("این سکه یا پک هنوز برای فروش منتشر نشده است.")
    if listing.sale_mode == m.SaleMode.UNIQUE and quantity != 1:
        raise ValidationError("تعداد نمونه اختصاصی باید یک باشد.")
    errors = readiness_errors(listing)
    if errors:
        raise ValidationError(errors)
    if getattr(listing, "catalog_link", False):
        return
    from inventory.models import InventoryLot
    from django.db.models import Sum

    lot_stock = (
        InventoryLot.objects.filter(
            product_variant_id=variant.pk, quantity_remaining__gt=0
        ).aggregate(total=Sum("quantity_remaining"))["total"]
        or 0
    )
    if int(variant.stock) != int(lot_stock):
        raise ValidationError("موجودی داخلی این سکه یا پک با لات‌های خرید تطبیق ندارد.")


def order_snapshot(variant):
    """Capture public descriptions only, at order creation, never backfill history."""
    from .api import serializers as s
    from .api.views import stock_sales, image_prefetch

    listing = listing_for(variant.pk)
    if listing is None:
        return {}
    if isinstance(listing, m.CoinSpecimen):
        obj = (
            stock_sales(m.CoinSpecimen.objects.filter(pk=listing.pk))
            .prefetch_related(image_prefetch())
            .get()
        )
        coin_serializer = s.CoinDetailSerializer(obj.issue.coin_type)
        coin_serializer.fields.pop("issues")
        issue_serializer = s.IssueSerializer(obj.issue)
        issue_serializer.fields.pop("specimens")
        return {
            "schema_version": 1,
            "kind": "coin",
            "name": variant.product.name,
            "catalog": coin_serializer.data,
            "issue": issue_serializer.data,
            "specimen": s.SpecimenSerializer(obj).data,
        }
    obj = (
        stock_sales(m.CoinPackVariant.objects.filter(pk=listing.pk))
        .prefetch_related(image_prefetch(), "items__issue__coin_type")
        .get()
    )
    return {
        "schema_version": 1,
        "kind": "pack",
        "name": variant.product.name,
        "year": obj.pack.year,
        "calendar": obj.pack.calendar,
        "is_complete": obj.pack.is_complete,
        "completeness_scope": obj.pack.completeness_scope,
        "variant": s.PackVariantSerializer(obj).data,
    }


def order_has_coins(order):
    from django.db.models import Q

    return order.items.filter(
        Q(variant__coin_specimen__isnull=False)
        | Q(variant__coin_pack_variant__isnull=False)
        | ~Q(catalog_snapshot={})
    ).exists()
