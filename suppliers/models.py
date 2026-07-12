from django.db import models


# ==================================
# مدل تأمین‌کننده (Supplier)
# ==================================
class Supplier(models.Model):
    """
    این مدل اطلاعات عمومی هر تأمین‌کننده را نگهداری می‌کند.

    این اطلاعات مستقل از محصولات هستند و شامل
    نام، اطلاعات تماس و وضعیت همکاری با تأمین‌کننده می‌شوند.

    هر تأمین‌کننده می‌تواند تعداد نامحدودی پیشنهاد فروش
    (SupplierOffer) برای محصولات مختلف داشته باشد.
    """

    # نام تأمین‌کننده
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="نام شرکت یا فروشنده عمده"
    )


    # نام slug
    slug = models.CharField(
        max_length=255,
        unique=False,
        help_text =" نامک یکتا برای لینک  ",
        unique=True,
    )



    
    # وب‌سایت رسمی
    website = models.URLField(
        blank=True,
        null=True,
        help_text="آدرس وب‌سایت تأمین‌کننده"
    )

    # شماره تماس
    phone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="شماره تماس"
    )

    # ایمیل
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="ایمیل"
    )

    # آدرس
    address = models.TextField(
        blank=True,
        null=True,
        help_text="آدرس دفتر یا انبار"
    )

    # فعال بودن همکاری
    is_active = models.BooleanField(
        default=True,
        help_text="آیا همکاری با این تأمین‌کننده فعال است؟"
    )

    # یادداشت داخلی
    note = models.TextField(
        blank=True,
        help_text="یادداشت‌های داخلی مدیر فروشگاه"
    )

    # تاریخ ایجاد
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="تاریخ ثبت تأمین‌کننده"
    )

    # آخرین ویرایش
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="آخرین زمان ویرایش اطلاعات"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "تأمین‌کننده"
        verbose_name_plural = "تأمین‌کنندگان"

    def __str__(self):
        return self.name





class SupplierOffer(models.Model):
    """
    ==========================================================
    پیشنهاد تأمین‌کننده (Supplier Offer)
    ==========================================================

    این مدل ارتباط بین یک واریانت محصول و یک تأمین‌کننده را
    نگهداری می‌کند.

    هر رکورد نشان می‌دهد که یک تأمین‌کننده، یک واریانت را
    با چه قیمت، موجودی و لینکی عرضه می‌کند.

    هر واریانت می‌تواند توسط چندین تأمین‌کننده عرضه شود.
    هر تأمین‌کننده نیز می‌تواند هزاران محصول عرضه کند.

    این مدل هسته سیستم تأمین‌کنندگان بازبیا است.

    ارتباط‌ها
    ----------
    Supplier (1) -------- (∞) SupplierOffer (∞) -------- (1) ProductVariant

    مثال
    -----
    محصول:
        تخته نرد کد 100

    تأمین‌کننده اول:
        عبدی
        قیمت خرید: 1,200,000
        موجودی: 15

    تأمین‌کننده دوم:
        شرکت X
        قیمت خرید: 1,150,000
        موجودی: 8

    هر دو به یک ProductVariant متصل هستند.
    ==========================================================
    """

    supplier = models.ForeignKey(
        "Supplier",
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name="تأمین‌کننده",
        help_text="تأمین‌کننده عرضه‌کننده این محصول"
    )

    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.CASCADE,
        related_name="supplier_offers",
        verbose_name="واریانت محصول",
        help_text="واریانتی که این تأمین‌کننده عرضه می‌کند"
    )

    supplier_product_name = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="نام محصول نزد تأمین‌کننده",
        help_text="نامی که تأمین‌کننده برای این محصول استفاده می‌کند."
    )

    supplier_product_code = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="کد محصول تأمین‌کننده",
        help_text="کد داخلی محصول نزد تأمین‌کننده (در صورت وجود)"
    )

    supplier_url = models.URLField(
        max_length=1000,
        verbose_name="لینک محصول",
        help_text="آدرس صفحه محصول در سایت تأمین‌کننده"
    )

    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name="قیمت خرید"
    )

    supplier_stock = models.PositiveIntegerField(
        default=0,
        verbose_name="موجودی تأمین‌کننده"
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name="موجود"
    )

    is_primary = models.BooleanField(
        default=False,
        verbose_name="تأمین‌کننده اصلی",
        help_text="اگر فعال باشد این تأمین‌کننده به عنوان تأمین‌کننده اصلی محصول استفاده می‌شود."
    )

    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="آخرین مشاهده در لیست محصولات"
    )

    last_checked = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بررسی"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )

    class Meta:
        verbose_name = "پیشنهاد تأمین‌کننده"
        verbose_name_plural = "پیشنهادهای تأمین‌کنندگان"

        ordering = ["supplier", "variant"]

        constraints = [
            models.UniqueConstraint(
                fields=["supplier", "variant"],
                name="unique_supplier_variant"
            )
        ]

    def __str__(self):
        return f"{self.supplier.name} → {self.variant.sku}"





class SupplierPriceHistory(models.Model):
    """
    ==========================================================
    تاریخچه قیمت تأمین‌کننده (SupplierPriceHistory)
    ==========================================================

    این مدل تمامی تغییرات قیمت خرید محصولات از تأمین‌کنندگان
    را ثبت می‌کند.

    هر بار که قیمت خرید یک SupplierOffer تغییر کند، یک رکورد
    جدید در این جدول ایجاد می‌شود.

    این جدول فقط برای نگهداری تاریخچه است و هیچ تغییری در
    قیمت فعلی ایجاد نمی‌کند.

    ارتباط‌ها
    ----------
    SupplierOffer (1) -------- (∞) SupplierPriceHistory

    مثال
    -----
    1405/04/01    1,200,000
    1405/04/03    1,150,000
    1405/04/08    1,180,000

    کاربردها
    --------
    - مشاهده تاریخچه قیمت خرید
    - رسم نمودار تغییر قیمت
    - محاسبه کمترین و بیشترین قیمت
    - تحلیل نوسانات قیمت
    ==========================================================
    """

    supplier_offer = models.ForeignKey(
        "SupplierOffer",
        on_delete=models.CASCADE,
        related_name="price_history",
        verbose_name="پیشنهاد تأمین‌کننده",
        help_text="پیشنهاد تأمین‌کننده‌ای که قیمت آن تغییر کرده است."
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name="قیمت خرید",
        help_text="قیمت خرید ثبت‌شده در این تاریخ."
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ثبت",
        help_text="زمان ثبت این تغییر قیمت."
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "تاریخچه قیمت تأمین‌کننده"
        verbose_name_plural = "تاریخچه قیمت تأمین‌کنندگان"

    def __str__(self):
        return (
            f"{self.supplier_offer.variant.sku} | "
            f"{self.price} | "
            f"{self.created_at:%Y-%m-%d %H:%M}"
        )
