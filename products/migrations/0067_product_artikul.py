# Generated by Django 4.0.10 on 2024-07-10 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0066_rename_customer_name_order_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='artikul',
            field=models.CharField(default='1', max_length=20),
            preserve_default=False,
        ),
    ]