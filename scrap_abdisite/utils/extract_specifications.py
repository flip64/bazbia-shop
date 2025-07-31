import requests
from bs4 import BeautifulSoup

def extract_specifications(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    feature_list = []

    # جستجو برای بخش "ویژگی های محصول"
    section_title = soup.find(text=lambda t: "ویژگی های محصول" in t)
    if section_title:
        ul = section_title.find_next("ul")
        if ul:
            for li in ul.find_all("li"):
                if ":" in li.text:
                    key, val = li.text.split(":", 1)
                    feature_list.append(f"{key.strip()}: {val.strip()}")

    return feature_list
