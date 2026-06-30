# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils import check_product

url = raw_input("Product URL: ").strip()

result = check_product(url)

print("=" * 50)

if result:
    print("SUCCESS")
    print(result)
else:
    print("FAILED (None returned)")
