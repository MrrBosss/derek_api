# Generated by Django 4.0.10 on 2024-08-18 11:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0088_rename_name_product_ch_name_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='content',
            new_name='description',
        ),
        migrations.RenameField(
            model_name='product',
            old_name='content_en',
            new_name='description_en',
        ),
        migrations.RenameField(
            model_name='product',
            old_name='content_ru',
            new_name='description_ru',
        ),
    ]