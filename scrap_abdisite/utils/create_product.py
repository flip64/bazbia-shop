def import_products_from_json(user):

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # scrap_abdisite/
    EDITED_FOLDER = os.path.join(BASE_DIR, "data/edited")
    pattern = re.compile(r"edited_(\d{8})_(\d{4})_\d+\.json$")
    list_of_files = [
        f for f in glob.glob(os.path.join(EDITED_FOLDER, "*.json"))
        if pattern.search(os.path.basename(f))
    ]

    if not list_of_files:
        raise FileNotFoundError("هیچ فایل JSON ویرایش‌شده‌ای پیدا نشد.")

    def file_key(f):
        match = pattern.search(os.path.basename(f))
        date_part = match.group(1)
        time_part = match.group(2)
        return date_part + time_part

    latest_file = max(list_of_files, key=file_key)

    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    supplier, _ = Supplier.objects.get_or_create(name="عمده فروش عبدی")

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

        # ===========================
        # 🔹 واریانت پیش‌فرض ایجاد کن
        # ===========================
        if not product.variants.exists():
            from products.models import ProductVariant
            ProductVariant.objects.create(
                product=product,
                sku=f"{product.slug}-default",
                price=product.base_price,
                stock=item.get('quantity', 0)  # موجودی از فایل JSON یا صفر
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

        # WatchedURL
        WatchedURL.objects.update_or_create(
            user=user,
            product=product,
            supplier=supplier,
            url=product_link,
            defaults={'price': price}
        )

        # تصاویر
        image_urls = item.get('images', [])
        if image_urls:
            download_and_attach_images(product, image_urls, main_index=0)
