# -*- coding: utf-8 -*-
import os
import logging
from decimal import Decimal
from django.db.models.signals import pre_save
from django.dispatch import receiver
from products.models import ProductVariant

# ------------------ پیکربندی لاگ ------------------
LOG_FILE = os.path.join(os.path.dirname(__file__), "price_update.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ------------------ WooCommerce API ------------------
try:
    from woocommerce import API
    wcapi = API(
        url="https://bazbia.ir",
        consumer_key=     "ck_803298f060530d6afe5f9beff0dd9bd097549ee7",
        consumer_secret=  "cs_cc2026350c028fe1b3a9204195ad963b37c4d265",
        version="wc/v3",
        timeout=20
    )
    logger.info("✅ اتصال اولیه به WooCommerce انجام شد.")
except Exception as e:
    logger.exception("❌ خطا در راه‌اندازی WooCommerce API: %s", e)


# ------------------ سیگنال تشخیص تغییر قیمت ------------------
@receiver(pre_save, sender=ProductVariant)
def detect_price_change(sender, instance, **kwargs):
    """
    بررسی تغییر قیمت و به‌روزرسانی در ووکامرس
    """
    if not instance.pk:
        # یعنی واریانت جدید است، قبلاً وجود نداشته
        logger.debug(f"⏩ واریانت جدید است ({instance}), سیگنال نادیده گرفته شد.")
        return

    try:
        old_instance = ProductVariant.objects.get(pk=instance.pk)
    except ProductVariant.DoesNotExist:
        logger.debug(f"⚠ واریانت {instance.pk} در دیتابیس یافت نشد.")
        return

    old_price = old_instance.price or Decimal("0.0")
    new_price = instance.price or Decimal("0.0")

    if old_price == new_price:
        return  # قیمت تغییری نکرده

    product_name = instance.product.name if instance.product else "نامشخص"
    logger.info(f"🔔 تغییر قیمت تشخیص داده شد برای '{product_name}': {old_price} → {new_price}")

    # ------------------ بروزرسانی ووکامرس ------------------
    try:
        response = wcapi.get("products", params={"search": product_name})
        logger.debug(f"📡 جستجو در ووکامرس برای '{product_name}'، پاسخ {response.status_code}")

        if response.status_code == 200:
            products = response.json()
            if products:
                product_id = products[0]["id"]
                logger.info(f"✅ محصول '{product_name}' یافت شد (ID={product_id})")

                update_data = {"regular_price": str(new_price)}
                update_response = wcapi.put(f"products/{product_id}", update_data)

                if update_response.status_code in [200, 201]:
                    logger.info(f"✅ قیمت '{product_name}' در ووکامرس بروزرسانی شد: {new_price}")
                else:
                    logger.error(f"❌ خطا در بروزرسانی قیمت '{product_name}': {update_response.text}")
            else:
                logger.warning(f"⚠ محصول '{product_name}' در ووکامرس پیدا نشد.")
        else:
            logger.error(f"❌ پاسخ نامعتبر از ووکامرس ({response.status_code}): {response.text}")

    except Exception as e:
        logger.exception(f"❌ خطا در اتصال یا بروزرسانی WooCommerce: {e}")

    # ------------------ ذخیره تاریخچه در دیتابیس ------------------
    try:
        from products.models import PriceChangeLog
        PriceChangeLog.objects.create(
            variant=instance,
            old_price=old_price,
            new_price=new_price
        )
        logger.info(f"📝 تاریخچه تغییر قیمت برای '{product_name}' ثبت شد.")
    except Exception as e:
        logger.exception(f"❌ خطا در ثبت PriceChangeLog برای '{product_name}': {e}")
