from django.db.models.signals import pre_save
from django.dispatch import receiver
from products.models import ProductVariant
from decimal import Decimal
from woocommerce import API
import os

# اتصال به ووکامرس
wcapi = API(
    url="https://bazbia.ir",
    consumer_key="ck_803298f060530d6afe5f9beff0dd9bd097549ee7",
    consumer_secret="cs_6278dfe82c44657a49ef30b65f6fcd7b47c7998b",
    version="wc/v3",
    timeout=15
)

@receiver(pre_save, sender=ProductVariant)
def detect_price_change(sender, instance, **kwargs):
    """
    وقتی قیمت واریانت تغییر کند، در ووکامرس هم آپدیت می‌شود.
    """
    if not instance.pk:
        return

    try:
        old_instance = ProductVariant.objects.get(pk=instance.pk)
    except ProductVariant.DoesNotExist:
        return

    old_price = old_instance.price
    new_price = instance.price

    if old_price != new_price:
        product_name = instance.product.name
        print(f"🔔 قیمت '{product_name}' تغییر کرد: {old_price} → {new_price}")

        # --- چک در ووکامرس ---
        try:
            response = wcapi.get("products", params={"search": product_name})
            if response.status_code == 200:
                products = response.json()
                if products:
                    product_id = products[0]["id"]
                    print(f"✅ محصول '{product_name}' در ووکامرس پیدا شد (ID={product_id})")

                    # آپدیت قیمت
                    update_data = {"regular_price": str(new_price)}
                    wcapi.put(f"products/{product_id}", update_data)
                    print(f"💰 قیمت '{product_name}' در ووکامرس بروز شد → {new_price}")
                else:
                    print(f"⚠️ محصول '{product_name}' در ووکامرس یافت نشد.")
            else:
                print("⚠️ خطا در دریافت اطلاعات از ووکامرس:", response.status_code)

        except Exception as e:
            print("❌ خطا در اتصال به ووکامرس:", e)

        # ذخیره در جدول تاریخچه (اختیاری)
        from products.models import PriceChangeLog
        PriceChangeLog.objects.create(
            variant=instance,
            old_price=old_price,
            new_price=new_price
        )
