from types import SimpleNamespace

from django.contrib.sitemaps.views import sitemap


def storefront_sitemap(request, sitemaps):
    """
    Sitemap را روی دامنه اصلی فروشگاه تولید می‌کند،
    حتی اگر endpoint از backend.bazbia.ir سرو شود.
    """

    site = SimpleNamespace(
        domain="bazbia.ir",
        name="Bazbia",
    )

    return sitemap(
        request,
        sitemaps=sitemaps,
        site=site,
    )
