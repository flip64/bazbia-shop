from .models import Banner

def banners_processor(request):
    """
    این فانکشن بنرها را از دیتابیس می‌گیرد و در همه قالب‌ها به صورت متغیر banners
    در دسترس قرار می‌دهد.
    """
    banners = Banner.objects.all().order_by('-created_at')
    return {'banners': banners}
