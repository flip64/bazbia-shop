import requests
import json
import time

BASE_URL = "https://api.digikala.com/v1/categories"

def fetch_category(slug=None):
    if slug:
        url = f"{BASE_URL}/{slug}/"
    else:
        url = f"{BASE_URL}/"
    print(f"Fetching {url}")
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def build_tree(slug=None):
    data = fetch_category(slug)
    tree = {
        "id": data.get("id"),
        "name": data.get("title"),
        "slug": data.get("slug"),
        "children": []
    }
    for child in data.get("children", []):
        child_slug = child.get("slug")
        time.sleep(0.3)  # کمی تاخیر برای پرهیز از بن شدن
        tree["children"].append(build_tree(child_slug))
    return tree

if __name__ == "__main__":
    print("Building Digikala category tree...")
    category_tree = build_tree()
    with open("digikala_categories.json", "w", encoding="utf-8") as f:
        json.dump(category_tree, f, ensure_ascii=False, indent=2)
    print("✅ Saved to digikala_categories.json")
