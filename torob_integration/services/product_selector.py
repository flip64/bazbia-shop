# torob_integration/services/product_selector.py

from urllib.parse import parse_qs, urlparse

from django.db.models import (
    Case,
    IntegerField,
    QuerySet,
    When,
)

from products.models import ProductVariant
from products.services.variant_stock import ( filter_available_variants)

class TorobProductSelector:
    """
    انتخاب واریانت‌های مجاز برای خروجی TorobAPI v3.
    """

    PAGE_SIZE = 100

    
    
    @classmethod
    def base_queryset(cls) -> QuerySet:
        """
        فقط واریانت‌هایی را برمی‌گرداند که:

        - برای ترب فعال شده‌اند
        - محصول اصلی فعال است
        - موجودی قابل عرضه ترکیبی دارند
        - قیمت معتبر دارند
        """

        queryset = ProductVariant.objects.filter(
            torob_config__is_enabled=True,
            product__is_active=True,
            price__gt=0,
        )

        queryset = filter_available_variants(
            queryset
        )

        return (
            queryset
            .select_related(
                "product",
                "product__category",
                "torob_config",
            )
            .prefetch_related(
                # ویژگی‌های اختصاصی واریانت
                "attributes__attribute",

                # تصاویر اختصاصی واریانت
                "images",

                # تصاویر عمومی محصول
                "product__images",

                # مشخصات عمومی محصول
                "product__specifications",
            )
            .distinct()
        )

    
    @classmethod
    def get_paginated(
        cls,
        *,
        page: int,
        sort: str,
    ) -> tuple[QuerySet, int]:
        """
        دریافت یک صفحه از واریانت‌های ترب.

        خروجی:
            - queryset صفحه فعلی
            - تعداد کل واریانت‌های مجاز
        """

        queryset = cls.base_queryset()

        if sort == "date_added_desc":
            queryset = queryset.order_by(
                "-created_at",
                "-id",
            )

        elif sort == "date_updated_desc":
            queryset = queryset.order_by(
                "-torob_config__torob_updated_at",
                "-id",
            )

        else:
            raise ValueError(
                "Invalid sort parameter"
            )

        total = queryset.count()

        start = (page - 1) * cls.PAGE_SIZE
        end = start + cls.PAGE_SIZE

        return queryset[start:end], total

    @classmethod
    def get_by_page_uniques(
        cls,
        page_uniques: list[str],
    ) -> QuerySet:
        """
        دریافت واریانت‌ها بر اساس page_unique.

        در پروژه بازبیا:
            page_unique = ProductVariant.id

        ترتیب خروجی مطابق ترتیب ورودی حفظ می‌شود.
        """

        variant_ids = cls.normalize_variant_ids(
            page_uniques
        )

        if not variant_ids:
            return cls.base_queryset().none()

        preserved_order = cls.build_preserved_order(
            variant_ids
        )

        return (
            cls.base_queryset()
            .filter(id__in=variant_ids)
            .order_by(preserved_order)
        )

    @classmethod
    def get_by_page_urls(
        cls,
        page_urls: list[str],
    ) -> QuerySet:
        """
        دریافت واریانت‌ها از روی URL صفحات محصول.

        ساختار مورد انتظار:

        https://bazbia.ir/product/product-slug?variant=1695

        ترتیب خروجی مطابق ترتیب URLهای ورودی حفظ می‌شود.
        """

        variant_ids = []

        for page_url in page_urls:
            variant_id = cls.extract_variant_id_from_url(
                page_url
            )

            if variant_id is not None:
                variant_ids.append(variant_id)

        variant_ids = cls.remove_duplicates_preserving_order(
            variant_ids
        )

        if not variant_ids:
            return cls.base_queryset().none()

        preserved_order = cls.build_preserved_order(
            variant_ids
        )

        return (
            cls.base_queryset()
            .filter(id__in=variant_ids)
            .order_by(preserved_order)
        )

    @staticmethod
    def extract_variant_id_from_url(
        page_url: str,
    ) -> int | None:
        """
        استخراج شناسه واریانت از query parameter لینک.
        """

        if not isinstance(page_url, str):
            return None

        try:
            parsed_url = urlparse(page_url)
            query_params = parse_qs(
                parsed_url.query
            )

            values = query_params.get("variant")

            if not values:
                return None

            variant_id = int(values[0])

            if variant_id <= 0:
                return None

            return variant_id

        except (
            TypeError,
            ValueError,
            IndexError,
        ):
            return None

    @classmethod
    def normalize_variant_ids(
        cls,
        values: list[str],
    ) -> list[int]:
        """
        تبدیل page_uniqueها به شناسه عددی معتبر
        و حذف مقادیر تکراری با حفظ ترتیب.
        """

        variant_ids = []

        for value in values:
            try:
                variant_id = int(value)
            except (TypeError, ValueError):
                continue

            if variant_id <= 0:
                continue

            variant_ids.append(variant_id)

        return cls.remove_duplicates_preserving_order(
            variant_ids
        )

    @staticmethod
    def remove_duplicates_preserving_order(
        values: list[int],
    ) -> list[int]:
        """
        حذف مقادیر تکراری بدون تغییر ترتیب اولیه.
        """

        seen = set()
        result = []

        for value in values:
            if value in seen:
                continue

            seen.add(value)
            result.append(value)

        return result

    @staticmethod
    def build_preserved_order(
        variant_ids: list[int],
    ) -> Case:
        """
        ساخت ترتیب دیتابیسی مطابق ترتیب ورودی ترب.
        """

        return Case(
            *[
                When(
                    id=variant_id,
                    then=position,
                )
                for position, variant_id
                in enumerate(variant_ids)
            ],
            output_field=IntegerField(),
        )
