#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
create_products_from_raw.py
- خواندن آخرین raw_*.json
- فیلتر کردن لینک‌هایی که قبلاً در WatchedURL ثبت شده‌اند
- برای هر لینک جدید:
    - گرفتن جزئیات از abdi_fetcher
    - ساخت Product (is_active=False)
    - ساخت یک ProductVariant با purchase_price و price
    - ذخیره تصاویر در ProductImage
    - ثبت WatchedURL با variant و supplier
- ارسال گزارش ایمیل و لاگ کامل
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from urllib.parse import urlparse
from decimal import Decimal

# ------------------ راه‌اندازی Django ------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazbia_shop.settings")

import django
django.setup()

from django.db import transaction
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

# ------------------ مدل‌ها ------------------
from products.models import (
    Product, ProductVariant, ProductImage, ProductSpecification, Tag, Category
)
from suppliers.models import Supplier
from scrap_abdisite.models import WatchedURL

# ------------------ توابع استخراج (abdi_fetcher) ------------------
from scrap_abdisite.utils.abdi_fetcher import (
    fetch_product_details,
    extract_specifications,
    extract_tags,
    extract_product_images,
    extract_quantity,
)

# ------------------ تنظیم لاگ ------------------
LOG_DIR = os.path.join(BASE_DIR, "scrap_abdisite", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"create_products_from_raw_{datetime.now():%Y%m%d_%H%M%S}.log")

logger = logging.getLogger("create_products_from_raw")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
ch = logging.StreamHandler()
fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
fh.setFormatter(fmt)
ch.setFormatter(fmt)
logger.addHandler(fh)
logger.addHandler(ch)

# ------------------ مسیر فایل raw ------------------
RAW_FOLDER = os.path.join(BASE_DIR, "scrap_abdisite", "data", "raw")

# ------------------ کمکی‌ها ------------------
def get_latest_raw_file():
    files = [f for f in os.listdir(RAW_FOLDER) if f.startswith("raw_") and f.endswith(".json")]
    if not files:
        return None
    files.sort(key=lambda f: os.path.getmtime(os.path.join(RAW_FOLDER, f)), reverse=True)
    return os.path.join(RAW_FOLDER, files[0])

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def download_and_attach_image(product, img_url, is_main=False):
    """دانلود عکس و ذخیره در ProductImage (اجتناب از تکرار بر اساس source_url)"""
    try:
        if not img_url:
            return None
        # جلوگیری از تکراری بودن تصویر
        if ProductImage.objects.filter(product=product, source_url=img_url).exists():
            logger.info(f"⏭️ تصویر تکراری، رد شد: {img_url}")
            return None

        resp = None
        import requests
        resp = requests.get(img_url, timeout=20)
        if resp.status_code != 200:
            logger.warning(f"❌ عدم دریافت تصویر ({resp.status_code}): {img_url}")
            return None

        parsed = urlparse(img_url)
        filename = os.path.basename(parsed.path) or f"{slugify(product.name)}.jpg"
        # امن‌سازی اسم فایل
        filename = filename.split("?")[0]
        content = ContentFile(resp.content)
        img = ProductImage(product=product, source_url=img_url, is_main=is_main)
        img.image.save(filename, content, save=True)
        logger.info(f"✅ تصویر ذخیره شد: {filename}")
        return img
    except Exception as e:
        logger.error(f"❌ خطا در دانلود/ذخیره تصویر {img_url}: {e}")
        logger.debug(traceback.format_exc())
        return None

def unique_sku(base):
    """تولید SKU یکتا بر پایه base"""
    candidate = slugify(base)[:30]
    sku = candidate
    counter = 1
    while ProductVariant.objects.filter(sku=sku).exists():
        sku = f"{candidate}-{counter}"
        counter += 1
    return sku

# ------------------ ایجاد Supplier و کاربر پیش‌فرض ------------------
def get_supplier():
    supplier_name = "عمده فروش عبدی"
    supplier, _ = Supplier.objects.get_or_create(name=supplier_name)
    return supplier

def get_default_user():
    User = get_user_model()
    try:
        user = User.objects.get(username="flip")
    except User.DoesNotExist:
        user = User.objects.filter(is_superuser=True).first() or User.objects.first()
    return user

