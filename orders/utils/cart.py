def items(self):
    items_list = []

    for item in self.cart.items.select_related("variant", "variant__product").prefetch_related("variant__images"):
        variant = item.variant
        product = variant.product

        # قیمت با تخفیف
        price = variant.get_price()

        # پیدا کردن تصویر مناسب
        image_url = None
        try:
            # 1️⃣ تصویر اصلی واریانت
            variant_main_image = variant.images.filter(is_main=True).first()
            if variant_main_image and variant_main_image.image:
                image_url = variant_main_image.image.url

            # 2️⃣ اگر نبود، تصویر اصلی محصول
            if not image_url:
                product_main_image = product.images.filter(is_main=True).first()
                if product_main_image and product_main_image.image:
                    image_url = product_main_image.image.url

            # 3️⃣ اگر هنوز هیچ تصویری نیست، اولین تصویر موجود
            if not image_url and product.images.exists():
                first_image = product.images.first()
                if first_image.image:
                    image_url = first_image.image.url
        except Exception:
            image_url = None

        items_list.append({
            "id": item.id,
            "variant": variant.id,
            "product_name": str(variant),  # شامل attributes
            "quantity": item.quantity,
            "price": price,
            "total_price": price * item.quantity,
            "image": self.request.build_absolute_uri(image_url) if image_url else None,
        })

    return items_list
