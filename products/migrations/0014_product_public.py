# Generated by Django 4.0.10 on 2024-06-10 11:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0013_rename_definition_product_content_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='public',
            field=models.BooleanField(default=True),
        ),
    ]
