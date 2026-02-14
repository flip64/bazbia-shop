#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta

# ================= Django setup =================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazbia_shop.settings")

import django
django.setup()

from django.db import transaction, connection
from django.db.utils import OperationalError
from django.db.models import Q
from scrap_abdisite.models import WatchedURL, PriceHistory
from scrap_abdisite.utils.abdi_fetcher import fetch_product_details, extract_quantity

# ================= Logging =================
LOG_DIR = os.path.join(BASE_DIR, "scrap_abdisite", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"sync_abdi_{datetime.now():%Y%m%d_%H%M%S}.log")

# logger مخصوص فایل (فقط تغییرات)
file_logger = logging.getLogger("sync_abdi_file")
file_logger.setLevel(logging.INFO)

# logger مخصوص کنسول
console_logger = logging.getLogger("sync_abdi_console")
console_logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

file_logger.addHandler(file_handler)
console_logger.addHandler(console_handler)

file_logger.propagate = False
console_logger.propagate = False

# ================= Helpers =================
def calc_sale_price(purchase_price, profit_percent):
    return (
        purchase_price
        * (Decimal("1") + Decimal(profit_percent) / Decimal("100"))
    ).quantize(Decimal("100"), rounding=ROUND_HALF_UP)

def stop_program_on_db_disconnect(e):
    file_logger.critical("💥 Database connection lost. Program stopped.", exc_info=True)
    try:
        connection.close()
    except Exception:
        pass
    sys.exit(1)

# ================= Core =================
def sync_watched(watched: WatchedURL, dry_run=False):
    url = watched.url
    variant = watched.variant

    console_logger.info(f"🔄 Sync: {variant.sku}")

    try:
        name, price = fetch_product_details(url)
        stock = extract_quantity(url)

        if price is None:
            console_logger.warning(f"⚠️ No price: {url}")
            return

        price = Decimal(price)
        stock = int(stock or 0)

        changes = []

        # ---------- WatchedURL price ----------
        if watched.price != price:
            changes.append(f"💰 WatchedURL price {watched.price} → {price}")
            if not dry_run:
                PriceHistory.objects.create(
                    watched_url=watched,
                    price=price
                )
                watched.price = price

        # ---------- Variant price ----------
        if variant.purchase_price != price:
            old_sale = variant.price
            new_sale = calc_sale_price(price, variant.profit_percent)
            changes.append(f"🧾 Variant price {old_sale} → {new_sale}")
            if not dry_run:
                variant.purchase_price = price
                variant.price = new_sale

        # ---------- Stock ----------
        if variant.stock != stock:
            changes.append(f"📦 Stock {variant.stock} → {stock}")
            if not dry_run:
                variant.stock = stock

        # ---------- Save ----------
        if not dry_run:
            with transaction.atomic():
                watched.save()  # last_checked همیشه آپدیت می‌شود
                if changes:
                    variant.save()

        # ---------- Output ----------
        if changes:
            file_logger.info(f"{variant.sku} | " + " | ".join(changes))
        else:
            console_logger.info(f"⚡ No changes: {variant.sku}")

    except OperationalError as e:
        if "2006" in str(e) or "2013" in str(e):
            stop_program_on_db_disconnect(e)
        raise

    except Exception as e:
        console_logger.error(f"❌ Error syncing {url}: {e}", exc_info=True)

# ================= Runner =================
def run(dry_run=False):
    now = datetime.now()
    threshold = now - timedelta(hours=6)

    qs = WatchedURL.objects.select_related("variant").filter(
        Q(last_checked__isnull=True) |
        Q(last_checked__lt=threshold)
    )

    console_logger.info(
        f"🚀 Start syncing {qs.count()} items (eligible only) (dry_run={dry_run})"
    )

    for watched in qs:
        sync_watched(watched, dry_run=dry_run)
        time.sleep(2)

    console_logger.info("✅ Sync finished")

# ================= Main =================
if __name__ == "__main__":
    run(dry_run=False)