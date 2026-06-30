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
    response = session.get(BASE_URL, timeout=20)
    response.raise_for_status()

    root = ET.fromstring(response.content)

    sitemaps = []

    for sitemap in root.findall("sm:sitemap", NAMESPACE):

        loc = sitemap.find("sm:loc", NAMESPACE)

        if loc is not None and "product-sitemap" in loc.text:
            sitemaps.append(loc.text)

    return sitemaps


def get_all_urls():

    urls = []

    sitemaps = get_product_sitemaps()

    print(f"Found {len(sitemaps)} sitemaps")

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

    print(f"Total urls: {len(urls)}")

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
                        f"[{found}] "
                        f"{product['name']} | "
                        f"{product['price']} | "
                        f"Stock: {product['stock']}"
                    )

            except Exception:
                pass

            if done % 25 == 0 or done == total:
                print(
                    f"Checked: {done}/{total} | "
                    f"Available: {found}"
                )

    results.sort(key=lambda x: x["name"])

    # مسیر پوشه data (یک شاخه بالاتر)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")

    # اگر پوشه وجود نداشت، ساخته شود
    os.makedirs(DATA_DIR, exist_ok=True)

    # فایل خروجی
    output_file = os.path.join(DATA_DIR, "available_products.json")

    # ذخیره
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("\n" + "=" * 60)
    print("Finished")
    print(f"Available products : {len(results)}")
    print(f"Saved to           : {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
