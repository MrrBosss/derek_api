# from urllib.parse import urlparse

# import requests
# from django.conf import settings
# from requests.auth import HTTPBasicAuth
# from django.core.files.base import ContentFile

# from products.models import Category, ProductWeight, Product


# # Функция для получения данных об изображениях
# def get_images_data(url):
#     response = requests.get(url, auth=HTTPBasicAuth(settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD))
#     response.raise_for_status()  # Выбрасывает исключение, если запрос не успешен
#     return response.json()


# def save_first_image(product: Product, images_request_url):
#     images_data = get_images_data(images_request_url)
#     if images_data['rows']:
#         first_image_meta = images_data['rows'][0]['meta']['downloadHref']
#         image_response = requests.get(first_image_meta, auth=HTTPBasicAuth(
#             settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD))
#         image_response.raise_for_status()  # Выбрасывает исключение, если запрос не успешен

#         image_content = ContentFile(image_response.content)

#         # Генерация имени файла
#         image_name = f"{product.id}_image.jpg"

#         # Сохранение изображения в поле image продукта
#         product.image.save(image_name, image_content, save=True)
#         print("Image saved successfully!")
#     else:
#         print("No images found.")


# def create_product(item):
#     product_name = item['name']  # noqa
#     product_code = item['code']
#     product_guid = item['id']
#     product_price = item['salePrices'][0]['value'] / 100.0  # цена в копейках
#     product_weight_value = item['weight']
#     images = item['images']['meta']

#     # Создание или получение категории
#     category_name = item.get('pathName', 'Default Category')
#     category, created = Category.objects.get_or_create(name=category_name)

#     # Создание или получение веса продукта
#     if product_weight_value:
#         product_weight, created = ProductWeight.objects.get_or_create(value=int(product_weight_value))
#     else:
#         product_weight = None
#     # Создание или получение продукта
#     product, created = Product.objects.get_or_create(
#         title=product_name,
#         defaults={
#             'guid': product_guid,
#             'title': product_name,
#             'price': product_price,
#             'category': category,
#             'artikul': product_code,
#             'public': True,
#         }
#     )
#     if images['size'] > 0:
#         save_first_image(product, images['href'])

#     # Добавление веса к продукту
#     if product_weight:
#         product.weight.add(product_weight)

#     # Сохранение продукта
#     product.save()


# def update_product(item):
#     product_name = item['name']  # noqa
#     product_code = item['code']
#     product_guid = item['id']
#     product_price = item['salePrices'][0]['value'] / 100.0  # цена в копейках
#     product_weight_value = item['weight']
#     images = item['images']['meta']

#     # Создание или получение категории
#     category_name = item.get('pathName', 'Default Category')
#     category, created = Category.objects.get_or_create(name=category_name)

#     # Создание или получение веса продукта
#     if product_weight_value:
#         product_weight, created = ProductWeight.objects.get_or_create(value=int(product_weight_value))
#     else:
#         product_weight = None
#     # Создание или получение продукта
#     product, created = Product.objects.update_or_create(
#         guid=product_guid,
#         defaults={
#             'title': product_name,
#             # 'content': product_name,
#             'price': product_price,
#             'category': category,
#             'artikul': product_code,
#             'public': True,
#         }
#     )
#     if images['size'] > 0:
#         save_first_image(product, images['href'])

#     # Добавление веса к продукту
#     if product_weight:
#         product.weight.add(product_weight)

#     # Сохранение продукта
#     product.save()


# def delete_product(product_id):
#     product = Product.objects.filter(guid=product_id).first()
#     if product:
#         product.public = False
#         product.save()


# data3 = "https://api.moysklad.ru/api/remap/1.2/entity/product/b2e44cab-2a29-11ef-0a80-170d000a1962?expand=supplier",


# def update_stock(data):
#     product_url = data['meta']['href']
#     stock = data['stock']
#     parsed_url = urlparse(product_url)
#     product_id = parsed_url.path.split('/')[-1]
#     product_obj = Product.objects.filter(guid=product_id).first()
#     if product_obj:
#         product_obj.stock = int(stock)
#         product_obj.save()

import time
from urllib.parse import urlparse
import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
from django.core.files.base import ContentFile

from products.models import Category, ProductWeight, Product, ProductColor

# Function to get image data
def get_images_data(url):
    response = requests.get(url, auth=HTTPBasicAuth(settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD))
    response.raise_for_status()  # Raise an exception for unsuccessful requests
    return response.json()

# Function to save the first image for a product
def save_first_image(product: Product, images_request_url):
    ...
    # images_data = get_images_data(images_request_url)
    # if images_data['rows']:
    #     first_image_meta = images_data['rows'][0]['meta']['downloadHref']
    #     image_response = requests.get(first_image_meta, auth=HTTPBasicAuth(
    #         settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD))
    #     image_response.raise_for_status()  # Raise an exception if the request is unsuccessful

    #     image_content = ContentFile(image_response.content)

    #     # Generate a file name for the image
    #     image_name = f"{product.id}_image.jpg"

    #     # Save the image to the product
    #     product.image.save(image_name, image_content, save=True)
    #     print("Image saved successfully!")
    # else:
    #     print("No images found.")

# Function to extract name, color, and weight from product name
def extract_name_color_weight(product_name):
    parts = product_name.split(', ')
    name = parts[0] if len(parts) > 0 else ''
    color = parts[1] if len(parts) > 1 else None
    weight = parts[2] if len(parts) > 2 else None
    return name, color, weight

# Function to create a product
def create_or_update_product(item):
    product_name = item['name']  # e.g. "Product Name, Color, Weight"
    product_code = item['code']
    product_guid = item['id']
    product_price = item['salePrices'][0]['value'] / 100.0  # Convert price from kopecks to rubles
    images = item['images']['meta']
    # Create or get category
    category_name = item.get('pathName', 'Default Category')
    category, _created = Category.objects.get_or_create(name=category_name)

    # Extract name, color, and weight
    name, color, weight_value = extract_name_color_weight(product_name)
    # print(f"Extracted Name: {name}, Color: {color}, Weight: {weight_value}")  # Debug output

    # Create or get product weight
    
    # Create or get product
    product, created = Product.objects.update_or_create(
        title=name,
        defaults={
            'guid': product_guid,
            'price': product_price,
            'category': category,
            'artikul': product_code,
            'public': True,
            'description': item.get('description', ''),  # Default to empty string if no description

        }
    )

    Product.objects.filter(title=product_name).delete()

    if weight_value:
        product_weight, _created = ProductWeight.objects.get_or_create(mass=weight_value)
        product.weight.add(product_weight)
    if color:
        color_obj, _created = ProductColor.objects.get_or_create(name=color)
        product.color.add(color_obj)  # Set color for product

    # Save the first image if available
    if images['size'] > 0:
        time.sleep(2)
        save_first_image(product, images['href'])

    print(f"Product '{name}' created or updated successfully!")


# Function to delete a product
def delete_product(product_id):
    product = Product.objects.filter(guid=product_id).first()
    if product:
        product.public = False
        product.save()
        print(f"Product '{product.title}' marked as deleted.")

# Function to update stock for a product
def update_stock(data):
    product_url = data['meta']['href']
    stock = data['stock']
    parsed_url = urlparse(product_url)
    product_id = parsed_url.path.split('/')[-1]
    product_obj = Product.objects.filter(guid=product_id).first()
    if product_obj:
        product_obj.stock = int(stock)
        product_obj.save()
        print(f"Stock for product '{product_obj.title}' updated to {stock}.")
