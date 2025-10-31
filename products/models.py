from django.db import models
from decimal import Decimal, ROUND_HALF_UP

# ==============================
# مدل دسته‌بندی محصولات (Category)
# ==============================
class Category(models.Model):
    name = models.CharField(max_length=100, help_text="نام دسته‌بندی")
    slug = models.SlugField(unique=True, help_text="نامک یکتا برای URL")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, help_text="تصویر دسته‌بندی")

    # دسته‌بندی والد برای پشتیبانی از ساختار درختی
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='subcategories',
        help_text="دسته‌بندی والد (اختیاری)"
    )

    def __str__(self):
        return f"{self.parent.name} -> {self.name}" if self.parent else self.name


# ==============================
# مدل تگ محصولات (Tag)
# ==============================
class Tag(models.Model):
    name = models.CharField(max_length=50, help_text="نام تگ")
    slug = models.SlugField(unique=True, help_text="نامک یکتا برای URL")

    def __str__(self):
        return self.name


# ==============================
# مدل محصول (Product)
# ==============================
class Product(models.Model):
    name = models.CharField(max_length=200, help_text="نام محصول")
    slug = models.SlugField(unique=True, help_text="نامک یکتا برای URL")
    description = models.TextField(blank=True, null=True, help_text="توضیحات محصول")
    base_price = models.DecimalField(max_digits=12, decimal_places=0, help_text="قیمت پایه محصول")

    # دسته‌بندی اصلی محصول
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='products',
        help_text="دسته‌بندی اصلی محصول"
    )

    # تگ‌های محصول
    tags = models.ManyToManyField(Tag, blank=True, related_name='products', help_text="تگ‌های مرتبط با محصول")

    is_active = models.BooleanField(default=True, help_text="آیا محصول فعال و قابل فروش است")
    quantity = models.IntegerField(default=0, help_text="موجودی کلی محصول")

    created_at = models.DateTimeField(auto_now_add=True, help_text="تاریخ ایجاد محصول")
    updated_at = models.DateTimeField(auto_now=True, help_text="تاریخ آخرین بروزرسانی محصول")

    def __str__(self):
        return self.name


# ===========================
# مشخصات محصول (ProductSpecification)
# ===========================
class ProductSpecification(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='specifications',
        help_text="محصول مرتبط"
    )
    name = models.CharField(max_length=100, help_text="نام مشخصه (مثلا وزن، جنس)")
    value = models.TextField(help_text="مقدار مشخصه (مثلا 1 کیلوگرم، فلز)")

    def __str__(self):
        return f"{self.name}: {self.value} ({self.product.name})"


# ===========================
# ویژگی ها و مقادیر آنها (Attribute & AttributeValue)
# ===========================
class Attribute(models.Model):
    name = models.CharField(max_length=50, help_text="نام ویژگی (مثلا رنگ یا سایز)")

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE,
        related_name='values',
        help_text="ویژگی مرتبط"
    )
    value = models.CharField(max_length=50, help_text="مقدار ویژگی (مثلا قرمز یا XL)")

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


# ===========================
# مدل واریانت محصول (ProductVariant)
# برای رنگ/سایز و موجودی و قیمت متفاوت
# ===========================
class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='variants',
        help_text="محصول مرتبط"
    )
    sku = models.CharField(
        max_length=50, unique=True,
        help_text='کد اختصاصی واریانت برای انبار'
    )
    price = models.DecimalField(max_digits=12, decimal_places=0, help_text="قیمت فروش محصول")
    discount_price = models.DecimalField(
        max_digits=12, decimal_places=0,
        blank=True, null=True,
        help_text='قیمت پس از تخفیف (اختیاری)'
    )

    # موجودی و آستانه هشدار
    stock = models.PositiveIntegerField(default=0, help_text="موجودی واریانت")
    low_stock_threshold = models.PositiveIntegerField(
        default=5, help_text="آستانه هشدار اتمام موجودی"
    )

    # ویژگی های واریانت (مثلا رنگ یا سایز)
    attributes = models.ManyToManyField(
        AttributeValue, related_name='variants', blank=True,
        help_text="ویژگی‌های مرتبط با این واریانت"
    )

    expiration_date = models.DateField(blank=True, null=True, help_text="تاریخ انقضای محصول (اختیاری)")

    # =======================
    # فیلدهای جدید برای مدیریت قیمت
    # =======================
    purchase_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="قیمت خرید از تأمین‌کننده"
    )
    profit_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=20.00,
        help_text="درصد سود محصول بر اساس قیمت خرید"
    )

    created_at = models.DateTimeField(auto_now_add=True, help_text="تاریخ ایجاد واریانت")

    def __str__(self):
        try:
            attrs = ", ".join([f"{attr.attribute.name}: {attr.value}" for attr in self.attributes.all()])
            return f"{self.product.name} ({attrs})" if attrs else self.product.name
        except:
            return self.product.name

    @property
    def calculated_price(self):
        """محاسبه قیمت فروش بر اساس درصد سود و قیمت خرید، با رند کردن به نزدیک‌ترین 100 تومان"""
        if self.purchase_price:
            final_price = self.purchase_price * (Decimal(1) + self.profit_percent / Decimal(100))
            return final_price.quantize(Decimal('100'), rounding=ROUND_HALF_UP)
        return None


