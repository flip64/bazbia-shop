# torob_integration/services/product_mapper.py

from decimal import Decimal
from typing import Any

from django.conf import settings
from django.utils import timezone

from products.models import ProductVariant


class TorobProductMapper:
    """
    تبدیل ProductVariant به فرمت محصول TorobAPI v3.
    """

    STOREFRONT_BASE_URL = getattr(
        settings,
        "STOREFRONT_BASE_URL",
        "https://bazbia.ir",
    )

    @classmethod
    def map_variant(
        cls,
        variant: ProductVariant,
        *,
        request=None,
    ) -> dict[str, Any]:
        product = variant.product

        current_price, old_price = cls.get_prices(variant)

        return {
            "page_unique": str(variant.id),

            "page_url": cls.build_page_url(variant),

            "product_group_id": str(product.id),

            "title": cls.build_title(variant),

            "subtitle": cls.get_subtitle(product),

            "current_price": current_price,

            "old_price": old_price,

            # واریانت ناموجود اصلاً وارد queryset نمی‌شود.
            "availability": True,

            "category_name": cls.get_category_name(product),

            "image_links": cls.get_image_links(
                variant,
                request=request,
            ),

            "short_desc": cls.get_short_description(product),

            "spec": cls.build_spec(variant),

            "guarantee": cls.get_guarantee(product),

            "date_added": cls.format_datetime(
                variant.created_at
            ),

            "date_updated": cls.format_datetime(
                cls.get_date_updated(variant)
            ),
        }

    @staticmethod
    def get_prices(
        variant: ProductVariant,
    ) -> tuple[int, int | None]:
        """
        منطق قیمت باید با API اصلی سایت یکسان باشد.
        """

        price = variant.price
        discount_price = variant.discount_price

        if (
            discount_price is not None
            and discount_price > 0
            and discount_price < price
        ):
            return (
                int(discount_price),
                int(price),
            )

        return (
            int(price),
            None,
        )

    @classmethod
    def build_page_url(
        cls,
        variant: ProductVariant,
    ) -> str:
        product = variant.product

        base_url = cls.STOREFRONT_BASE_URL.rstrip("/")

        return (
            f"{base_url}/product/{product.slug}"
            f"?variant={variant.id}"
        )

    @staticmethod
    def build_title(
        variant: ProductVariant,
    ) -> str:
        """
        نام محصول به همراه ویژگی‌های مهم همان واریانت.
        """

        product_name = str(variant.product.name).strip()

        attribute_parts = []

        for item in variant.attributes.all():
            text = TorobProductMapper.format_attribute_for_title(
                item
            )

            if text:
                attribute_parts.append(text)

        if not attribute_parts:
            return product_name[:500]

        suffix = " - ".join(attribute_parts)

        return f"{product_name} - {suffix}"[:500]

    @staticmethod
    def format_attribute_for_title(attribute_value) -> str:
        """
        این متد باید در صورت تفاوت نام فیلدهای مدل ویژگی،
        با مدل واقعی پروژه هماهنگ شود.
        """

        attribute_name = None
        value = None

        if hasattr(attribute_value, "attribute"):
            attribute = attribute_value.attribute

            attribute_name = getattr(
                attribute,
                "name",
                None,
            )

        attribute_name = (
            attribute_name
            or getattr(attribute_value, "name", None)
        )

        value = (
            getattr(attribute_value, "value", None)
            or getattr(attribute_value, "name", None)
        )

        if not value:
            return ""

        if attribute_name and str(attribute_name) != str(value):
            return f"{attribute_name}: {value}"

        return str(value)

    @staticmethod
    def get_subtitle(product) -> str | None:
        """
        نام انگلیسی محصول، اگر مدل چنین فیلدی داشته باشد.
        """

        value = (
            getattr(product, "english_name", None)
            or getattr(product, "subtitle", None)
        )

        if not value:
            return None

        return str(value)[:500]

    @staticmethod
    def get_category_name(product) -> str | None:
        category = getattr(product, "category", None)

        if category is None:
            return None

        name = getattr(category, "name", None)

        if not name:
            return None

        return str(name)[:200]

    @staticmethod
    def get_short_description(product) -> str | None:
        value = (
            getattr(product, "short_description", None)
            or getattr(product, "short_desc", None)
            or getattr(product, "description", None)
        )

        if not value:
            return None

        return str(value).strip()[:500]

    @staticmethod
    def get_guarantee(product) -> str | None:
        value = (
            getattr(product, "guarantee", None)
            or getattr(product, "warranty", None)
        )

        if not value:
            return None

        return str(value).strip()[:200]

    @classmethod
    def build_spec(
        cls,
        variant: ProductVariant,
    ) -> dict[str, str | int]:
        """
        ویژگی‌های واریانت در spec قرار می‌گیرند.
        """

        result: dict[str, str | int] = {}

        for item in variant.attributes.all():
            key, value = cls.extract_attribute_pair(item)

            if not key or value in (None, ""):
                continue

            result[str(key)] = cls.normalize_spec_value(value)

        return result

    @staticmethod
    def extract_attribute_pair(attribute_value):
        """
        با چند ساختار رایج مدل Attribute سازگار است.
        """

        attribute = getattr(
            attribute_value,
            "attribute",
            None,
        )

        key = None

        if attribute is not None:
            key = getattr(attribute, "name", None)

        key = (
            key
            or getattr(attribute_value, "attribute_name", None)
            or getattr(attribute_value, "name", None)
        )

        value = (
            getattr(attribute_value, "value", None)
            or getattr(attribute_value, "display_value", None)
            or getattr(attribute_value, "name", None)
        )

        return key, value

    @staticmethod
    def normalize_spec_value(value) -> str | int:
        if isinstance(value, bool):
            return str(value)

        if isinstance(value, int):
            return value

        if isinstance(value, Decimal):
            if value == value.to_integral_value():
                return int(value)

            return str(value)

        return str(value)

    @classmethod
    def get_image_links(
        cls,
        variant: ProductVariant,
        *,
        request=None,
    ) -> list[str]:
        """
        ترتیب تصاویر:

        1. تصاویر اختصاصی واریانت انتخاب‌شده
        2. تصاویر عمومی محصول

        تصاویر اختصاصی سایر واریانت‌ها فعلاً ارسال نمی‌شوند
        تا با الزام مستندات ترب مغایرت نداشته باشد.
        """

        links: list[str] = []

        variant_images = cls.get_variant_images(variant)
        product_images = cls.get_product_images(
            variant.product
        )

        for image_object in [
            *variant_images,
            *product_images,
        ]:
            image_url = cls.get_image_url(
                image_object,
                request=request,
            )

            if not image_url:
                continue

            if image_url not in links:
                links.append(image_url)

        return links

    @staticmethod
    def get_variant_images(variant) -> list:
        """
        چند related_name رایج را بررسی می‌کند.
        بعداً نام دقیق را با مدل پروژه ثابت می‌کنیم.
        """

        for related_name in (
            "images",
            "variant_images",
            "productvariantimage_set",
        ):
            manager = getattr(
                variant,
                related_name,
                None,
            )

            if manager is None:
                continue

            queryset = manager.all()

            try:
                return list(
                    queryset.order_by(
                        "-is_main",
                        "id",
                    )
                )
            except Exception:
                return list(
                    queryset.order_by("id")
                )

        return []

    @staticmethod
    def get_product_images(product) -> list:
        manager = getattr(product, "images", None)

        if manager is None:
            return []

        queryset = manager.all()

        try:
            return list(
                queryset.order_by(
                    "-is_main",
                    "id",
                )
            )
        except Exception:
            return list(
                queryset.order_by("id")
            )

    @staticmethod
    def get_image_url(
        image_object,
        *,
        request=None,
    ) -> str | None:
        image_field = getattr(
            image_object,
            "image",
            None,
        )

        if not image_field:
            return None

        try:
            url = image_field.url
        except (AttributeError, ValueError):
            return None

        if request is not None:
            return request.build_absolute_uri(url)[:1000]

        media_base_url = getattr(
            settings,
            "MEDIA_BASE_URL",
            "https://backend.bazbia.ir",
        ).rstrip("/")

        if str(url).startswith(("http://", "https://")):
            return str(url)[:1000]

        return f"{media_base_url}{url}"[:1000]

    @staticmethod
    def get_date_updated(variant):
        config = variant.torob_config

        date_added = variant.created_at
        date_updated = config.torob_updated_at

        if date_updated is None:
            return date_added

        if date_updated < date_added:
            return date_added

        return date_updated

    @staticmethod
    def format_datetime(value) -> str:
        """
        خروجی ISO 8601 دارای timezone.
        """

        if timezone.is_naive(value):
            value = timezone.make_aware(
                value,
                timezone.get_current_timezone(),
            )

        return value.isoformat()
