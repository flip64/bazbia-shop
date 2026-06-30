# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils import check_product

url = "https://pakhshabdi.com/product/%da%86%d8%b3%d8%a8-%d8%a2%d9%84%d9%88%d9%85%db%8c%d9%86%db%8c%d9%88%d9%85%db%8c-%d8%af%d9%88%d8%b1-%da%af%d8%a7%d8%b2-5-%d8%b3%d8%a7%d9%86%d8%aa/"

result = check_product(url)

print("=" * 50)

if result:
    print("SUCCESS")
    print(result)
else:
    print("FAILED (None returned)")