# ==============================
# مدل تصاویر محصول (ProductImage)
# ==============================
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='images',
        help_text="محصول مرتبط با تصویر"
    )
    image = models.ImageField(upload_to='product_images/', blank=True, null=True, help_text="فایل تصویر محصول")
    source_url = models.URLField(blank=True, null=True, help_text="لینک تصویر از تأمین‌کننده")
    alt_text = models.CharField(max_length=255, blank=True, null=True, help_text="متن جایگزین تصویر برای SEO")
    is_main = models.BooleanField(default=False, help_text="آیا تصویر اصلی محصول است؟")
    created_at = models.DateTimeField(auto_now_add=True, help_text="تاریخ ایجاد تصویر")

    def __str__(self):
        return f"Image of {self.product.name} - {self.source_url or 'No URL'}"


# ==============================
# مدل ویدئوهای محصول (ProductVideo)
# ==============================
class ProductVideo(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='videos',
        help_text="محصول مرتبط با ویدئو"
    )
    video = models.FileField(upload_to='product_videos/', help_text='فایل ویدئو')
    caption = models.CharField(max_length=255, blank=True, null=True, help_text="توضیح یا کپشن ویدئو")
    created_at = models.DateTimeField(auto_now_add=True, help_text="تاریخ ایجاد ویدئو")

    def __str__(self):
        return f"Video of {self.product.name}"


# ==============================
# محصولات ویژه (SpecialProduct)
# ==============================
class SpecialProduct(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='special', help_text="محصول ویژه")
    title = models.CharField(max_length=255, blank=True, null=True, help_text="عنوان ویژه برای نمایش")
    start_date = models.DateTimeField(blank=True, null=True, help_text="تاریخ شروع ویژه بودن")
    end_date = models.DateTimeField(blank=True, null=True, help_text="تاریخ پایان ویژه بودن")
    is_active = models.BooleanField(default=True, help_text="آیا محصول ویژه فعال است؟")

    def __str__(self):
        return f"ویژه: {self.product.name}"


# ==============================
# تصاویر واریانت محصول (ProductVariantImage)
# ==============================
class ProductVariantImage(models.Model):
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.CASCADE, related_name='images',
        help_text="واریانت مرتبط با تصویر"
    )
    image = models.ImageField(
        upload_to='variant_images/',
        blank=True, null=True,
        help_text="فایل تصویر واریانت"
    )
    source_url = models.URLField(
        blank=True, null=True,
        help_text="لینک تصویر اصلی واریانت از تأمین‌کننده (اختیاری)"
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True, null=True,
        help_text="متن جایگزین تصویر برای SEO"
    )
    is_main = models.BooleanField(
        default=False,
        help_text="آیا این تصویر به عنوان تصویر اصلی واریانت استفاده شود؟"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="تاریخ ایجاد تصویر واریانت"
    )

    def __str__(self):
        return f"Image of {self.variant.product.name} - {self.variant.sku} - {self.source_url or 'No URL'}"



# ==============================
# تصاویر تغیرات قیمت (PriceChangeLog)
# ==============================

class PriceChangeLog(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    old_price = models.DecimalField(max_digits=12, decimal_places=2)
    new_price = models.DecimalField(max_digits=12, decimal_places=2)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.variant.product.name}: {self.old_price} → {self.new_price}"
