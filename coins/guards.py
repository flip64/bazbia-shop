"""Shared guards used by model saves and QuerySet updates, including F expressions."""

from contextlib import contextmanager
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum


@contextmanager
def inventory_write(variant_ids, using="default", force=False):
    if not apps.is_installed("coins") or not apps.ready:
        yield
        return
    Variant = apps.get_model("products", "ProductVariant")
    Specimen = apps.get_model("coins", "CoinSpecimen")
    Pack = apps.get_model("coins", "CoinPackVariant")
    Offer = apps.get_model("suppliers", "SupplierOffer")
    ids = sorted(set(v for v in variant_ids if v))
    if not force:
        registered = set(
            Specimen.objects.using(using)
            .filter(variant_id__in=ids)
            .values_list("variant_id", flat=True)
        )
        registered.update(
            Pack.objects.using(using)
            .filter(variant_id__in=ids)
            .values_list("variant_id", flat=True)
        )
        ids = sorted(registered)
        if not ids:
            yield
            return
    with transaction.atomic(using=using):
        list(
            Variant.objects.using(using)
            .select_for_update()
            .filter(pk__in=ids)
            .order_by("pk")
        )
        yield
        modes = dict(
            Specimen.objects.using(using)
            .filter(variant_id__in=ids)
            .values_list("variant_id", "sale_mode")
        )
        packs = dict(
            Pack.objects.using(using)
            .filter(variant_id__in=ids)
            .values_list("variant_id", "sale_mode")
        )
        modes.update(packs)
        for pv in (
            Pack.objects.using(using)
            .filter(variant_id__in=ids)
            .select_related("variant", "pack")
        ):
            if pv.variant.product_id != pv.pack.product_id:
                raise ValidationError("محصول واریانت با پک مرتبط تطبیق ندارد.")
        for specimen in (
            Specimen.objects.using(using)
            .filter(variant_id__in=ids)
            .select_related("variant")
        ):
            if (
                apps.get_model("coins", "CoinPack")
                .objects.using(using)
                .filter(product_id=specimen.variant.product_id)
                .exists()
            ):
                raise ValidationError("سکه تکی نباید به محصول پک منتقل شود.")
        for variant in Variant.objects.using(using).filter(pk__in=modes):
            if variant.stock < 0 or (
                modes[variant.pk] == "unique" and variant.stock > 1
            ):
                raise ValidationError("موجودی نمونه اختصاصی باید صفر یا یک باشد.")
            if modes[variant.pk] == "unique":
                reserved = 0
                if apps.is_installed("orders"):
                    reserved = (
                        apps.get_model("orders", "OrderItem")
                        .objects.using(using)
                        .filter(
                            variant_id=variant.pk,
                            order__status__in=[
                                "pending",
                                "paid",
                                "shipped",
                                "completed",
                            ],
                        )
                        .aggregate(total=Sum("quantity"))["total"]
                        or 0
                    )
                packed = 0
                if variant.pk not in packs:
                    packed = (
                        apps.get_model("coins", "PackAssemblyAllocation")
                        .objects.using(using)
                        .filter(source_variant_id=variant.pk)
                        .aggregate(total=Sum("quantity"))["total"]
                        or 0
                    )
                if variant.stock + reserved + packed > 1:
                    raise ValidationError(
                        "این نمونه اختصاصی قبلاً رزرو، فروخته یا داخل پک مصرف شده است."
                    )

            # A prepared pack or a photographed unique object cannot be backed by supplier offers.
            if (
                variant.pk in packs or modes[variant.pk] == "unique"
            ) and Offer.objects.using(using).filter(
                variant_id=variant.pk, is_available=True, supplier_stock__gt=0
            ).exists():
                raise ValidationError(
                    "برای پک آماده یا نمونه اختصاصی، فقط موجودی داخلی مجاز است."
                )


class GuardedStockQuerySetMixin:
    """No bulk bypass for registered coin stock; unrelated products retain behavior."""

    def _variant_ids(self):
        field = (
            "pk"
            if self.model._meta.label_lower == "products.productvariant"
            else "variant_id"
        )
        return list(self.values_list(field, flat=True))

    def update(self, **kwargs):
        relevant = {
            "stock",
            "product",
            "product_id",
            "variant",
            "variant_id",
            "supplier_stock",
            "is_available",
        }
        if not relevant.intersection(kwargs):
            return super().update(**kwargs)
        ids = self._variant_ids()
        target = kwargs.get("variant_id", kwargs.get("variant"))
        if target is not None:
            if hasattr(target, "resolve_expression"):
                # Django bulk_update emits CASE expressions even for ordinary offers.
                # Resolve their destination IDs using SQL rather than banning all bulk updates.
                ids.extend(
                    self.annotate(_coin_target_variant=target).values_list(
                        "_coin_target_variant", flat=True
                    )
                )
            else:
                ids.append(getattr(target, "pk", target))
        with inventory_write(ids, self.db):
            return super().update(**kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        with transaction.atomic(using=self.db):
            return super().bulk_update(objs, fields, batch_size=batch_size)

    def bulk_create(self, objs, *args, **kwargs):
        objs = list(objs)
        ids = [getattr(o, "variant_id", None) or o.pk for o in objs]
        with inventory_write(ids, self.db):
            return super().bulk_create(objs, *args, **kwargs)


def validate_stock_candidate(variant):
    """Friendly ModelForm errors before save; transactional post-write guard remains authoritative."""
    if not apps.is_installed("coins") or not apps.ready or not variant.pk:
        return
    Specimen = apps.get_model("coins", "CoinSpecimen")
    Pack = apps.get_model("coins", "CoinPackVariant")
    listing = (
        Specimen.objects.filter(variant_id=variant.pk).first()
        or Pack.objects.filter(variant_id=variant.pk).first()
    )
    if listing and listing.sale_mode == "unique":
        if variant.stock not in (0, 1):
            raise ValidationError(
                {"stock": "موجودی نمونه اختصاصی باید صفر یا یک باشد."}
            )


def validate_offer_candidate(offer):
    if not apps.is_installed("coins") or not apps.ready or not offer.variant_id:
        return
    if offer.is_available and offer.supplier_stock > 0:
        Pack = apps.get_model("coins", "CoinPackVariant")
        Specimen = apps.get_model("coins", "CoinSpecimen")
        if (
            Pack.objects.filter(variant_id=offer.variant_id).exists()
            or Specimen.objects.filter(
                variant_id=offer.variant_id, sale_mode="unique"
            ).exists()
        ):
            raise ValidationError(
                {
                    "supplier_stock": "پک آماده و نمونه اختصاصی فقط از موجودی داخلی عرضه می‌شوند."
                }
            )
