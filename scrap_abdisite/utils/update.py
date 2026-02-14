#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta

# ================= Django setup =================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bazbia_shop.settings")

import django
django.setup()

from django.db import transaction, close_old_connections
from django.db.utils import OperationalError
from django.db.models import Q

from scrap_abdisite.models import WatchedURL, PriceHistory
from products.models import ProductVariant   # اگر مسیر فرق دارد اصلاح کن
from scrap_abdisite.utils.abdi_fetcher import fetch_product_details, extract_quantity

# ================= Logging =================
LOG_DIR = os.path.join(BASE_DIR, "scrap_abdisite", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = os.path.join(LOG_DIR, f"sync_abdi_{RUN_ID}.log")
DATA_FILE = os.path.join(LOG_DIR, f"scrape_results_{RUN_ID}.json")

logger = logging.getLogger("sync_abdi")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
fh.setFormatter(formatter)

sh = logging.StreamHandler()
sh.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(sh)

logger.propagate = False

# ================= Helpers =================
def calc_sale_price(purchase_price, profit_percent):
    return (
        purchase_price
        * (Decimal("1") + Decimal(profit_percent) / Decimal("100"))
    ).quantize(Decimal("100"), rounding=ROUND_HALF_UP)

# ================= Phase 1: Scraping =================
def phase1_scrape():
    logger.info("🚀 Phase 1 started: Load DB → Scrape → JSON")

    threshold = datetime.now() - timedelta(hours=6)

    qs = list(
        WatchedURL.objects
        .select_related("variant")
        .filter(Q(last_checked__isnull=True) | Q(last_checked__lt=threshold))
        .values(
            "id",
            "url",
            "price",
            "variant__id",
            "variant__sku",
            "variant__purchase_price",
            "variant__price",
            "variant__profit_percent",
            "variant__stock",
        )
    )

    logger.info(f"📦 {len(qs)} items loaded from DB")

    close_old_connections()  # 🔥 قطع کامل کانکشن DB

    results = []

    for i, row in enumerate(qs, start=1):
        url = row["url"]
        sku = row["variant__sku"]

        try:
            name, price = fetch_product_details(url)
            stock = extract_quantity(url)

            if price is None:
                logger.warning(f"[{i}] ⚠️ No price | {sku}")
                continue

            result = {
                "watched_id": row["id"],
                "variant_id": row["variant__id"],
                "sku": sku,
                "old_price": str(row["price"]),
                "new_price": str(price),
                "old_stock": row["variant__stock"],
                "new_stock": int(stock or 0),
                "profit_percent": row["variant__profit_percent"],
                "checked_at": datetime.now().isoformat()
            }

            results.append(result)
            logger.info(f"[{i}] ✅ Scraped {sku}")

        except Exception as e:
            logger.error(f"[{i}] ❌ Scrape failed {sku}: {e}", exc_info=True)

        time.sleep(2)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    logger.info(f"💾 Phase 1 finished → {DATA_FILE}")

# ================= Phase 2: Sync DB =================
def phase2_sync():
    logger.info("🚀 Phase 2 started: JSON → DB")

    if not os.path.exists(DATA_FILE):
        logger.error("❌ Data file not found, aborting")
        return

    with open(DATA_FILE, encoding="utf-8") as f:
        rows = json.load(f)

    watched_updates = []
    variant_updates = []
    price_histories = []

    for r in rows:
        old_price = Decimal(r["old_price"]) if r["old_price"] else None
        new_price = Decimal(r["new_price"])

        # WatchedURL
        watched = WatchedURL(
            id=r["watched_id"],
            price=new_price,
            last_checked=datetime.fromisoformat(r["checked_at"])
        )

        if old_price != new_price:
            price_histories.append(
                PriceHistory(
                    watched_url_id=r["watched_id"],
                    price=new_price
                )
            )

        watched_updates.append(watched)

        # Variant
        new_sale = calc_sale_price(new_price, Decimal(r["profit_percent"]))
        variant = Variant(
            id=r["variant_id"],
            purchase_price=new_price,
            price=new_sale,
            stock=r["new_stock"]
        )
        variant_updates.append(variant)

    try:
        with transaction.atomic():
            WatchedURL.objects.bulk_update(
                watched_updates,
                ["price", "last_checked"]
            )

            Variant.objects.bulk_update(
                variant_updates,
                ["purchase_price", "price", "stock"]
            )

            if price_histories:
                PriceHistory.objects.bulk_create(price_histories)

        logger.info(
            f"✅ Phase 2 finished | watched={len(watched_updates)} "
            f"variants={len(variant_updates)} history={len(price_histories)}"
        )

    except OperationalError as e:
        logger.critical("💥 DB error during Phase 2", exc_info=True)
        sys.exit(1)

# ================= Main =================
if __name__ == "__main__":
    logger.info("🔥 Sync job started")

    phase1_scrape()
    phase2_sync()

    logger.info("🏁 Sync job finished successfully")