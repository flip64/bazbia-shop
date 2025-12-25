#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, json, logging, traceback, time
from datetime import datetime
from urllib.parse import urlparse
from decimal import Decimal

# ================= Django setup =================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazbia_shop.settings")

import django
django.setup()

from django.db import transaction
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django.conf import settings
from django.contrib.auth import get_user_model

# ================= Models =================
from products.models import (
    Product, ProductVariant, ProductImage, ProductSpecification, Tag, Category
)
from suppliers.models import Supplier
from scrap_abdisite.models import WatchedURL

# ================= Fetchers =================
from scrap_abdisite.utils.abdi_fetcher import (
    fetch_product_details,
    extract_specifications,
    extract_tags,
    extract_product_images,
    extract_quantity,
)

# ================= Logging =================
LOG_DIR = os.path.join(BASE_DIR, "scrap_abdisite", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(
    LOG_DIR, f"create_products_from_raw_{datetime.now():%Y%m%d_%H%M%S}.log"
)

logger = logging.getLogger("create_products_from_raw")
logger.setLevel(logging.INFO)

if not logger.handlers:
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    ch = logging.StreamHandler()
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)

# ================= Paths =================
RAW_FOLDER = os.path.join(BASE_DIR, "scrap_abdisite", "data", "raw")

# ================= Helpers =================
def get_latest_raw_file():
    files = [f for f in os.listdir(RAW_FOLDER) if f.startswith("raw_")]
    if not files:
        return None
    files.sort(key=lambda f: os.path.getmtime(os.path.join(RAW_FOLDER, f)), reverse=True)
    return os.path.join(RAW_FOLDER, files[0])

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_link(item):
    return item.get("product_link") or item.get("url")

def unique_sku(base):
    sku = slugify(base)[:30]
    base_sku = sku
    i = 1
    while ProductVariant.objects.filter(sku=sku).exists():
        sku = f"{base_sku}-{i}"
        i += 1
    return sku

# ================= Image Handler =================
def download_and_attach_image(product, img_url, is_main=False):
    try:
        import requests

        if not img_url:
            return None

        if ProductImage.objects.filter(product=product, source_url=img_url).exists():
            return None

        resp = requests.get(
            img_url,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        if resp.status_code != 200:
            return None

        if not resp.headers.get("Content-Type", "").startswith("image/"):
            logger.warning(f"❌ Not image: {img_url}")
            return None

        ext = os.path.splitext(urlparse(img_url).path)[1] or ".jpg"
        filename = f"{slugify(product.name)}-{int(time.time())}{ext}"

        img = ProductImage(product=product, source_url=img_url, is_main=is_main)
        img.image.save(filename, ContentFile(resp.content), save=True)
        return img

    except Exception as e:
        logger.error(f"❌ Image error {img_url}: {e}")
        return None

# ================= Core =================
def get_supplier():
    return Supplier.objects.get_or_create(name="عمده فروش عبدی")[0]

def get_user():
    User = get_user_model()
    return User.objects.filter(is_superuser=True).first()

def process_item(item, supplier, user):
    link = get_link(item)
    if not link:
        return None

    logger.info(f"🔎 Processing: {link}")

    try:
        name, price = fetch_product_details(link)
        specs = extract_specifications(link) or []
        tags = extract_tags(link) or []
        images = extract_product_images(link) or []
        quantity = extract_quantity(link) or 0

        name = name or item.get("name") or "نامشخص"
        price = Decimal(price or 0)

        category = None
        if item.get("category"):
            category, _ = Category.objects.get_or_create(
                slug=slugify(item["category"]),
                defaults={"name": item["category"]}
            )

        with transaction.atomic():
            slug = slugify(name)
            i = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{slug}-{i}"
                i += 1

            product = Product.objects.create(
                name=name,
                slug=slug,
                base_price=price,
                description=item.get("description", ""),
                category=category,
                quantity=quantity,
                is_active=False
            )

            for spec in specs:
                if ":" in spec:
                    k, v = spec.split(":", 1)
                    ProductSpecification.objects.create(
                        product=product, name=k.strip(), value=v.strip()
                    )

            for tag in (tags or []) + item.get("tags", []):
                if tag:
                    t, _ = Tag.objects.get_or_create(
                        slug=slugify(tag), defaults={"name": tag}
                    )
                    product.tags.add(t)

            variant = ProductVariant.objects.create(
                product=product,
                sku=unique_sku(product.slug),
                price=price,
                purchase_price=price,
                stock=quantity,
                profit_percent=30
            )

            if not WatchedURL.objects.filter(url=link).exists():
                WatchedURL.objects.create(
                    user=user,
                    variant=variant,
                    supplier=supplier,
                    url=link,
                    price=price
                )

        # 🔥 images OUTSIDE transaction
        main = False
        for img in images:
            if download_and_attach_image(product, img, is_main=not main):
                main = True

        for img in item.get("image_links", []):
            download_and_attach_image(product, img)

        logger.info(f"✅ Created: {product.name}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed {link}: {e}")
        logger.debug(traceback.format_exc())
        return False

# ================= Main =================
def main():
    logger.info("🚀 create_products_from_raw started")

    raw_file = get_latest_raw_file()
    if not raw_file:
        logger.warning("No raw file found")
        return

    items = load_json(raw_file)
    existing = set(WatchedURL.objects.values_list("url", flat=True))

    supplier = get_supplier()
    user = get_user()

    for item in items:
        link = get_link(item)
        if link and link not in existing:
            process_item(item, supplier, user)

    logger.info("🎯 Finished")

if __name__ == "__main__":
    main()
