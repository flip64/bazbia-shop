from django.http import JsonResponse
from products.models import Category

def list_categories(request):
    categories = Category.objects.all().values('id', 'name', 'slug')
    data = list(categories)  # تبدیل QuerySet به لیست ساده
    return JsonResponse(data, safe=False)
