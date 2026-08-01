# torob_integration/signals.py

from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_save,
    pre_delete,
)
from django.dispatch import receiver
from django.utils import timezone

from products.models import (
    Attribute,
    AttributeValue,
    Category,
    Product,
    ProductImage,
    ProductSpecification,
    ProductVariant,
    ProductVariantImage,
)

from .models import TorobVariantConfig


# =========================================================
# Helper functions
# =========================================================

def touch_variant(variant_id: int | None) -> int:
    """
    زمان آخرین تغییر ترب را برای یک واریانت به‌روزرسانی می‌کند.

    خروجی:
        تعداد رکوردهای به‌روزشده
    """
    if not variant_id:
        return 0

    return TorobVariantConfig.objects.filter(
        variant_id=variant_id,
    ).update(
        torob_updated_at=timezone.now(),
    )


def touch_variants(variant_ids) -> int:
    """
    زمان تغییر ترب را برای چند واریانت به‌روزرسانی می‌کند.
    """
    variant_ids = {
        variant_id
        for variant_id in variant_ids
        if variant_id
    }

    if not variant_ids:
        return 0

    return TorobVariantConfig.objects.filter(
        variant_id__in=variant_ids,
    ).update(
        torob_updated_at=timezone.now(),
    )


def touch_product_variants(product_id: int | None) -> int:
    """
    زمان تغییر ترب تمام واریانت‌های یک محصول را به‌روزرسانی می‌کند.
    """
    if not product_id:
        return 0

    return TorobVariantConfig.objects.filter(
        variant__product_id=product_id,
    ).update(
        torob_updated_at=timezone.now(),
    )


def touch_category_variants(category_id: int | None) -> int:
    """
    زمان تغییر ترب واریانت‌های محصولات یک دسته‌بندی را به‌روزرسانی می‌کند.
    """
    if not category_id:
        return 0

    return TorobVariantConfig.objects.filter(
        variant__product__category_id=category_id,
    ).update(
        torob_updated_at=timezone.now(),
    )


def touch_attribute_value_variants(
    attribute_value_id: int | None,
) -> int:
    """
    تمام واریانت‌هایی را لمس می‌کند که از یک AttributeValue استفاده می‌کنند.
    """
    if not attribute_value_id:
        return 0

    return TorobVariantConfig.objects.filter(
        variant__attributes__id=attribute_value_id,
    ).update(
        torob_updated_at=timezone.now(),
    )


def touch_attribute_variants(attribute_id: int | None) -> int:
    """
    تمام واریانت‌هایی را لمس می‌کند که مقداری از یک Attribute دارند.
    """
    if not attribute_id:
        return 0

    return TorobVariantConfig.objects.filter(
        variant__attributes__attribute_id=attribute_id,
    ).update(
        torob_updated_at=timezone.now(),
    )


# =========================================================
# ProductVariant
# قیمت، تخفیف، موجودی، SKU و سایر فیلدهای مستقیم
# =========================================================

@receiver(
    post_save,
    sender=ProductVariant,
    dispatch_uid="torob_product_variant_saved",
)
def handle_product_variant_saved(
    sender,
    instance,
    created,
    raw=False,
    **kwargs,
):
    """
    برای واریانت جدید، تنظیمات ترب را با حالت غیرفعال ایجاد می‌کند.

    برای واریانت ویرایش‌شده، torob_updated_at را تغییر می‌دهد.
    """
    if raw:
        return

    config, config_created = TorobVariantConfig.objects.get_or_create(
        variant=instance,
        defaults={
            "is_enabled": False,
            "page_unique": str(instance.pk),
        },
    )

    # زمان اولیه رکورد جدید از default مدل تأمین می‌شود.
    if not created and not config_created:
        TorobVariantConfig.objects.filter(
            pk=config.pk,
        ).update(
            torob_updated_at=timezone.now(),
        )


# =========================================================
# Product
# نام، slug، توضیحات، دسته‌بندی و وضعیت فعال
# =========================================================

@receiver(
    post_save,
    sender=Product,
    dispatch_uid="torob_product_saved",
)
def handle_product_saved(
    sender,
    instance,
    raw=False,
    **kwargs,
):
    if raw:
        return

    touch_product_variants(instance.pk)


# =========================================================
# Category
# category_name خروجی ترب
# =========================================================

@receiver(
    post_save,
    sender=Category,
    dispatch_uid="torob_category_saved",
)
def handle_category_saved(
    sender,
    instance,
    raw=False,
    **kwargs,
):
    if raw:
        return

    touch_category_variants(instance.pk)


