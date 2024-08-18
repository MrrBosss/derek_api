# Generated by Django 4.0.10 on 2024-08-18 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0084_alter_productweight_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productweight',
            name='price',
        ),
        migrations.RemoveField(
            model_name='productweight',
            name='value',
        ),
        migrations.AddField(
            model_name='product',
            name='characters',
            field=models.CharField(blank=True, help_text='Add 2 or 3 characters to describe the product', max_length=3, null=True),
        ),
        migrations.AddField(
            model_name='productweight',
            name='mass',
            field=models.FloatField(default=0),
        ),
    ]
