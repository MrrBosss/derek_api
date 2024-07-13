from urllib.parse import urlparse

import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
from django.core.files.base import ContentFile

from products.models import Category, ProductWeight, Product


# Функция для получения данных об изображениях
def get_images_data(url):
    response = requests.get(url, auth=HTTPBasicAuth(settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD))
    response.raise_for_status()  # Выбрасывает исключение, если запрос не успешен
    return response.json()


def save_first_image(product: Product, images_request_url):
    images_data = get_images_data(images_request_url)
    if images_data['rows']:
        first_image_meta = images_data['rows'][0]['meta']['downloadHref']
        image_response = requests.get(first_image_meta, auth=HTTPBasicAuth(
            settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD))
        image_response.raise_for_status()  # Выбрасывает исключение, если запрос не успешен

        image_content = ContentFile(image_response.content)

        # Генерация имени файла
        image_name = f"{product.id}_image.jpg"

        # Сохранение изображения в поле image продукта
        product.image.save(image_name, image_content, save=True)
        print("Image saved successfully!")
    else:
        print("No images found.")


def create_product(item):
    product_name = item['name']  # noqa
    product_code = item['code']
    product_guid = item['id']
    product_price = item['salePrices'][0]['value'] / 100.0  # цена в копейках
    product_weight_value = item['weight']
    images = item['images']['meta']

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
            'guid': product_guid,
            'content': product_name,
            'price': product_price,
            'category': category,
            'artikul': product_code,
            'public': True,
        }
    )
    if images['size'] > 0:
        save_first_image(product, images['href'])

    # Добавление веса к продукту
    if product_weight:
        product.weight.add(product_weight)

    # Сохранение продукта
    product.save()


def update_product(item):
    product_name = item['name']  # noqa
    product_code = item['code']
    product_guid = item['id']
    product_price = item['salePrices'][0]['value'] / 100.0  # цена в копейках
    product_weight_value = item['weight']
    images = item['images']['meta']

    # Создание или получение категории
    category_name = item.get('pathName', 'Default Category')
    category, created = Category.objects.get_or_create(name=category_name)

    # Создание или получение веса продукта
    if product_weight_value:
        product_weight, created = ProductWeight.objects.get_or_create(value=int(product_weight_value))
    else:
        product_weight = None
    # Создание или получение продукта
    product, created = Product.objects.update_or_create(
        guid=product_guid,
        defaults={
            'title': product_name,
            'content': product_name,
            'price': product_price,
            'category': category,
            'artikul': product_code,
            'public': True,
        }
    )
    if images['size'] > 0:
        save_first_image(product, images['href'])

    # Добавление веса к продукту
    if product_weight:
        product.weight.add(product_weight)

    # Сохранение продукта
    product.save()


def delete_product(product_id):
    product = Product.objects.filter(guid=product_id).first()
    if product:
        product.public = False
        product.save()


data3 = "https://api.moysklad.ru/api/remap/1.2/entity/product/b2e44cab-2a29-11ef-0a80-170d000a1962?expand=supplier",


def update_stock(data):
    product_url = data['meta']['href']
    stock = data['stock']
    parsed_url = urlparse(product_url)
    product_id = parsed_url.path.split('/')[-1]
    product_obj = Product.objects.filter(guid=product_id).first()
    if product_obj:
        product_obj.stock = int(stock)
        product_obj.save()
