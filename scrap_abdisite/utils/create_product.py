import os
import glob
import re
import json
from decimal import Decimal
from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile
from django.utils.text import slugify

from products.models import Product, Category, Tag, ProductSpecification, ProductImage
from scrap_abdisite.models import WatchedURL
from suppliers.models import Supplier


def import_products_from_json(user):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # scrap_abdisite/
    EDITED_FOLDER = os.path.join(BASE_DIR, "data/edited")

    pattern = re.compile(r"edited_(\d{8})_(\d{4})_\d+\.json$")
    list_of_files = [
        f for f in glob.glob(os.path.join(EDITED_FOLDER, "*.json"))
        if pattern.search(os.path.basename(f))
    ]

    print(f"Found {len(list_of_files)} edited JSON files.")

    if not list_of_files:
        raise FileNotFoundError("هیچ فایل JSON ویرایش‌شده‌ای پیدا نشد.")

    def file_key(f):
        match = pattern.search(os.path.basename(f))
        date_part = match.group(1)
        time_part = match.group(2)
        return date_part + time_part

    latest_file = max(list_of_files, key=file_key)
    print(f"Using latest JSON file: {latest_file}")

    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    supplier, _ = Supplier.objects.get_or_create(name="عمده فروش عبدی")
    print(f"Using supplier: {supplier.name}")

    for idx, item in enumerate(data, start=1):
        name = item.get('name')
        price = Decimal(item.get('price', 0))
        product_link = item.get('product_link')
        category_slug = slugify(item.get('category', ''))

        category = None
        if category_slug:
            category, _ = Category.objects.get_or_create(
                slug=category_slug,
                defaults={'name': item['category']}
            )

        product, created = Product.objects.update_or_create(
            name=name,
            defaults={
                'slug': generate_unique_slug(name),
                'base_price': price * Decimal("1.2") if price > 0 else Decimal("0"),
                'category': category,
                'description': item.get('description', ''),
                'is_active': True
            }
        )
        action = "Created" if created else "Updated"
        print(f"[{idx}/{len(data)}] {action} product: {product.name}")

        # تگ‌ها
        for tag_name in item.get('tags', []):
            tag_slug = slugify(tag_name)
            tag, _ = Tag.objects.get_or_create(slug=tag_slug, defaults={'name': tag_name})
            product.tags.add(tag)
        if item.get('tags'):
            print(f" - Added tags: {', '.join(item.get('tags'))}")

        # ویژگی‌ها
        existing_specs = {(spec.name, spec.value) for spec in product.specifications.all()}
        for spec in item.get('specifications', []):
            if ':' in spec:
                spec_name, spec_value = [part.strip() for part in spec.split(':', 1)]
                if (spec_name, spec_value) not in existing_specs:
                    ProductSpecification.objects.create(
                        product=product,
                        name=spec_name,
                        value=spec_value
                    )
        if item.get('specifications'):
            print(f" - Added specifications: {', '.join(item.get('specifications'))}")

        # موجودی صفر اگر قیمت صفر
        if price == 0:
            for variant in product.variants.all():
                variant.stock = 0
                variant.save()

        # WatchedURL
        WatchedURL.objects.update_or_create(
            user=user,
            product=product,
            supplier=supplier,
            url=product_link,
            defaults={'price': price}
        )

        # تصاویر
        image_urls = item.get('image_links', [])
        if image_urls:
            print(f" - Downloading {len(image_urls)} images...")
            download_and_attach_images(product, image_urls, main_index=0)


def generate_unique_slug(name):
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def download_and_attach_images(product: Product, image_urls: list, main_index: int = 0):
    print("be inja residim")
    for idx, url in enumerate(image_urls):
        if not url:
            continue
        if ProductImage.objects.filter(product=product, source_url=url).exists():
            print(f"   - Image already exists: {url}")
            continue
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                print(f"   - Failed to download (status {response.status_code}): {url}")
                continue

            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path) or f"{product.slug}_{idx}.jpg"

            image_instance = ProductImage(
                product=product,
                source_url=url,
                is_main=(idx == main_index)
            )
            image_instance.image.save(filename, ContentFile(response.content), save=True)
            print(f"   - Saved image: {filename}")

        except Exception as e:
            print(f"   - Error downloading image {url}: {e}")
            