@receiver(
    pre_delete,
    sender=Category,
    dispatch_uid="torob_category_deleting",
)
def handle_category_deleting(
    sender,
    instance,
    **kwargs,
):
    """
    قبل از حذف دسته‌بندی اجرا می‌شود؛ چون پس از حذف، category محصولات
    به null تبدیل می‌شود و دیگر نمی‌توان محصولات قبلی آن دسته را پیدا کرد.
    """
    touch_category_variants(instance.pk)


# =========================================================
# ProductImage
# تصاویر عمومی محصول
# =========================================================

@receiver(
    post_save,
    sender=ProductImage,
    dispatch_uid="torob_product_image_saved",
)
def handle_product_image_saved(
    sender,
    instance,
    raw=False,
    **kwargs,
):
    if raw:
        return

    touch_product_variants(instance.product_id)


@receiver(
    post_delete,
    sender=ProductImage,
    dispatch_uid="torob_product_image_deleted",
)
def handle_product_image_deleted(
    sender,
    instance,
    **kwargs,
):
    touch_product_variants(instance.product_id)


# =========================================================
# ProductVariantImage
# تصاویر اختصاصی همان واریانت
# =========================================================

@receiver(
    post_save,
    sender=ProductVariantImage,
    dispatch_uid="torob_variant_image_saved",
)
def handle_variant_image_saved(
    sender,
    instance,
    raw=False,
    **kwargs,
):
    if raw:
        return

    touch_variant(instance.variant_id)


@receiver(
    post_delete,
    sender=ProductVariantImage,
    dispatch_uid="torob_variant_image_deleted",
)
def handle_variant_image_deleted(
    sender,
    instance,
    **kwargs,
):
    touch_variant(instance.variant_id)


# =========================================================
# ProductSpecification
# مشخصات عمومی محصول
# =========================================================

@receiver(
    post_save,
    sender=ProductSpecification,
    dispatch_uid="torob_product_specification_saved",
)
def handle_product_specification_saved(
    sender,
    instance,
    raw=False,
    **kwargs,
):
    if raw:
        return

    touch_product_variants(instance.product_id)


@receiver(
    post_delete,
    sender=ProductSpecification,
    dispatch_uid="torob_product_specification_deleted",
)
def handle_product_specification_deleted(
    sender,
    instance,
    **kwargs,
):
    touch_product_variants(instance.product_id)


# =========================================================
# ProductVariant.attributes
# اتصال یا حذف ویژگی از واریانت
# =========================================================

@receiver(
    m2m_changed,
    sender=ProductVariant.attributes.through,
    dispatch_uid="torob_variant_attributes_changed",
)
def handle_variant_attributes_changed(
    sender,
    instance,
    action,
    reverse,
    pk_set,
    **kwargs,
):
    """
    حالت عادی:
        instance یک ProductVariant است.

    حالت reverse:
        instance یک AttributeValue است و چند واریانت تغییر کرده‌اند.
    """
    if action not in {
        "post_add",
        "post_remove",
        "post_clear",
    }:
        return

    if reverse:
        # در حالت reverse، pk_set شناسه واریانت‌ها را دارد.
        # در post_clear ممکن است pk_set برابر None باشد.
        if pk_set:
            touch_variants(pk_set)
        else:
            touch_attribute_value_variants(instance.pk)

        return

    touch_variant(instance.pk)


# =========================================================
# AttributeValue
# تغییر مقدار، مثل «قرمز» به «زرشکی»
# =========================================================

@receiver(
    post_save,
    sender=AttributeValue,
    dispatch_uid="torob_attribute_value_saved",
)
def handle_attribute_value_saved(
    sender,
    instance,
    raw=False,
    **kwargs,
):
    if raw:
        return

    touch_attribute_value_variants(instance.pk)


@receiver(
    pre_delete,
    sender=AttributeValue,
    dispatch_uid="torob_attribute_value_deleting",
)
def handle_attribute_value_deleting(
    sender,
    instance,
    **kwargs,
):
    """
    باید قبل از حذف اجرا شود؛ زیرا بعد از حذف، روابط ManyToMany
    از بین رفته‌اند.
    """
    touch_attribute_value_variants(instance.pk)


# =========================================================
# Attribute
# تغییر نام ویژگی، مثل «رنگ» به «رنگ محصول»
# =========================================================

@receiver(
    post_save,
    sender=Attribute,
    dispatch_uid="torob_attribute_saved",
)
def handle_attribute_saved(
    sender,
    instance,
    raw=False,
    **kwargs,
):
    if raw:
        return

    touch_attribute_variants(instance.pk)


@receiver(
    pre_delete,
    sender=Attribute,
    dispatch_uid="torob_attribute_deleting",
)
def handle_attribute_deleting(
    sender,
    instance,
    **kwargs,
):
    touch_attribute_variants(instance.pk)
