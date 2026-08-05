# -*- coding: utf-8 -*-

from django.db.models import (
    F,
    IntegerField,
    OuterRef,
    QuerySet,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from products.models import ProductVariant


class VariantStockService:
    """
    سرویس محاسبه موجودی قابل عرضه واریانت‌ها.

    موجودی قابل عرضه:
        موجودی داخلی بازبیا
        +
        موجودی معتبر تأمین‌کنندگان

    این سرویس دو حالت استفاده دارد:

    1. محاسبه موجودی یک واریانت:
        VariantStockService.calculate(variant)

    2. محاسبه موجودی روی QuerySet:
        VariantStockService.annotate(queryset)

    حالت QuerySet برای فیلتر، شمارش، مرتب‌سازی و صفحه‌بندی
    بخش‌هایی مانند اتصال به ترب مناسب است.
    """

    INTERNAL_STOCK_FIELD = "stock"
    SUPPLIER_STOCK_ANNOTATION = "supplier_available_stock"
    AVAILABLE_STOCK_ANNOTATION = "available_stock"

    @classmethod
    def calculate(
        cls,
        variant: ProductVariant,
    ) -> int:
        """
        موجودی قابل عرضه یک واریانت را محاسبه می‌کند.

        اگر واریانت قبلاً با متد annotate این سرویس
        حاشیه‌نویسی شده باشد، همان مقدار آماده استفاده می‌شود
        و Query جدیدی به دیتابیس ارسال نمی‌شود.
        """

        annotated_available_stock = getattr(
            variant,
            cls.AVAILABLE_STOCK_ANNOTATION,
            None,
        )

        if annotated_available_stock is not None:
            return int(
                annotated_available_stock or 0
            )

        internal_stock = int(
            variant.stock or 0
        )

        supplier_stock_result = (
            variant.supplier_offers
            .filter(
                supplier__is_active=True,
                is_available=True,
                supplier_stock__gt=0,
            )
            .aggregate(
                total_stock=Sum(
                    "supplier_stock"
                )
            )
        )

        supplier_stock = int(
            supplier_stock_result[
                "total_stock"
            ]
            or 0
        )

        return (
            internal_stock
            + supplier_stock
        )

    @classmethod
    def annotate(
        cls,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        موجودی تأمین‌کنندگان و موجودی قابل عرضه را
        به QuerySet واریانت‌ها اضافه می‌کند.

        فیلدهای ایجادشده روی هر واریانت:

        supplier_available_stock:
            مجموع موجودی معتبر تأمین‌کنندگان

        available_stock:
            موجودی داخلی + موجودی تأمین‌کنندگان

        این متد چیزی را در دیتابیس ذخیره نمی‌کند.
        """

        # برای جلوگیری از Circular Import، مدل تأمین‌کننده
        # در زمان اجرای متد وارد می‌شود.
        from suppliers.models import SupplierOffer

        supplier_stock_subquery = (
            SupplierOffer.objects
            .filter(
                variant_id=OuterRef("pk"),
                supplier__is_active=True,
                is_available=True,
                supplier_stock__gt=0,
            )
            .values("variant_id")
            .annotate(
                total_stock=Sum(
                    "supplier_stock"
                )
            )
            .values("total_stock")[:1]
        )

        queryset = queryset.annotate(
            supplier_available_stock=Coalesce(
                Subquery(
                    supplier_stock_subquery,
                    output_field=IntegerField(),
                ),
                Value(0),
                output_field=IntegerField(),
            )
        )

        queryset = queryset.annotate(
            available_stock=(
                Coalesce(
                    F("stock"),
                    Value(0),
                    output_field=IntegerField(),
                )
                +
                F(
                    "supplier_available_stock"
                )
            )
        )

        return queryset

    @classmethod
    def filter_available(
        cls,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        فقط واریانت‌هایی را برمی‌گرداند که موجودی
        قابل عرضه آن‌ها بیشتر از صفر باشد.
        """

        queryset = cls.annotate(
            queryset
        )

        return queryset.filter(
            available_stock__gt=0
        )


def calculate_variant_available_stock(
    variant: ProductVariant,
) -> int:
    """
    تابع سازگار با کدهای قبلی پروژه.

    استفاده‌های قبلی همچنان بدون تغییر کار خواهند کرد:

        calculate_variant_available_stock(variant)
    """

    return VariantStockService.calculate(
        variant
    )


def annotate_variant_available_stock(
    queryset: QuerySet,
) -> QuerySet:
    """
    افزودن موجودی ترکیبی به QuerySet واریانت‌ها.
    """

    return VariantStockService.annotate(
        queryset
    )


def filter_available_variants(
    queryset: QuerySet,
) -> QuerySet:
    """
    فیلتر واریانت‌های دارای موجودی قابل عرضه.
    """

    return VariantStockService.filter_available(
        queryset
    )
