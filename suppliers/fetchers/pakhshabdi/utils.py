# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import requests
import traceback

try:
    unicode
except NameError:
    unicode = str




HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(HEADERS)


def check_product(url):
    try:
        r = session.get(url, timeout=20)

        if r.status_code != 200:
            print("Status code:", r.status_code)
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

        if name:
            product_name = re.sub(r"<.*?>", "", name.group(1)).strip()
            if not isinstance(product_name, unicode):
                product_name = product_name.decode("utf-8", "ignore")
        else:
            product_name = u""

        product = {
            "name": product_name,
            "price": int(price.group(1)) //10 if price else 0,
            "stock": int(stock.group(1)),
            "url": url
        }

        print("SUCCESS:", product["name"])

        return product

    except Exception:
        print("=" * 80)
        print("ERROR:", url)
        traceback.print_exc()
        return None
