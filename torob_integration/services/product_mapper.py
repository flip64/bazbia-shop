# torob_integration/services/product_mapper.py

from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

from django.conf import settings
from django.utils import timezone
from django.utils.html import strip_tags

from products.models import ProductVariant


class TorobProductMapper:
    """
    تبدیل ProductVariant به ساختار مورد انتظار TorobAPI v3.
    """

    STOREFRONT_BASE_URL = getattr(
        settings,
        "STOREFRONT_BASE_URL",
        "https://bazbia.ir",
    ).rstrip("/")

    MEDIA_BASE_URL = getattr(
        settings,
        "MEDIA_BASE_URL",
        "https://backend.bazbia.ir",
    ).rstrip("/")

    @classmethod
    def map_variant(
        cls,
        variant: ProductVariant,
        *,
        request=None,
    ) -> dict[str, Any]:
        """
        تبدیل یک واریانت مجاز به ساختار محصول ترب.
        """

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

            # واریانت‌های ناموجود در Selector حذف می‌شوند.
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

    # =====================================================
    # Price
    # =====================================================

    @staticmethod
    def get_prices(
        variant: ProductVariant,
    ) -> tuple[int, int | None]:
        """
        قیمت خروجی ترب باید با قیمت همان واریانت در سایت یکسان باشد.
        """

        price = variant.price
        discount_price = variant.discount_price

        if price is None or price <= 0:
            raise ValueError(
                f"Variant {variant.id} has no valid price."
            )

        if (
            discount_price is not None
            and discount_price > 0
            and discount_price < price
        ):
            return int(discount_price), int(price)

        return int(price), None

    # =====================================================
    # URL
    # =====================================================

    @classmethod
    def build_page_url(
        cls,
        variant: ProductVariant,
    ) -> str:
        """
        لینک کامل صفحه محصول که همان واریانت را انتخاب می‌کند.
        """

        product_url = (
            f"{cls.STOREFRONT_BASE_URL}"
            f"/product/{variant.product.slug}/"
        )

        query_string = urlencode(
            {
                "variant": variant.id,
            }
        )

        return f"{product_url}?{query_string}"[:1500]

    # =====================================================
    # Title and textual information
    # =====================================================

    @classmethod
    def build_title(
        cls,
        variant: ProductVariant,
    ) -> str:
        """
        نام محصول به همراه ویژگی‌های همان واریانت.
        """

        product_name = str(
            variant.product.name
        ).strip()

        attribute_parts: list[str] = []

        for attribute_value in variant.attributes.all():
            text = cls.format_attribute_for_title(
                attribute_value
            )

            if text and text not in attribute_parts:
                attribute_parts.append(text)

        if not attribute_parts:
            return product_name[:500]

        suffix = " - ".join(attribute_parts)

        return f"{product_name} - {suffix}"[:500]

    @staticmethod
    def format_attribute_for_title(
        attribute_value,
    ) -> str:
        """
        نمونه خروجی:
            رنگ: طوسی
            سایز: بزرگ
        """

        attribute = getattr(
            attribute_value,
            "attribute",
            None,
        )

        attribute_name = getattr(
            attribute,
            "name",
            None,
        )

        value = getattr(
            attribute_value,
            "value",
            None,
        )

        if value in (None, ""):
            return ""

        value_text = str(value).strip()

        if not attribute_name:
            return value_text

        attribute_name_text = str(
            attribute_name
        ).strip()

        return f"{attribute_name_text}: {value_text}"

    @staticmethod
    def get_subtitle(product) -> str | None:
        """
        نام انگلیسی یا زیرعنوان محصول، در صورت وجود.
        """

        value = (
            getattr(product, "english_name", None)
            or getattr(product, "subtitle", None)
        )

        if not value:
            return None

        value = strip_tags(str(value)).strip()

        return value[:500] or None

    @staticmethod
    def get_category_name(product) -> str | None:
        category = getattr(
            product,
            "category",
            None,
        )

        if category is None:
            return None

        name = getattr(
            category,
            "name",
            None,
        )

        if not name:
            return None

        return str(name).strip()[:200] or None

    @staticmethod
    def get_short_description(product) -> str | None:
        """
        توضیح کوتاه محصول.

        اگر فقط description وجود داشته باشد، HTML آن حذف می‌شود
        و حداکثر ۵۰۰ کاراکتر ارسال خواهد شد.
        """

        value = (
            getattr(product, "short_description", None)
            or getattr(product, "short_desc", None)
            or getattr(product, "description", None)
        )

        if not value:
            return None

        value = strip_tags(str(value))
        value = " ".join(value.split())

        return value[:500] or None

    @staticmethod
    def get_guarantee(product) -> str | None:
        value = (
            getattr(product, "guarantee", None)
            or getattr(product, "warranty", None)
        )

        if not value:
            return None

        value = strip_tags(str(value)).strip()

        return value[:200] or None

    # =====================================================
    # Specifications
    # =====================================================

    @classmethod
    def build_spec(
        cls,
        variant: ProductVariant,
    ) -> dict[str, str | int]:
        """
        ساخت spec از دو منبع:

        1. مشخصات عمومی محصول
        2. ویژگی‌های اختصاصی واریانت

        در صورت تکراری‌بودن نام ویژگی،
        مقدار واریانت بر مقدار عمومی محصول اولویت دارد.
        """

        result: dict[str, str | int] = {}

        product = variant.product

        # مشخصات عمومی محصول
        for specification in product.specifications.all():
            key = getattr(
                specification,
                "name",
                None,
            )

            value = getattr(
                specification,
                "value",
                None,
            )

            if not key or value in (None, ""):
                continue

            normalized_key = str(key).strip()

            if not normalized_key:
                continue

            result[normalized_key] = (
                cls.normalize_spec_value(value)
            )

        # ویژگی‌های اختصاصی واریانت
        for attribute_value in variant.attributes.all():
            key, value = cls.extract_attribute_pair(
                attribute_value
            )

            if not key or value in (None, ""):
                continue

            normalized_key = str(key).strip()

            if not normalized_key:
                continue

            # مقدار واریانت، مقدار عمومی مشابه را جایگزین می‌کند.
            result[normalized_key] = (
                cls.normalize_spec_value(value)
            )

        return result

    @staticmethod
    def extract_attribute_pair(
        attribute_value,
    ) -> tuple[str | None, Any]:
        """
        استخراج نام ویژگی و مقدار آن از AttributeValue.
        """

        attribute = getattr(
            attribute_value,
            "attribute",
            None,
        )

        key = getattr(
            attribute,
            "name",
            None,
        )

        value = getattr(
            attribute_value,
            "value",
            None,
        )

        return key, value

    @staticmethod
    def normalize_spec_value(
        value,
    ) -> str | int:
        """
        ترب برای مقدار spec رشته یا عدد صحیح می‌پذیرد.
        """

        if isinstance(value, bool):
            return "بله" if value else "خیر"

        if isinstance(value, int):
            return value

        if isinstance(value, Decimal):
            if value == value.to_integral_value():
                return int(value)

            return str(value)

        value = strip_tags(str(value))
        value = " ".join(value.split())

        return value

    # =====================================================
    # Images
    # =====================================================

    @classmethod
    def get_image_links(
        cls,
        variant: ProductVariant,
        *,
        request=None,
    ) -> list[str]:
        """
        ترتیب تصاویر:

        1. تصاویر اختصاصی همان واریانت
        2. تصاویر عمومی محصول

        اولین تصویر واریانت باید تصویر اصلی آن باشد.
        تصاویر تکراری حذف می‌شوند.
        """

        links: list[str] = []

        image_objects = [
            *cls.get_variant_images(variant),
            *cls.get_product_images(variant.product),
        ]

        for image_object in image_objects:
            image_url = cls.get_image_url(
                image_object,
                request=request,
            )

            if not image_url:
                continue

            if cls.is_thumbnail_url(image_url):
                continue

            if image_url not in links:
                links.append(image_url)

        return links

    @staticmethod
    def get_variant_images(
        variant,
    ) -> list:
        """
        related_name مدل ProductVariantImage در پروژه: images
        """

        return list(
            variant.images.all().order_by(
                "-is_main",
                "id",
            )
        )

    @staticmethod
    def get_product_images(
        product,
    ) -> list:
        """
        related_name مدل ProductImage در پروژه: images
        """

        return list(
            product.images.all().order_by(
                "-is_main",
                "id",
            )
        )

    @classmethod
    def get_image_url(
        cls,
        image_object,
        *,
        request=None,
    ) -> str | None:
        """
        اولویت:

        1. فایل ذخیره‌شده در image
        2. لینک خارجی source_url
        """

        image_field = getattr(
            image_object,
            "image",
            None,
        )

        if image_field:
            try:
                url = str(image_field.url)

                if url.startswith(
                    ("http://", "https://")
                ):
                    return url[:1000]

                if request is not None:
                    return request.build_absolute_uri(
                        url
                    )[:1000]

                return (
                    f"{cls.MEDIA_BASE_URL}{url}"
                )[:1000]

            except (AttributeError, ValueError):
                pass

        source_url = getattr(
            image_object,
            "source_url",
            None,
        )

        if source_url:
            source_url = str(
                source_url
            ).strip()

            if source_url.startswith(
                ("http://", "https://")
            ):
                return source_url[:1000]

        return None

    @staticmethod
    def is_thumbnail_url(
        image_url: str,
    ) -> bool:
        """
        جلوگیری از ارسال thumbnailهای مشخص.

        این بررسی فقط بر اساس نام URL است و فایل اصلی را حذف نمی‌کند.
        """

        lowered_url = image_url.lower()

        thumbnail_markers = (
            "/thumb/",
            "/thumbnail/",
            "_thumb.",
            "-thumb.",
        )

        return any(
            marker in lowered_url
            for marker in thumbnail_markers
        )

    # =====================================================
    # Dates
    # =====================================================

    @staticmethod
    def get_date_updated(variant):
        """
        زمان تغییر اختصاصی ترب.

        اگر زمان ترب نامعتبر یا قدیمی‌تر از زمان ساخت واریانت باشد،
        created_at استفاده می‌شود.
        """

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
        خروجی ISO 8601 و timezone-aware.
        """

        if value is None:
            raise ValueError(
                "Datetime value cannot be None."
            )

        if timezone.is_naive(value):
            value = timezone.make_aware(
                value,
                timezone.get_current_timezone(),
            )

        return value.isoformat()
