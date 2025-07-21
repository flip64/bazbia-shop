# products/templatetags/category_tags.py
from django import template

register = template.Library()

@register.inclusion_tag('products/category_tree.html')
def render_category_tree(categories):
    return {'categories': categories}
