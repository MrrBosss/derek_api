# Generated by Django 4.2.16 on 2024-10-10 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0100_alter_productprice_artikul'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='color',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='weight',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
