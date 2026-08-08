
# analytics/models.py

import hashlib

from django.conf import settings
from django.db import models


class SiteEvent(models.Model):
    """
    رویدادهای مهم کاربران داخل سایت.

    نمونه:
    - بازدید صفحه
    - مشاهده محصول
    - افزودن به سبد
    - شروع پرداخت
    - ثبت سفارش
    - پرداخت موفق
    """

    class EventType(models.TextChoices):
        PAGE_VIEW = "page_view", "بازدید صفحه"
        PRODUCT_VIEW = "product_view", "مشاهده محصول"
        ADD_TO_CART = "add_to_cart", "افزودن به سبد"
        CHECKOUT_STARTED = "checkout_started", "شروع تسویه حساب"
        ORDER_CREATED = "order_created", "ثبت سفارش"
        ORDER_PAID = "order_paid", "پرداخت موفق"

    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
        db_index=True,
        verbose_name="نوع رویداد",
    )

    # -------------------------
    # User / Session
    # -------------------------

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="analytics_events",
        verbose_name="کاربر",
    )

    session_key = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="کلید نشست",
    )

    visitor_id = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        verbose_name="شناسه بازدیدکننده",
    )

    # -------------------------
    # Page
    # -------------------------

    path = models.CharField(
        max_length=500,
        blank=True,
        db_index=True,
        verbose_name="مسیر صفحه",
    )

    page_url = models.TextField(
        blank=True,
        verbose_name="آدرس کامل صفحه",
    )

    referrer = models.TextField(
        blank=True,
        verbose_name="صفحه ارجاع‌دهنده",
    )

    # -------------------------
    # Traffic Source
    # -------------------------

    source = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="منبع ورودی",
    )

    utm_source = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="UTM Source",
    )

    utm_medium = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name="UTM Medium",
    )

    utm_campaign = models.CharField(
        max_length=150,
        blank=True,
        db_index=True,
        verbose_name="UTM Campaign",
    )

    utm_content = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="UTM Content",
    )

    utm_term = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="UTM Term",
    )

    # -------------------------
    # Product
    # -------------------------

    product = models.ForeignKey(
        "products.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="analytics_events",
        verbose_name="محصول",
    )

    variant = models.ForeignKey(
        "products.ProductVariant",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="analytics_events",
        verbose_name="تنوع محصول",
    )

    # -------------------------
    # Request information
    # -------------------------

    ip_hash = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        verbose_name="هش IP",
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
    )

    # -------------------------
    # Extra information
    # -------------------------

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="اطلاعات اضافی",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="زمان ثبت",
    )

    class Meta:
        ordering = ("-created_at",)

        indexes = [
            models.Index(
                fields=["event_type", "created_at"],
                name="analytics_event_time_idx",
            ),
            models.Index(
                fields=["source", "created_at"],
                name="analytics_source_time_idx",
            ),
            models.Index(
                fields=["product", "created_at"],
                name="analytics_product_time_idx",
            ),
            models.Index(
                fields=["visitor_id", "created_at"],
                name="analytics_visitor_time_idx",
            ),
        ]

        verbose_name = "رویداد سایت"
        verbose_name_plural = "رویدادهای سایت"

    def __str__(self):
        return (
            f"{self.get_event_type_display()} "
            f"- {self.created_at:%Y-%m-%d %H:%M}"
        )

    @staticmethod
    def hash_ip(ip_address: str) -> str:
        """
        IP خام را ذخیره نمی‌کنیم.
        فقط هش آن برای تشخیص تقریبی بازدیدکننده‌ها نگهداری می‌شود.
        """

        if not ip_address:
            return ""

        value = (
            f"{settings.SECRET_KEY}:{ip_address}"
        ).encode("utf-8")

        return hashlib.sha256(value).hexdigest()
