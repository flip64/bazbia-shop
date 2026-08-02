# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import json
import re
import requests
import xml.etree.ElementTree as ET
import logging


from logging.handlers import RotatingFileHandler
from multiprocessing.dummy import Pool as ThreadPool
from suppliers.fetchers.pakhshabdi.utils import check_product
BASE_URL = "https://pakhshabdi.com/sitemap_index.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

NAMESPACE = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9"
}

session = requests.Session()
session.headers.update(HEADERS)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))



logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    os.path.join(BASE_DIR, "fetch_product_list.log"),
    maxBytes=5 * 1024 * 1024,   # 5 MB
    backupCount=2             # نگهداری 5 فایل قدیمی
)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

handler.setFormatter(formatter)
logger.addHandler(handler)




def get_product_sitemaps():

    r = session.get(BASE_URL, timeout=20)
    root = ET.fromstring(r.content)

    sitemaps = []

    for item in root.findall("sm:sitemap", NAMESPACE):

        loc = item.find("sm:loc", NAMESPACE)

        if loc is not None and "product-sitemap" in loc.text.lower():
            sitemaps.append(loc.text.strip())

    return sitemaps


def get_all_urls():

    urls = []

    for sitemap in get_product_sitemaps():

        try:
            r = session.get(sitemap, timeout=20)
            root = ET.fromstring(r.content)

            for item in root.findall("sm:url", NAMESPACE):

                loc = item.find("sm:loc", NAMESPACE)

                if loc is not None:
                    urls.append(loc.text.strip())

        except:
            pass

    return urls


def main():

    urls = get_all_urls()

    results = []

    pool = ThreadPool(20)


    for product in pool.imap_unordered(check_product, urls):

        if product:
            results.append(product)

    pool.close()
    pool.join()

    results.sort(key=lambda x: x["name"])

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR , "data"  )

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    output_file = os.path.join(DATA_DIR, "available_products.json")

    with open(output_file, "wb") as f:
     f.write(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2
        ).encode("utf-8")
     )                           
    logger.info("Found %d available products.", len(results))
    logger.info("Saved: %s", output_file)

if __name__ == "__main__":
    main()
