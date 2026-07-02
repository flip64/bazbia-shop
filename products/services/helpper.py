from django.utils.text import slugify


from django.utils.text import slugify


def create_slug(name):
    """
    تولید اسلاگ محصول
    نسخه ساده - بعداً توسعه داده می‌شود.
    """
    return slugify(name)


