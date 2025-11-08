# -*- coding: utf-8 -*-
import os
import logging
from decimal import Decimal
from django.db.models.signals import pre_save, post_save
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
        consumer_key="ck_803298f060530d6afe5f9beff0dd9bd097549ee7",
        consumer_secret="cs_cc2026350c028fe1b3a9204195ad963b37c4d265",
        version="wc/v3",
        timeout=20
    )
    logger.info("اتصال اولیه به WooCommerce انجام شد.")
except Exception as e:
    logger.exception("خطا در راه‌اندازی WooCommerce API: %s", e)


# ====================================================
# 1️⃣ pre_save: محاسبه خودکار قیمت فروش
# ====================================================
@receiver(pre_save, sender=ProductVariant)
def calculate_price(sender, instance, **kwargs):
    """
    محاسبه خودکار قیمت فروش بر اساس قیمت خرید و درصد سود
    """
    if instance.purchase_price is not None and instance.profit_percent is not None:
        calculated_price = instance.calculated_price
        if calculated_price is not None and instance.price != calculated_price:
            logger.debug(
                f"محاسبه قیمت فروش برای واریانت {instance.pk if instance.pk else 'جدید'}: "
                f"{instance.price} → {calculated_price}"
            )
            instance.price = calculated_price


# ====================================================
# 2️⃣ post_save: بروزرسانی WooCommerce بدون ثبت تاریخچه
# ====================================================
@receiver(post_save, sender=ProductVariant)
def update_woocommerce(sender, instance, created, **kwargs):
    """
    بروزرسانی قیمت واریانت در WooCommerce
    """
    try:
        product_name = instance.product.name if instance.product else "نامشخص"
        response = wcapi.get("products", params={"search": product_name})
        if response.status_code == 200 and response.json():
            product_id = response.json()[0]["id"]
            update_response = wcapi.put(f"products/{product_id}", {"regular_price": str(instance.price)})
            if update_response.status_code in [200, 201]:
                logger.info(f"قیمت '{product_name}' در ووکامرس بروزرسانی شد: {instance.price}")
            else:
                logger.error(f"خطا در بروزرسانی قیمت '{product_name}': {update_response.text}")
        else:
            logger.warning(f"محصول '{product_name}' در ووکامرس پیدا نشد.")
    except Exception as e:
        logger.exception(f"خطا در اتصال یا بروزرسانی WooCommerce: {e}")
