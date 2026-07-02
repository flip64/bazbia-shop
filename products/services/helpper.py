from django.utils.text import slugify

from products.models import Product


def create_slug(name):
    slug = slugify(name)

    if not slug:
        slug = "product"

    original_slug = slug
    counter = 2

    while Product.objects.filter(slug=slug).exists():
        slug = f"{original_slug}-{counter}"
        counter += 1

    return slug
