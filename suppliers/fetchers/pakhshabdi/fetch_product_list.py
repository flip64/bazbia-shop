# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import json
import re
import requests
import xml.etree.ElementTree as ET
from multiprocessing.dummy import Pool as ThreadPool

BASE_URL = "https://pakhshabdi.com/sitemap_index.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

NAMESPACE = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9"
}

session = requests.Session()
session.headers.update(HEADERS)


def check_product(url):
    try:
        r = session.get(url, timeout=20)

        if r.status_code != 200:
            return None

        html = r.text

        name = re.search(
            r'<h1[^>]*class="[^"]*product_title[^"]*"[^>]*>(.*?)</h1>',
            html,
            re.I | re.S
        )

        stock = re.search(
            r'class="stock\s+in-stock"[^>]*>\s*(\d+)',
            html,
            re.I
        )

        if not stock:
            return None

        price = re.search(
            r'property="product:price:amount"\s+content="(\d+)"',
            html,
            re.I
        )

        return {
            "name": re.sub(r"<.*?>", "", name.group(1)).strip() if name else "",
            "price": int(price.group(1)) if price else 0,
            "stock": int(stock.group(1)),
            "url": url
        }

    except:
        return None


def get_product_sitemaps():

    r = session.get(BASE_URL, timeout=20)
    root = ET.fromstring(r.content)

    sitemaps = []

    for item in root.findall("sm:sitemap", NAMESPACE):

        loc = item.find("sm:loc", NAMESPACE)

        if loc is not None and "product" in loc.text.lower():
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
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    output_file = os.path.join(DATA_DIR, "available_products.json")

    with open(output_file, "w") as f:
        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("Found {} available products.".format(len(results)))
    print("Saved:", output_file)


if __name__ == "__main__":
    main()
