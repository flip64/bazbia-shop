import os
import glob
import re
import json
from decimal import Decimal
from urllib.parse import urlparse
import requests
import logging

# Django imports
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "your_project.settings")  # جایگزین با settings خودت
django.setup()

from django.core.files.base import ContentFile
from django.utils.text import slugify
from products.models import Product, Category, Tag, ProductSpecification, ProductImage, ProductVariant
from scrap_abdisite.models import WatchedURL
from suppliers.models import Supplier
from django.contrib.auth import get_user_model

# ------------------- Logging -------------------
logging.basicConfig(
    filename="import_products.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)
logger = logging.getLogger(__name__)

# ------------------- Helper Functions -------------------
def generate_unique_slug(name):
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug

def download_and_attach_images(product: Product, image_urls: list, main_index: int = 0):
    for idx, url in enumerate(image_urls):
        if not url:
            continue
        if ProductImage.objects.filter(product=product, source_url=url).exists():
            logger.info(f"Duplicate image skipped: {url}")
            continue
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                logger.error(f"Download failed ({response.status_code}): {url}")
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
            logger.info(f"Image saved: {filename}")

        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")

# ------------------- Main Import Function -------------------
def import_products():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # scrap_abdisite/
    EDITED_FOLDER = os.path.join(BASE_DIR, "data/edited")
    pattern = re.compile(r"edited_(\d{8})_(\d{4})_\d+\.json$")
    list_of_files = [f for f in glob.glob(os.path.join(EDITED_FOLDER, "*.json")) if pattern.search(os.path.basename(f))]

    if not list_of_files:
        logger.error("هیچ فایل JSON ویرایش‌شده‌ای پیدا نشد.")
        return

    def file_key(f):
        match = pattern.search(os.path.basename(f))
        date_part = match.group(1)
        time_part = match.group(2)
        return date_part + time_part

    latest_file = max(list_of_files, key=file_key)
    logger.info(f"⏳ در حال پردازش فایل: {latest_file}")

    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Supplier
    supplier, _ = Supplier.objects.get_or_create(name="عمده فروش عبدی")

    # User flip
    User = get_user_model()
    flip_user = User.objects.get(username="flip")

    for idx, item in enumerate(data, start=1):
        name = item.get('name')
        price = Decimal(item.get('price', 0))
        product_link = item.get('product_link')
        category_slug = slugify(item.get('category', ''))

        category = None
        if category_slug:
            category, _ = Category.objects.get_or_create(
                slug=category_slug,
                defaults={'name': item.get('category', '')}
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

        # 🔹 ایجاد واریانت پیش‌فرض
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
                stock=item.get('quantity', 0)
            )

        # تگ‌ها
        for tag_name in item.get('tags', []):
            tag_slug = slugify(tag_name)
            tag, _ = Tag.objects.get_or_create(slug=tag_slug, defaults={'name': tag_name})
            product.tags.add(tag)

        # مشخصات
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

        # موجودی صفر اگر قیمت صفر
        if price == 0:
            for variant in product.variants.all():
                variant.stock = 0
                variant.save()

        # WatchedURL با user flip
        if product_link:
            WatchedURL.objects.update_or_create(
                user=flip_user,
                product=product,
                supplier=supplier,
                url=product_link,
                defaults={"price": price}
            )

        # تصاویر
        image_urls = item.get('images', [])
        if image_urls:
            download_and_attach_images(product, image_urls, main_index=0)

        logger.info(f"{idx}. محصول '{name}' پردازش شد.")

    logger.info("✅ همه محصولات با موفقیت پردازش شدند.")


if __name__ == "__main__":
    import_products()
