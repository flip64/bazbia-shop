# products/sitemaps.py

from django.conf import settings
from django.contrib.sitemaps import Sitemap

from products.models import Product, Category


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return (
            Product.objects
            .filter(is_active=True)
            .only("id", "slug", "updated_at")
            .order_by("id")
        )

    def location(self, obj):
        return (
            f"{settings.STOREFRONT_BASE_URL}"
            f"/product/{obj.slug}"
        )

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return (
            Category.objects
            .only("id", "slug")
            .order_by("id")
        )

    def location(self, obj):
        return (
            f"{settings.STOREFRONT_BASE_URL}"
            f"/products?category={obj.slug}"
        )
