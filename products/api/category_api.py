from django.http import JsonResponse
from products.models import Category

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
