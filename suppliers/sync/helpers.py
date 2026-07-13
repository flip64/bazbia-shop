# -*- coding: utf-8 -*-

import re
from decimal import Decimal
from django.utils.text import slugify

from products.models import Product, ProductVariant


# ==============================
# ساخت اسلاگ یکتا
# ==============================
def unique_slug(name):
    max_length = Product._meta.get_field("slug").max_length

    base = slugify(name)

    if not base:
        base = "product"

    base = base[:max_length]

    slug = base
    i = 1

    while Product.objects.filter(slug=slug).exists():
        suffix = "-{}".format(i)
        slug = "{}{}".format(base[: max_length - len(suffix)], suffix)
        i += 1

    return slug


# ==============================
# ساخت SKU یکتا
# ==============================
def unique_sku(text):

    base = slugify(text)

    if not base:
        base = "sku"

    base = base[:40]

    sku = base
    i = 1

    while ProductVariant.objects.filter(sku=sku).exists():
        sku = "{}-{}".format(base, i)
        i += 1

    return sku


# ==============================
# تبدیل قیمت به Decimal
# ==============================
def to_decimal(value):

    if value is None:
        return Decimal("0")

    if isinstance(value, Decimal):
        return value

    value = str(value)

    value = value.replace(",", "")
    value = value.replace("٬", "")
    value = value.replace(" ", "")

    try:
        return Decimal(value)
    except:
        return Decimal("0")


# ==============================
# تبدیل موجودی
# ==============================
def to_stock(value):

    try:
        return int(value)
    except:
        return 0


# ==============================
# نرمال کردن نام محصول
# ==============================
def normalize_name(name):

    if not name:
        return ""

    name = re.sub(r"\s+", " ", name)

    return name.strip()


# ==============================
# وضعیت موجودی
# ==============================
def is_available(stock):

    return to_stock(stock) > 0


# ==============================
# حذف اسلش انتهای لینک
# ==============================
def normalize_url(url):

    if not url:
        return ""

    return url.strip().rstrip("/")
