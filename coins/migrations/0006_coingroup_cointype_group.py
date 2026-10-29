# Shared coin groups and independent annual descriptions.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coins', '0005_cointype_mint_year'),
    ]

    operations = [
        migrations.AddField(model_name="cointype", name="year_story", field=models.TextField("داستان یا توضیح اختصاصی این سال", blank=True)),
        migrations.CreateModel(
            name='CoinGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='زمان تغییر')),
                ('name', models.CharField(max_length=200, verbose_name='نام گروه سکه')),
                ('slug', models.SlugField(max_length=180, unique=True, verbose_name='نامک')),
                ('introduction', models.TextField(blank=True, verbose_name='معرفی مشترک')),
                ('story', models.TextField(blank=True, verbose_name='داستان مشترک')),
                ('story_sources', models.TextField(blank=True, verbose_name='منابع داستان')),
                ('obverse', models.ImageField(blank=True, upload_to='coins/groups/', verbose_name='عکس مرجع روی گروه')),
                ('reverse', models.ImageField(blank=True, upload_to='coins/groups/', verbose_name='عکس مرجع پشت گروه')),
                ('obverse_url', models.URLField(blank=True, max_length=1000, verbose_name='لینک عکس روی گروه')),
                ('reverse_url', models.URLField(blank=True, max_length=1000, verbose_name='لینک عکس پشت گروه')),
                ('issuer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='coins.coinissuer', verbose_name='کشور')),
            ],
            options={
                'verbose_name': 'گروه سکه',
                'verbose_name_plural': 'گروه\u200cهای سکه',
                'ordering': ['name', 'pk'],
            },
        ),
        migrations.AddField(
            model_name='cointype',
            name='group',
            field=models.ForeignKey(blank=True, help_text='داستان و عکس عمومی از گروه خوانده می\u200cشود؛ عکس\u200cها و فروش این سال مستقل است.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='coins', to='coins.coingroup', verbose_name='گروه سکه'),
        ),
    ]
