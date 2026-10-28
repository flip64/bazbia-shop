from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("coins", "0003_coinissue_description_cointype_introduction_and_more")]
    operations = [migrations.AddField(model_name="coinspecimen", name="catalog_link", field=models.BooleanField(default=False, editable=False))]
