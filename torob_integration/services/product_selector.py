# torob_integration/services/product_selector.py

from urllib.parse import parse_qs, urlparse

from django.db.models import QuerySet

from products.models import ProductVariant


class TorobProductSelector:
    """
    انتخاب واریانت‌های مجاز برای خروجی TorobAPI v3.
    """

    PAGE_SIZE = 100

    @classmethod
    def base_queryset(cls) -> QuerySet:
        """
        فقط واریانت‌هایی که:

        - برای ترب فعال شده‌اند
        - محصول اصلی فعال است
        - موجودی بیشتر از صفر دارند
        - قیمت معتبر دارند

        را برمی‌گرداند.
        """

        return (
            ProductVariant.objects
            .filter(
                torob_config__is_enabled=True,
                product__is_active=True,
                stock__gt=0,
                price__gt=0,
            )
            .select_related(
                "product",
                "product__category",
                "torob_config",
            )
            .prefetch_related(
                "attributes",
                "product__images",
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
        دریافت صفحه مشخص از محصولات ترب.

        خروجی:
            queryset صفحه فعلی
            تعداد کل محصولات
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
            raise ValueError("Invalid sort parameter")

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
        دریافت واریانت‌ها با page_unique.

        طبق تصمیم پروژه، page_unique برابر شناسه واریانت است.
        """

        variant_ids = []

        for value in page_uniques:
            try:
                variant_ids.append(int(value))
            except (TypeError, ValueError):
                continue

        return (
            cls.base_queryset()
            .filter(id__in=variant_ids)
            .order_by("id")
        )

    @classmethod
    def get_by_page_urls(
        cls,
        page_urls: list[str],
    ) -> QuerySet:
        """
        دریافت واریانت‌ها از روی لینک صفحه محصول.

        ساختار لینک مورد انتظار:

        https://bazbia.ir/product/product-slug?variant=1695
        """

        variant_ids = []

        for page_url in page_urls:
            variant_id = cls.extract_variant_id_from_url(page_url)

            if variant_id is not None:
                variant_ids.append(variant_id)

        return (
            cls.base_queryset()
            .filter(id__in=variant_ids)
            .order_by("id")
        )

    @staticmethod
    def extract_variant_id_from_url(page_url: str) -> int | None:
        try:
            parsed_url = urlparse(page_url)
            query_params = parse_qs(parsed_url.query)

            values = query_params.get("variant")

            if not values:
                return None

            return int(values[0])

        except (TypeError, ValueError):
            return None