# ------------------ عملیات اصلی برای یک آیتم ------------------
def process_item(item, supplier, user):
    link = item.get("product_link") or item.get("url") or item.get("product_link")
    if not link:
        logger.warning(f"⏭️ آیتم بدون لینک رد شد: {item.get('name')}")
        return None

    try:
        logger.info(f"🔎 پردازش لینک: {link}")

        # گرفتن جزئیات از abdi_fetcher
        name, price = fetch_product_details(link)
        specs = extract_specifications(link) or []
        tags = extract_tags(link) or []
        images = extract_product_images(link) or []
        quantity = extract_quantity(link)

        # مقداردهی اولیه برای فیلدها
        name = name or item.get("name") or "نامشخص"
        price_val = Decimal(price) if price is not None else Decimal(0)
        base_price = price_val

        # دسته‌بندی: اگر فایل raw category داشت تلاش کن دسته بسازی/یافت کنی
        category = None
        cat_name = item.get("category") or item.get("cat") or None
        if cat_name:
            cat_slug = slugify(cat_name)
            category, _ = Category.objects.get_or_create(slug=cat_slug, defaults={"name": cat_name})

        with transaction.atomic():
            # ساخت محصول غیرفعال
            slug_candidate = slugify(name)
            # تضمین یونیک بودن slug
            slug = slug_candidate
            sctr = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{slug_candidate}-{sctr}"
                sctr += 1

            product = Product.objects.create(
                name=name,
                slug=slug,
                description=item.get("description") or "",
                base_price=base_price,
                category=category,
                is_active=False,
                quantity=quantity or 0
            )

            # مشخصات
            for spec in specs:
                if ":" in spec:
                    k, v = spec.split(":", 1)
                    ProductSpecification.objects.create(product=product, name=k.strip(), value=v.strip())
                else:
                    ProductSpecification.objects.create(product=product, name=spec.strip(), value="")

            # تگ‌ها
            for tag_name in tags + item.get("tags", []):
                if not tag_name:
                    continue
                tag_slug = slugify(tag_name)
                tag_obj, _ = Tag.objects.get_or_create(slug=tag_slug, defaults={"name": tag_name})
                product.tags.add(tag_obj)

            # واریانت (یک واریانت برای هر محصول)
            sku = unique_sku(f"{product.slug}-default")
            variant = ProductVariant.objects.create(
                product=product,
                sku=sku,
                price=price_val,
                purchase_price=price_val,
                stock=quantity or 0,
                profit_percent=30.0
            )

            # تصاویر: دانلود و attach
            main_done = False
            for idx, img_url in enumerate(images):
                if not img_url:
                    continue
                img_inst = download_and_attach_image(product, img_url, is_main=(not main_done))
                if img_inst and not main_done:
                    main_done = True

            # اگر در فایل raw تصویری بود و از abdi_fetcher تصویری نیومد، استفاده کن
            raw_images = item.get("images") or item.get("image_links") or []
            for img_url in raw_images:
                if not img_url:
                    continue
                # فقط اضافه کن اگر منبع مشابه وجود نداره
                if not ProductImage.objects.filter(product=product, source_url=img_url).exists():
                    download_and_attach_image(product, img_url, is_main=False)

            # ثبت WatchedURL
            WatchedURL.objects.create(
                user=user,
                variant=variant,
                supplier=supplier,
                url=link,
                price=price_val
            )

            logger.info(f"✅ ساخته شد: {product.name} (SKU: {variant.sku})")
            return {"name": product.name, "link": link, "price": str(price_val)}
    
    except Exception as e:
        logger.error(f"❌ خطا در پردازش {link}: {e}")
        logger.debug(traceback.format_exc())
        return None

# ------------------ تابع اصلی ------------------
def main():
    logger.info("🚀 شروع اجرای create_products_from_raw")

    latest = get_latest_raw_file()
    if not latest:
        logger.warning("⚠️ هیچ فایل raw پیدا نشد در: %s", RAW_FOLDER)
        return

    try:
        raw_items = load_json(latest)
    except Exception as e:
        logger.error(f"❌ خطا در خواندن فایل JSON {latest}: {e}")
        return

    logger.info(f"📦 فایل raw بارگذاری شد: {os.path.basename(latest)} - مجموع آیتم‌ها: {len(raw_items)}")

    # لینک‌های ثبت شده در WatchedURL
    existing_urls = set(WatchedURL.objects.values_list("url", flat=True))
    logger.info(f"🗂 تعداد لینک‌های موجود در WatchedURL: {len(existing_urls)}")

    # تامین‌کننده و کاربر پیش‌فرض
    supplier = get_supplier()
    user = get_default_user()
    if not user:
        logger.warning("⚠️ هیچ کاربری برای ثبت WatchedURL یافت نشد؛ WatchedURL با user=NULL ساخته خواهد شد.")

    new_items = [it for it in raw_items if it.get("product_link") and it.get("product_link") not in existing_urls]
    logger.info(f"🆕 آیتم‌های جدید برای پردازش: {len(new_items)}")

    created = []
    for item in new_items:
        res = process_item(item, supplier, user)
        if res:
            created.append(res)

    # گزارش ایمیل
    try:
        if created:
            subject = f"🆕 گزارش تولید محصولات جدید - {len(created)} محصول"
            body_lines = [f"- {c['name']} | {c['link']} | قیمت: {c['price']}" for c in created]
            body = "محصولات جدید ساخته شده:\n\n" + "\n".join(body_lines)
        else:
            subject = "✅ هیچ محصول جدیدی ساخته نشد"
            body = "در این اجرا هیچ محصول جدیدی یافت یا ساخته نشد."

        recipients = [getattr(settings, "ADMIN_EMAIL", None) or getattr(settings, "DEFAULT_FROM_EMAIL", None)]
        recipients = [r for r in recipients if r]
        if recipients:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=False)
            logger.info("📧 ایمیل گزارش ارسال شد به: %s", ", ".join(recipients))
        else:
            logger.info("ℹ️ آدرس ایمیل مدیر تنظیم نشده؛ ایمیل ارسال نشد.")
    except Exception as e:
        logger.error(f"❌ خطا در ارسال ایمیل گزارش: {e}")
        logger.debug(traceback.format_exc())

    logger.info("🎯 عملیات پایان یافت. محصولات ساخته‌شده: %d", len(created))
    print(f"🎯 عملیات پایان یافت. محصولات ساخته‌شده: {len(created)}")

if __name__ == "__main__":
    main()
