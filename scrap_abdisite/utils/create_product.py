import os
import glob
import re
import json
from decimal import Decimal
from django.utils.text import slugify
from products.models import Product, Category, Tag, ProductSpecification
from scrap_abdisite.models import WatchedURL
from suppliers.models import Supplier

def import_products_from_json(user):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # scrap_abdisite/
    EDITED_FOLDER = os.path.join(BASE_DIR, "data/edited")

    # پیدا کردن همه فایل‌های واقعی JSON ویرایش شده
    pattern = re.compile(r"edited_(\d{8})_(\d{4})_\d+\.json$")
    list_of_files = [
        f for f in glob.glob(os.path.join(EDITED_FOLDER, "*.json"))
        if pattern.search(os.path.basename(f))
    ]

    if not list_of_files:
        raise FileNotFoundError("هیچ فایل JSON ویرایش‌شده‌ای پیدا نشد.")

    # انتخاب آخرین فایل بر اساس تاریخ و زمان در نام
    def file_key(f):
        match = pattern.search(os.path.basename(f))
        date_part = match.group(1)  # YYYYMMDD
        time_part = match.group(2)  # HHMM
        return date_part + time_part

    latest_file = max(list_of_files, key=file_key)

    # باز کردن و خواندن فایل
    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    supplier, _ = Supplier.objects.get_or_create(name="عمده فروش عبدی")

    for item in data:
        name = item.get('name')
        price = Decimal(item.get('price', 0))
        product_link = item.get('product_link')
        category_slug = slugify(item.get('category', ''))

        # دسته‌بندی
        category = None
        if category_slug:
            category, _ = Category.objects.get_or_create(
                slug=category_slug,
                defaults={'name': item['category']}
            )

        # محصول را ایجاد یا بروزرسانی کن
        product, created = Product.objects.update_or_create(
            name=name,
            defaults={
                'slug': generate_unique_slug(name),
                'base_price': price * Decimal("1.2") if price > 0 else Decimal("0"),  # قیمت سایت بالاتر
                'category': category,
                'description': item.get('description', ''),
                'is_active': True,
                'stock': 0 if price == 0 else 1  # موجودی صفر اگر قیمت صفر، در غیر این صورت حداقل 1
            }
        )

        # تگ‌ها
        for tag_name in item.get('tags', []):
            tag_slug = slugify(tag_name)
            tag, _ = Tag.objects.get_or_create(slug=tag_slug, defaults={'name': tag_name})
            product.tags.add(tag)

        # ویژگی‌های محصول (ProductSpecification)
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

        # WatchedURL
        WatchedURL.objects.update_or_create(
            user=user,
            product=product,
            supplier=supplier,
            url=product_link,
            defaults={'price': price}
        )


def generate_unique_slug(name):
    from products.models import Product
    from django.utils.text import slugify

    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug
