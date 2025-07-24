from django.http import JsonResponse
from products.models import Category
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
import json



def list_categories(request):
    def build_tree(parent=None):
        categories = Category.objects.filter(parent=parent).values('id', 'name', 'slug')
        tree = []
        for cat in categories:
            children = build_tree(parent=cat['id'])
            item = {
                'id': cat['id'],
                'name': cat['name'],
                'slug': cat['slug'],
            }
            if children:
                item['children'] = children
            tree.append(item)
        return tree

    data = build_tree()
    return JsonResponse(data, safe=False)


@csrf_exempt
def import_categories(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST method allowed")

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    created = []

    def create_or_get_category(item, parent=None):
        slug = item['slug']
        name = item['name']

        category, is_created = Category.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'parent': parent}
        )

        # فقط اگر تازه ساخته شده اضافه کن به لیست
        if is_created:
            created.append(category.name)

        # بررسی children
        for child in item.get('children', []):
            create_or_get_category(child, parent=category)

    for cat_item in payload:
        create_or_get_category(cat_item)

    return JsonResponse({"status": "done","created": created})
