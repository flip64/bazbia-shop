import json
from decimal import Decimal
from django.utils.text import slugify
from products.models import Product, Category, Tag , ProductSpecification
from scrap_abdisite.models import  WatchedURL
from suppliers.models import  Supplier

def import_products_from_json(file, user):
    data = json.load(file)
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
                'base_price': price * Decimal("1.2"),
                'category': category,
                'description': item.get('description', ''),
                'is_active': True,
            }
        )

        # تگ‌ها
        for tag_name in item.get('tags', []):
            tag_slug = slugify(tag_name)
            tag, _ = Tag.objects.get_or_create(slug=tag_slug, defaults={'name': tag_name})
            product.tags.add(tag)



        # مدیریت ویژگی‌های محصول (ProductSpecification)
        if 'specifications' in item:
            existing_specs = {(spec.name, spec.value) for spec in product.specifications.all()}
            
            for spec in item['specifications']:
                if ':' in spec:
                    spec_name, spec_value = [part.strip() for part in spec.split(':', 1)]
                    
                    # فقط اگر این ویژگی وجود نداشت اضافه می‌کنیم
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
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug
