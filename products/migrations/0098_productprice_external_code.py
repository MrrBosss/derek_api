# Generated by Django 4.2.16 on 2024-10-03 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0097_alter_product_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='productprice',
            name='external_code',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
