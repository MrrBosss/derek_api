# Generated by Django 4.0.10 on 2024-08-16 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0080_product_price'),
    ]

    operations = [
        migrations.RenameField(
            model_name='productweight',
            old_name='value',
            new_name='mass',
        ),
        migrations.AlterField(
            model_name='brand',
            name='name',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
