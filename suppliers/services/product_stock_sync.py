# products/services/product_stock_sync.py

from django.db.models import Sum

from products.models import Product


def sync_product_stock_from_variants(product: Product) -> bool:
    """
    موجودی محصول را از مجموع موجودی تمام واریانت‌های آن
    محاسبه و به‌روزرسانی می‌کند.
    """

    new_stock = (
        product.variants.aggregate(
            total_stock=Sum("stock")
        )["total_stock"]
        or 0
    )

    if product.quantity == new_stock:
        return False

    product.quantity = new_stock
    product.save(
        update_fields=[
            "quantity",
            "updated_at",
        ]
    )

    return True
