import requests
from bs4 import BeautifulSoup

def extract_tags(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    tags = []

    # تگ‌ها معمولا در بخش "برچسب: ..." هستند و دارای rel="tag" هستند
    tag_links = soup.find_all("a", rel="tag")
    for tag in tag_links:
        text = tag.get_text(strip=True)
        if text:
            tags.append(text)

    return tags
