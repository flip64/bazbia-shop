# products/sitemaps.py

from django.contrib.sitemaps import Sitemap

from products.models import Product, Category


FRONTEND_URL = "https://bazbia.com"


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Product.objects.filter(
            is_active=True
        ).order_by("id")

    def location(self, obj):
        return f"{FRONTEND_URL}/product/{obj.slug}"

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Category.objects.all().order_by("id")

    def location(self, obj):
        return f"{FRONTEND_URL}/products?category={obj.slug}"
