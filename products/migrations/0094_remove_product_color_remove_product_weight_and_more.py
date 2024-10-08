# Generated by Django 4.2.16 on 2024-10-03 04:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0093_alter_orderitem_weight'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='color',
        ),
        migrations.RemoveField(
            model_name='product',
            name='weight',
        ),
        migrations.RemoveField(
            model_name='product',
            name='price',
        ),
        migrations.CreateModel(
            name='ProductPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.FloatField(default=100)),
                ('color', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.productcolor')),
                ('weight', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.productweight')),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='price',
            field=models.ManyToManyField(to='products.productprice'),
        ),
    ]
