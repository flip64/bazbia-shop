"""Conservative editorial grouping; never rewrite annual stories or sale identities."""
from collections import defaultdict
from django.db import migrations


def populate(apps, schema_editor):
    Coin = apps.get_model('coins', 'CoinType')
    Group = apps.get_model('coins', 'CoinGroup')
    Image = apps.get_model('coins', 'CoinCatalogImage')
    db = schema_editor.connection.alias
    buckets = defaultdict(list)
    fields = ('name', 'issuer_id', 'calendar', 'period_id', 'ruler_id', 'currency_id',
              'face_value', 'denomination_label', 'series_name', 'construction', 'shape',
              'issue_kind', 'obverse_description', 'reverse_description', 'obverse_inscription',
              'reverse_inscription', 'weight_g', 'diameter_mm', 'thickness_mm', 'edge_type')
    for coin in Coin.objects.using(db).filter(group__isnull=True).order_by('pk'):
        buckets[tuple(getattr(coin, key) for key in fields)].append(coin)
    for members in buckets.values():
        first = members[0]
        values = {'name': first.name, 'issuer_id': first.issuer_id,
                  'slug': 'coin-group-' + str(first.pk)}
        for field in ('introduction', 'story', 'story_sources'):
            texts = {getattr(c, field) for c in members if getattr(c, field).strip()}
            values[field] = next(iter(texts)) if len(texts) == 1 else ''
        for side in ('obverse', 'reverse'):
            image = Image.objects.using(db).filter(coin_type_id__in=[c.pk for c in members], view_type=side).order_by('pk').first()
            if image:
                values[side] = image.image
                values[side + '_url'] = image.source_url or ''
        group = Group.objects.using(db).create(**values)
        Coin.objects.using(db).filter(pk__in=[c.pk for c in members]).update(group_id=group.pk)
        # Preserve conflicting stories as annual content; identical copies stay archived
        # in the original story field and are no longer shown twice after group edits.
        if not values['story']:
            for coin in members:
                if coin.story:
                    Coin.objects.using(db).filter(pk=coin.pk).update(year_story=coin.story)


class Migration(migrations.Migration):
    dependencies = [('coins', '0006_coingroup_cointype_group')]
    operations = [migrations.RunPython(populate, migrations.RunPython.noop)]
