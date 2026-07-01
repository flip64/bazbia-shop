import os
import sys

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../")
)
sys.path.insert(0, BASE_DIR)

print(BASE_DIR)


from extractor  import extract_product_data
url = "https://pakhshabdi.com/product/%da%86%d8%b3%d8%a8-%d8%a2%d9%84%d9%88%d9%85%db%8c%d9%86%db%8c%d9%88%d9%85%db%8c-%d8%af%d9%88%d8%b1-%da%af%d8%a7%d8%b2-5-%d8%b3%d8%a7%d9%86%d8%aa/"
product = extract_product_data(url)

print (product.name)
