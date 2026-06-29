
# -*- coding: utf-8 -*-
import requests
import xml.etree.ElementTree as ET
import json
import os

BASE_URL = "https://pakhshabdi.com/sitemap_index.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

OUTPUT_FILE = "product_list.json"

NAMESPACE = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9"
}


def get_product_sitemaps():
    """دریافت لیست تمام Product Sitemap ها"""

    response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    response.raise_for_status()

    root = ET.fromstring(response.content)

    sitemaps = []

    for sitemap in root.findall("sm:sitemap", NAMESPACE):

        loc = sitemap.find("sm:loc", NAMESPACE)

        if loc is not None and "product-sitemap" in loc.text:
            sitemaps.append(loc.text)

    return sitemaps


def read_product_sitemap(url):
    """خواندن یک Product Sitemap"""

    print("Reading:" ,url)

    products = []

    try:

        response = requests.get(url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            print("Skip ("+ response.status_code +")")
            return products

        root = ET.fromstring(response.content)

        for item in root.findall("sm:url", NAMESPACE):

            loc = item.find("sm:loc", NAMESPACE)
            lastmod = item.find("sm:lastmod", NAMESPACE)

            if loc is None:
                continue

            product_url = loc.text.strip()

            slug = product_url.rstrip("/").split("/")[-1]

            products.append({
                "slug": slug,
                "url": product_url,
                "lastmod": lastmod.text if lastmod is not None else None
            })

    except Exception as e:
        print(e)

    return products


def main():

    all_products = []

    sitemaps = get_product_sitemaps()

    print("Found", len(sitemaps)," product sitemaps")

    for sitemap in sitemaps:

        products = read_product_sitemap(sitemap)

        print( len(products)," products")

        all_products.extend(products)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    print("-" * 50)
    print("Total:", len(all_products))
    print("Saved:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
