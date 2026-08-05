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
    سرویس موجودی قابل عرضه واریانت‌ها.

    موجودی قابل عرضه:
        موجودی داخلی بازبیا
        +
        موجودی معتبر تأمین‌کنندگان
    """

    @classmethod
    def calculate(
        cls,
        variant: ProductVariant,
    ) -> int:
        """
        محاسبه موجودی قابل عرضه یک واریانت.

        اگر واریانت قبلاً annotate شده باشد،
        از مقدار آماده available_stock استفاده می‌شود.
        """

        annotated_stock = getattr(
            variant,
            "available_stock",
            None,
        )

        if annotated_stock is not None:
            return int(annotated_stock or 0)

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

        return internal_stock + supplier_stock

    @classmethod
    def annotate(
        cls,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        افزودن دو مقدار محاسباتی به QuerySet:

        supplier_available_stock:
            موجودی معتبر تأمین‌کنندگان

        available_stock:
            موجودی داخلی + موجودی تأمین‌کنندگان
        """

        # قرار دادن import درون متد برای کاهش احتمال
        # وابستگی چرخشی بین apps
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

        return queryset.annotate(
            available_stock=(
                Coalesce(
                    F("stock"),
                    Value(0),
                    output_field=IntegerField(),
                )
                + F("supplier_available_stock")
            )
        )

    @classmethod
    def filter_available(
        cls,
        queryset: QuerySet,
    ) -> QuerySet:
        """
        دریافت واریانت‌هایی که موجودی قابل عرضه
        آن‌ها بیشتر از صفر است.
        """

        return (
            cls.annotate(queryset)
            .filter(
                available_stock__gt=0
            )
        )


def calculate_variant_available_stock(
    variant: ProductVariant,
) -> int:
    """
    تابع سازگار با کدهای قبلی پروژه.
    """

    return VariantStockService.calculate(
        variant
    )


def annotate_variant_available_stock(
    queryset: QuerySet,
) -> QuerySet:
    """
    افزودن موجودی ترکیبی به QuerySet.
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
