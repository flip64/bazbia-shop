# inventory/services.py

from django.db import transaction
from .models import InventoryMovement, ProductVariant


@transaction.atomic
def reserve_stock(variant: ProductVariant, quantity: int, order=None):
    """
    رزرو موجودی: موجودی کافی رو بررسی می‌کنه و موجودی رو کم می‌کنه.
    همچنین یه لاگ InventoryMovement ثبت می‌کنه.
    """
    if variant.stock < quantity:
        raise ValueError(f"موجودی کافی نیست. موجودی فعلی: {variant.stock}")

    variant.stock -= quantity
    variant.save()

    InventoryMovement.objects.create(
        product_variant=variant,
        type='reserve',
        quantity=-quantity,
        related_order=order
    )
    return True


@transaction.atomic
def release_stock(variant: ProductVariant, quantity: int, order=None):
    """
    آزاد کردن موجودی رزرو شده (مثلاً در صورت لغو سفارش)
    موجودی رو برمی‌گردونه و لاگ ثبت می‌کنه.
    """
    variant.stock += quantity
    variant.save()

    InventoryMovement.objects.create(
        product_variant=variant,
        type='release',
        quantity=quantity,
        related_order=order
    )
    return True


@transaction.atomic
def complete_sale(variant: ProductVariant, quantity: int, order=None):
    """
    تایید فروش نهایی: موجودی رزرو شده رو تبدیل به فروش قطعی می‌کنه.
    (در بعضی سیستم‌ها فقط لاگ ثبت می‌کنه چون موجودی قبلاً کم شده.)
    """
    InventoryMovement.objects.create(
        product_variant=variant,
        type='sold',
        quantity=0,
        related_order=order
    )
    return True
