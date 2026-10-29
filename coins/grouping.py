"""Shared public identities without merging inventory, variants, or order records."""
from django.db.models import Q, Min
from . import models as m


def group_images(group, request=None):
    images = []
    for index, side in enumerate(('obverse', 'reverse')):
        file = getattr(group, side)
        url = file.url if file else getattr(group, side + '_url')
        if not url:
            continue
        if request:
            url = request.build_absolute_uri(url)
        images.append({'id': -(group.pk * 2 + index), 'url': url,
            'alt_text': group.name, 'is_main': not images, 'view_type': side,
            'caption': 'تصویر مرجع گروه', 'pack_item_id': None})
    return images


def collapse_products(queryset):
    """Deduplicate inside the filtered set, before pagination; ordinary products survive."""
    links = m.CoinSpecimen.objects.filter(
        variant__product_id__in=queryset.order_by().values('pk'),
        issue__coin_type__group_id__isnull=False,
    ).filter(Q(issue__coin_type__is_published=True) | Q(is_published=True))
    representatives = links.order_by().values('issue__coin_type__group_id').annotate(
        representative=Min('variant__product_id')).values('representative')
    return queryset.filter(Q(pk__in=representatives) | ~Q(pk__in=links.values('variant__product_id')))
