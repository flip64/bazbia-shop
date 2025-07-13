import requests

from bs4 import BeautifulSoup

import pandas as pd

import time



products = []

page = 1



while True:

 url = f"https://pakhshabdi.com/product-category/home-goods/page/{page}/"

 print(f"در حال پردازش صفحه {page} ...")


 headers = {"User-Agent": "Mozilla/5.0"}

 response = requests.get(url, headers=headers)


 if response.status_code != 200:
  print("صفحه‌ای پیدا نشد، عملیات پایان یافت.")
  break


 soup = BeautifulSoup(response.content, "html.parser")
 items = soup.find_all("li", class_="col-md-3 col-6 mini-product-con type-product")
 

 if not items:
  print("محصولی در این صفحه یافت نشد، تمام شد.")
  break

 for item in items:
    # نام محصول
    name_tag = item.find("h2", class_="product-title")
    name_link_tag = name_tag.find("a") if name_tag else None
    name = name_link_tag.text.strip() if name_link_tag else "نام یافت نشد"

    # لینک محصول
    link = name_link_tag["href"] if name_link_tag and name_link_tag.has_attr("href") else "لینک یافت نشد"

    # قیمت
    price_tag = item.find("span", class_="woocommerce-Price-amount")
    price = price_tag.text.strip() if price_tag else "قیمت یافت نشد"

    # لینک عکس
    img_div = item.find("div", class_="img-con")
    img_tag = img_div.find("img") if img_div else None
    image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else "عکس یافت نشد"

    # درج نتایج
    products.append({
     "name": name,
     "price": price,
     "image_link": image_url,
     "product_link": link
        })
  
 page += 1
 time.sleep(1)
 if page > 1:
  break



# ذخیره در اکسل
df = pd.DataFrame(products)
df.to_excel("bazbia_pakhshabdi_home_goods.xlsx", index=False)
print("✅ فایل bazbia_pakhshabdi_home_goods.xlsx ذخیره شد.")



