from django.db import models
import os
import uuid
from django.utils.text import slugify



# ==============================
# مدل دسته‌بندی محصولات (Category)
# ==============================
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    # برای پشتیبانی از دسته‌بندی درختی
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='subcategories'
    )

    def __str__(self):
        # اگر زیر دسته بود، با فلش نشون بده
        return f"{self.parent.name} -> {self.name}" if self.parent else self.name



# ==============================
# مدل تگ محصولات (Tag)
# ==============================
class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name



# ==============================
# مدل محصول (Product)
# ==============================
class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)

    # قیمت بر حسب تومان (یا هر واحد پیشفرض)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)

    # دسته اصلی محصول
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='products'
    )

    # تگ‌های محصول (many to many)
    tags = models.ManyToManyField(Tag, blank=True, related_name='products')

   
    # فعال یا غیرفعال بودن محصول در فروشگاه
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# ===========================
# 🔍 مشخصات ثابت محصول (Specifications)
# مثلا جنس، وزن، کشور سازنده
# ===========================
class ProductSpecification(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='specifications'
    )
    name = models.CharField(max_length=100)    # مثلا جنس
    value = models.CharField(max_length=255)   # مثلا فلز

    def __str__(self):
        return f"{self.name}: {self.value} ({self.product.name})"


# ===========================
# 🎨 ویژگی ها (Attribute) و مقادیر آنها (AttributeValue)
# مثل رنگ / سایز که بعدا برای Variant استفاده میشه
# ===========================
class Attribute(models.Model):
    name = models.CharField(max_length=50)     # مثل رنگ یا سایز

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(
        Attribute, on_delete=models.CASCADE,
        related_name='values'
    )
    value = models.CharField(max_length=50)    # مثل قرمز یا XL

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


# ===========================
# 🎯 Variant
# برای تفاوت قیمت / موجودی مثل رنگ + سایز
# ===========================
class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='variants'
    )
    sku = models.CharField(
        max_length=50, unique=True,
        help_text='کد اختصاصی محصول برای انبار'
    )
    price = models.DecimalField(max_digits=12, decimal_places=2)

    discount_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        blank=True, null=True,
        help_text='قیمت پس از تخفیف (اختیاری)'
    )

    stock = models.PositiveIntegerField(default=0)
    attributes = models.ManyToManyField(
        AttributeValue, related_name='variants',
        blank=True
    )
    expiration_date = models.DateField(blank=True, null=True, help_text="تاریخ انقضای محصول")

  
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(
        default=5,
        help_text="آستانه هشدار اتمام موجودی برای این واریانت"
    )

    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.sku}"








# ==============================
# مدل تصاویر محصول (ProductImage)
# ==============================
class ProductImage(models.Model):
    # ارتباط با محصول
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='images'
    )

    # خود تصویر (دانلود شده)
    image = models.ImageField(
        upload_to='product_images/',
        help_text='مسیر ذخیره تصویر در media',
        blank=True, null=True
    )

    # لینک تصویر از تأمین‌کننده
    source_url = models.URLField(
        blank=True, null=True, unique=True,
        help_text='لینک تصویر اصلی از تأمین‌کننده (اختیاری)'
    )

    # متن جایگزین (برای SEO و کاربران نابینا)
    alt_text = models.CharField(
        max_length=255, blank=True, null=True
    )

    # آیا این تصویر به عنوان تصویر اصلی استفاده میشه؟
    is_main = models.BooleanField(
        default=False, help_text='تصویر اصلی محصول'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image of {self.product.name} - {self.source_url or 'No URL'}"

# ==============================
# مدل ویدئوهای محصول (ProductVideo)
# ==============================
class ProductVideo(models.Model):
    # ارتباط با محصول
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE,
        related_name='videos'
    )

    # فایل ویدئو
    video = models.FileField(
        upload_to='product_videos/',
        help_text='مسیر ذخیره ویدئو در media'
    )

    # کپشن (مثلا توضیح ویدئو)
    caption = models.CharField(
        max_length=255, blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Video of {self.product.name}"


# ==============================
# مدل  محصولات ویژه (SpecialProduct)
# ==============================


class SpecialProduct(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='special')
    title = models.CharField(max_length=255, blank=True, null=True)  # عنوان خاص برای اسلایدر مثلاً
    start_date = models.DateTimeField(blank=True, null=True)  # از چه تاریخی ویژه شده؟
    end_date = models.DateTimeField(blank=True, null=True)  # تا چه تاریخی ویژه هست؟
    is_active = models.BooleanField(default=True)  # فعال یا غیرفعال بودن نمایش

    def __str__(self):
        return f"ویژه: {self.product.name}"








