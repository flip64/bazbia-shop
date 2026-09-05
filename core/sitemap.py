# core/views/sitemap.py

from types import SimpleNamespace

from django.http import HttpResponse
from django.template.loader import render_to_string


def storefront_sitemap(request, sitemaps):
    site = SimpleNamespace(
        domain="bazbia.ir",
        name="Bazbia",
    )

    urls = []

    for sitemap_class in sitemaps.values():
        sitemap_obj = sitemap_class()

        urls.extend(
            sitemap_obj.get_urls(
                site=site,
                protocol="https",
            )
        )

    xml = render_to_string(
        "sitemap.xml",
        {
            "urlset": urls,
        },
    )

    return HttpResponse(
        xml,
        content_type="application/xml",
    )
