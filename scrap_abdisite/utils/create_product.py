#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
import json
import time
from decimal import Decimal
from urllib.parse import urlparse
import requests
import logging

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ---------- مسیر پروژه و sys.path ----------
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_file_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ---------- تنظیمات Django ----------
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazbia_shop.settings")
django.setup()

from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.contrib.auth import get_user_model

from products.models import (
    Product, Category, Tag, ProductSpecification, ProductImage, ProductVariant
)
from scrap_abdisite.models import WatchedURL
from suppliers.models import Supplier


# ---------- توابع کمکی ----------
def generate_unique_slug(name):
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def download_and_attach_images(product: Product, image_urls: list, main_index: int = 0):
    for idx, url in enumerate(image_urls or []):
        if not url:
            continue
        if ProductImage.objects.filter(product=product, source_url=url).exists():
            logger.info(f"⏭️ تصویر تکراری رد شد: {url}")
            continue
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                logger.error(f"❌ دانلود نشد ({response.status_code}): {url}")
                continue
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path) or f"{product.slug}_{idx}.jpg"
            filename = filename.encode("latin1", "ignore").decode("latin1")
            image_instance = ProductImage(
                product=product,
                source_url=url,
                is_main=(idx == main_index)
            )
            image_instance.image.save(filename, ContentFile(response.content), save=True)
            logger.info(f"✅ تصویر ذخیره شد: {filename}")
        except Exception as e:
            logger.error(f"❌ خطا در دانلود {url}: {e}")
            raise e


# ---------- تابع اصلی import ----------
def import_products():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    EDITED_FOLDER = os.path.join(BASE_DIR, "data/edited")

    # ---------- پیدا کردن آخرین فایل edited ----------
    all_edited_files = glob.glob(os.path.join(EDITED_FOLDER, "edited_*.json"))
    if not all_edited_files:
        logger.info("⚠️ هیچ فایل JSON ویرایش‌شده‌ای پیدا نشد. پردازش متوقف شد.")
        return

    latest_edited_file = max(all_edited_files, key=os.path.getmtime)
    logger.info(f"آخرین فایل ویرایش‌شده: {latest_edited_file}")

    # نام فایل created و creating بر اساس همان edited
    created_file = latest_edited_file.replace("edited_", "created_")
    creating_file = latest_edited_file.replace("edited_", "creating_")

    # ---------- اگر فایل created وجود داشت پردازش لازم نیست ----------
    if os.path.exists(created_file):
        logger.info(f"✅ فایل {created_file} قبلاً ساخته شده است. نیازی به پردازش نیست.")
        
            # ایجاد فایل stopemail
        STOP_EMAIL_FILE = os.path.join(BASE_DIR, "stopemail")
        with open(STOP_EMAIL_FILE, "w") as f:
          f.write("")  # خالی
        return

    # ---------- اگر creating وجود داشت از همان ادامه بده ----------
    if os.path.exists(creating_file):
        logger.info(f"⚡ ادامه پردازش از فایل existing creating: {creating_file}")
    else:
        # ایجاد فایل creating جدید از edited
        with open(latest_edited_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        with open(creating_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"فایل creating ساخته شد: {creating_file}")

    # ---------- پردازش محصولات ----------
    with open(creating_file, "r+", encoding="utf-8") as f:
        data = json.load(f)

        supplier, _ = Supplier.objects.get_or_create(name="عمده فروش عبدی")
        User = get_user_model()
        try:
            flip_user = User.objects.get(username="flip")
        except User.DoesNotExist:
            logger.error("❌ کاربر flip پیدا نشد. پردازش متوقف شد.")
            return

        BATCH_SIZE = 10
        SLEEP_TIME = 2

        for idx, item in enumerate(data, start=1):
            if item.get("status") == "created":
                logger.info(f"⏭️ محصول '{item.get('name', 'نامعلوم')}' قبلا پردازش شده است.")
                continue

            try:
                name = item.get('name', 'نامعلوم')
                price = Decimal(item.get('price') or 0)
                product_link = item.get('product_link')
                category_slug = slugify(item.get('category') or '')

                category = None
                if category_slug:
                    category, _ = Category.objects.get_or_create(
                        slug=category_slug,
                        defaults={'name': item.get('category') or ''}
                    )

                product, created = Product.objects.update_or_create(
                    name=name,
                    defaults={
                        'slug': generate_unique_slug(name),
                        'base_price': price * Decimal("1.2") if price > 0 else Decimal("0"),
                        'category': category,
                        'description': item.get('description') or '',
                        'is_active': True
                    }
                )

                # ایجاد و بروزرسانی واریانت‌ها
                if not product.variants.exists():
                    base_sku = f"{product.slug}-default"
                    sku = base_sku
                    counter = 1
                    while ProductVariant.objects.filter(sku=sku).exists():
                        sku = f"{base_sku}-{counter}"
                        counter += 1
                    ProductVariant.objects.create(
                        product=product,
                        sku=sku,
                        price=product.base_price,
                        stock=0
                    )

                if 'quantity' in item and item['quantity'] is not None:
                    for variant in product.variants.all():
                        variant.stock = item['quantity']
                        variant.save()

                if price == 0:
                    for variant in product.variants.all():
                        variant.stock = 0
                        variant.save()

                # تگ‌ها
                for tag_name in item.get('tags') or []:
                    tag_slug = slugify(tag_name)
                    tag, _ = Tag.objects.get_or_create(slug=tag_slug, defaults={'name': tag_name})
                    product.tags.add(tag)

                # مشخصات
                existing_specs = {(spec.name, spec.value) for spec in product.specifications.all()}
                for spec in item.get('specifications') or []:
                    if ':' in spec:
                        spec_name, spec_value = [part.strip() for part in spec.split(':', 1)]
                        if (spec_name, spec_value) not in existing_specs:
                            ProductSpecification.objects.create(
                                product=product,
                                name=spec_name,
                                value=spec_value
                            )

                # WatchedURL
                if product_link:
                    WatchedURL.objects.update_or_create(
                        user=flip_user,
                       variant=variant,
                        supplier=supplier,
                        url=product_link,
                        defaults={"price": price}
                    )

                # تصاویر
                download_and_attach_images(product, item.get('images') or [], main_index=0)

                item["status"] = "created"
                logger.info(f"✅ محصول '{name}' پردازش شد و ذخیره شد (ID: {product.id}).")

            except Exception as e:
                logger.error(f"❌ خطا در پردازش محصول '{item.get('name', 'نامعلوم')}': {e}")
                raise e

            # ذخیره دوره‌ای
            if idx % BATCH_SIZE == 0:
                logger.info(f"💤 توقف کوتاه {SLEEP_TIME} ثانیه بعد از {idx} محصول")
                f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.truncate()
                f.flush()
                time.sleep(SLEEP_TIME)

        # ذخیره نهایی
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.truncate()
        f.flush()

    # تغییر نام creating → created
    os.rename(creating_file, created_file)
    logger.info(f"✅ همه محصولات پردازش شدند و فایل ایجاد شد: {created_file}")


if __name__ == "__main__":
    import_products()
