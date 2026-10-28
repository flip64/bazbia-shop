from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("products", "0011_remove_product_quantity")]
    operations = [migrations.AddField(model_name="productvariant", name="is_sellable", field=models.BooleanField("قابل فروش", default=True, db_index=True))]
