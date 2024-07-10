import requests
from requests.auth import HTTPBasicAuth

from django.core.management.base import BaseCommand
from django.conf import settings
from products.models import Product, Category, ProductWeight

API_URL = "https://api.moysklad.ru/api/remap/1.2/entity/product"


def get_data(page):
    response = requests.get(
        url=API_URL + f"?limit=1000&offset={page * 1000}",
        auth=HTTPBasicAuth(settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD)
    )
    return response.json()


def parse_and_save_products(json_response):
    for item in json_response['rows']:
        product_name = item['name']
        product_code = item['code']
        product_price = item['salePrices'][0]['value'] / 100.0  # цена в копейках
        product_weight_value = item['weight']

        # Создание или получение категории
        category_name = item.get('pathName', 'Default Category')
        category, created = Category.objects.get_or_create(name=category_name)

        # Создание или получение веса продукта
        if product_weight_value:
            product_weight, created = ProductWeight.objects.get_or_create(value=int(product_weight_value))
        else:
            product_weight = None
        # Создание или получение продукта
        product, created = Product.objects.get_or_create(
            title=product_name,
            defaults={
                'content': product_name,
                'price': product_price,
                'category': category,
                'artikul': product_code,
                'public': True,
            }
        )

        # Добавление веса к продукту
        if product_weight:
            product.weight.add(product_weight)

        # Сохранение продукта
        product.save()


class Command(BaseCommand):
    help = 'Import products'

    def handle(self, *args, **options):
        for i in range(2):
            data = get_data(i)
            parse_and_save_products(data)
