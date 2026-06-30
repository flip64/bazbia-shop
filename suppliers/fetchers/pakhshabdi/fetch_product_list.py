# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import json
import re
import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

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
            return False

        html = r.text

        # نام محصول
        name = re.search(
            r'<h1[^>]*class="[^"]*product_title[^"]*"[^>]*>(.*?)</h1>',
            html,
            re.I | re.S
        )

        # موجودی
        stock = re.search(
            r'class="stock\s+in-stock"[^>]*>\s*(\d+)',
            html,
            re.I
        )

        if not stock:
            return False

        # قیمت
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

    except Exception:
        return False


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

    sitemaps = get_product_sitemaps()

    print("Found {} sitemaps".format(len(sitemaps)))

    for sitemap in sitemaps:

        print("Reading:", sitemap)

        try:

            r = session.get(sitemap, timeout=20)

            root = ET.fromstring(r.content)

            for item in root.findall("sm:url", NAMESPACE):

                loc = item.find("sm:loc", NAMESPACE)

                if loc is not None:
                    urls.append(loc.text.strip())

        except Exception as e:
            print(e)

    print("Total urls: {}".format(len(urls)))

    return urls


def main():

    urls = get_all_urls()

    results = []

    total = len(urls)
    done = 0
    found = 0

    print("-" * 60)
    print("Checking products...")
    print("-" * 60)

    with ThreadPoolExecutor(max_workers=20) as executor:

        futures = {
            executor.submit(check_product, url): url
            for url in urls
        }

        for future in as_completed(futures):

            done += 1

            try:

                product = future.result()

                if product:

                    found += 1
                    results.append(product)

                    print(
                        "[{}] {} | {} | Stock: {}".format(
                            found,
                            product["name"],
                            product["price"],
                            product["stock"]
                        )
                    )

            except Exception:
                pass

            if done % 25 == 0 or done == total:

                print(
                    "Checked: {}/{} | Available: {}".format(
                        done,
                        total,
                        found
                    )
                )

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

    print("\n" + "=" * 60)
    print("Finished")
    print("Available products :", len(results))
    print("Saved to           :", output_file)
    print("=" * 60)


if __name__ == "__main__":
    main()
