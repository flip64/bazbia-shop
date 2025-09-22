from .models import Banner
from products.models import Category

def banners_processor(request):
    """
    این فانکشن بنرها را از دیتابیس می‌گیرد و در همه قالب‌ها به صورت متغیر banners
    در دسترس قرار می‌دهد.
    """
    banners = Banner.objects.all().order_by('-created_at')
    return {'banners': banners}


def categories_processor(request):
    """
    این فانکشن دسته‌بندی‌ها را از دیتابیس می‌گیرد و در همه قالب‌ها به صورت متغیر category
    در دسترس قرار می‌دهد.
    """
    categories = Category.objects.filter(parent__isnull=True)
    return {'categories': categories}
