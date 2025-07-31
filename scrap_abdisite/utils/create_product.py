import json
from decimal import Decimal
from django.utils.text import slugify
from products.models import Product, Category, Tag
from scrap_abdisite.models import  WatchedURL
from suppliers.models import  Supplier

def import_products_from_json(file, user):
    data = json.load(file)

    # تأمین‌کننده پخش عبدی را پیدا یا ایجاد کن
    supplier, _ = Supplier.objects.get_or_create(name="عمده فروش عبدی")

    for item in data:
        name = item.get('name')
        price = Decimal(item.get('price', 0))
        product_link = item.get('product_link')
        category_slug = slugify(item.get('category', ''))

        # دسته‌بندی رو پیدا یا ایجاد کن
        category = None
        if category_slug:
            category, _ = Category.objects.get_or_create(
                slug=category_slug,
                defaults={'name': item['category']}
            )

        # محصول را ایجاد یا بروزرسانی کن
        # بررسی کن آیا محصولی با همین نام وجود دارد
        product = Product.objects.filter(name=name).first()

        # اگر وجود نداشت، محصول جدید بساز
        if not product:
         product = Product.objects.create(
          name=name,
          slug=slugify(name),
          base_price=price * Decimal("1.2"),  # قیمت با ۲۰٪ سود
          category=category,
          description=item.get('description', ''),
          is_active=True,
      )
    

        # تگ‌ها رو اضافه کن (در صورت نیاز)
        for tag_name in item.get('tags', []):
            tag_slug = slugify(tag_name)
            tag, _ = Tag.objects.get_or_create(slug=tag_slug, defaults={'name': tag_name})
            product.tags.add(tag)

        # لینک WatchedURL برای کاربر بساز
        
        WatchedURL.objects.get_or_create(
            user=user,
            product=product,
            supplier=supplier,
            url=product_link,
            defaults={'price': price}
        )


