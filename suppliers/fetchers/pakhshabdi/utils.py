# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(HEADERS)

def check_product(url):
    try:
        
        r = session.get(url, timeout=20)

        

        if r.status_code != 200:
            print("Status code is not 200")
            return None

        html = r.text

        
        name = re.search(
            r'<h1[^>]*class="[^"]*product_title[^"]*"[^>]*>(.*?)</h1>',
            html,
            re.I | re.S
        )

        print("Name regex:", bool(name))

        stock = re.search(
            r'class="stock\s+in-stock"[^>]*>\s*(\d+)',
            html,
            re.I
        )

        print("Stock regex:", bool(stock))

        if not stock:
            print("Stock not found")
            print(html[:1000])
            return None

        price = re.search(
            r'property="product:price:amount"\s+content="(\d+)"',
            html,
            re.I
        )

        print("Price regex:", bool(price))

        product = {
            "name": re.sub(r"<.*?>", "", name.group(1)).strip() if name else "",
            "price": int(price.group(1)) if price else 0,
            "stock": int(stock.group(1)),
            "url": url
        }

        print("SUCCESS:", product)

        return product

    except Exception as e:
        import traceback
        print("=" * 80)
        print("ERROR:", url)
        print(e)
        traceback.print_exc()
        return None
