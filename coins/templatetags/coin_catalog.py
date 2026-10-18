from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def catalog_query(context, **changes):
    allowed = {
        "q",
        "issuer",
        "period",
        "currency",
        "material",
        "kind",
        "shape",
        "calendar",
        "year",
        "ordering",
        "view",
        "page",
    }
    query = context["request"].GET.copy()
    for key in list(query):
        if key not in allowed:
            query.pop(key)
    for key, value in changes.items():
        if value is None or value == "":
            query.pop(key, None)
        else:
            query[key] = str(value)
    return "?" + query.urlencode()


@register.filter
def catalog_value(value):
    return "—" if value is None or value == "" else value
