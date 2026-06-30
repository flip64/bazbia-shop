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
        print("URL:", url)
        print("Status:", r.status_code)
        print("Length:", len(r.text))
        print("Has product_title:", "product_title" in r.text)
        print("Has InStock:", "InStock" in r.text)
        print("Has stock in-stock:", "stock in-stock" in r.text)

        return {
            "name": re.sub(r"<.*?>", "", name.group(1)).strip() if name else "",
            "price": int(price.group(1)) if price else 0,
            "stock": int(stock.group(1)),
            "url": url
        }

    except:
        return None
      
