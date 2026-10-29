from collections import OrderedDict
from django.db import migrations, models


def separate_years(apps, schema_editor):
    """Keep issue/variant/order identities; split only their catalog parents."""
    Coin = apps.get_model("coins", "CoinType")
    Issue = apps.get_model("coins", "CoinIssue")
    Image = apps.get_model("coins", "CoinCatalogImage")
    Composition = apps.get_model("coins", "CoinCompositionPart")
    Reference = apps.get_model("coins", "CoinCatalogReference")
    db = schema_editor.connection.alias

    def copy_fields(obj, **overrides):
        values = {field.attname: getattr(obj, field.attname)
                  for field in obj._meta.concrete_fields
                  if not field.primary_key and field.name not in ("created_at", "updated_at")}
        values.update(overrides)
        return values

    # Materialize original IDs so newly cloned rows are not visited again.
    for coin_id in list(Coin.objects.using(db).values_list("pk", flat=True)):
        coin = Coin.objects.using(db).get(pk=coin_id)
        issues = list(Issue.objects.using(db).filter(coin_type_id=coin_id).order_by("pk"))
        groups = OrderedDict()
        for issue in issues:
            groups.setdefault((issue.calendar, issue.year, issue.date_status), []).append(issue.pk)
        if not groups:
            # Older entries may have a single-year range without an issue yet.
            if coin.year_start is not None and coin.year_start == coin.year_end:
                Coin.objects.using(db).filter(pk=coin_id).update(mint_year=coin.year_start)
                Issue.objects.using(db).create(coin_type_id=coin_id, year=coin.year_start,
                                               calendar=coin.calendar, date_status="known")
            continue
        shared_images = list(Image.objects.using(db).filter(coin_type_id=coin_id, issue__isnull=True))
        compositions = list(Composition.objects.using(db).filter(coin_type_id=coin_id))
        references = list(Reference.objects.using(db).filter(coin_type_id=coin_id))
        themes = list(coin.themes.using(db).values_list("pk", flat=True))
        for index, ((calendar, year, status), issue_ids) in enumerate(groups.items()):
            if index == 0:
                target = coin
                Coin.objects.using(db).filter(pk=coin_id).update(mint_year=year, calendar=calendar)
            else:
                # Original slug continues to identify the first year's record.
                suffix = f"-year-{issue_ids[0]}"
                slug = coin.slug[:180 - len(suffix)] + suffix
                counter = 1
                while Coin.objects.using(db).filter(slug=slug).exists():
                    suffix = f"-year-{issue_ids[0]}-{counter}"
                    slug = coin.slug[:180 - len(suffix)] + suffix
                    counter += 1
                target = Coin.objects.using(db).create(**copy_fields(coin, slug=slug, mint_year=year, calendar=calendar))
                target.themes.set(themes)
                for obj in compositions:
                    Composition.objects.using(db).create(**copy_fields(obj, coin_type_id=target.pk))
                for obj in references:
                    Reference.objects.using(db).create(**copy_fields(obj, coin_type_id=target.pk))
                for obj in shared_images:
                    # Independent image rows preserve existing files without copying bytes.
                    Image.objects.using(db).create(**copy_fields(obj, coin_type_id=target.pk))
            Issue.objects.using(db).filter(pk__in=issue_ids).update(coin_type_id=target.pk)
            Image.objects.using(db).filter(issue_id__in=issue_ids).update(coin_type_id=target.pk)


class Migration(migrations.Migration):
    dependencies = [("coins", "0004_coinspecimen_catalog_link")]
    operations = [
        migrations.AddField(model_name="cointype", name="mint_year",
                            field=models.IntegerField("سال ضرب", null=True, blank=True, db_index=True)),
        migrations.RunPython(separate_years, migrations.RunPython.noop),
    ]
