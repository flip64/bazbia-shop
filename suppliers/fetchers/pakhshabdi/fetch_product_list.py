import requests
import xml.etree.ElementTree as ET
import json
import re
ThreadPoolExecutor, as_completed
from product_checker import  check_product
BASE_URL = "https://pakhshabdi.com/sitemap_index.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

OUTPUT_FILE = "available_products.json"

NAMESPACE = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9"
}

session = requests.Session()
session.headers.update(HEADERS)



def check_product(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)

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
            "url":url
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


def extract_json_ld(html):

    m = re.search(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        re.DOTALL
    )

    if not m:
        return None

    text = m.group(1).strip()

    try:
        return json.loads(text)

    except:

        try:

            start = text.find("{")
            end = text.rfind("}") + 1

            return json.loads(text[start:end])

        except:
            return None



        
        
        
def main():

    urls = get_all_urls()

    results = []

    total = len(urls)
    done = 0
    found = 0

    print("-" * 60)
    print("Checking products...")
    print("-" * 60)

    # تعداد تردها را بسته به سرعت اینترنت می‌توان تغییر داد
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
                        f"[{found}] {product['name']} | "
                        f"{product['price']} {product['currency']}"
                    )

            except Exception:
                pass

            if done % 25 == 0 or done == total:
                print(
                    f"Checked: {done}/{total} | "
                    f"Available: {found}"
                )

    results.sort(key=lambda x: x["name"])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("\n" + "=" * 60)
    print("Finished")
    print(f"Available products : {len(results)}")
    print(f"Saved to           : {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
