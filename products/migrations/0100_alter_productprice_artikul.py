# Generated by Django 4.2.16 on 2024-10-04 05:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0099_remove_product_artikul_productprice_artikul'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productprice',
            name='artikul',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='artikul'),
        ),
    ]
