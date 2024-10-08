import time
from urllib.parse import urlparse
import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
from django.core.files.base import ContentFile

from products.models import Category, ProductWeight, Product, ProductColor, ProductPrice
from urllib.parse import urlparse


# Function to get image data
def get_images_data(url):
    response = requests.get(url, auth=HTTPBasicAuth(settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD))
    response.raise_for_status()  # Raise an exception for unsuccessful requests
    return response.json()


# Function to save the first image for a product
def save_first_image(product: Product, images_request_url):
    images_data = get_images_data(images_request_url)
    if images_data['rows']:
        first_image_meta = images_data['rows'][0]['meta']['downloadHref']
        image_response = requests.get(first_image_meta, auth=HTTPBasicAuth(
            settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD))
        image_response.raise_for_status()  # Raise an exception if the request is unsuccessful

        image_content = ContentFile(image_response.content)

        # Generate a file name for the image
        image_name = f"{product.id}_image.jpg"

        # Save the image to the product
        product.image.save(image_name, image_content, save=True)
        print("Image saved successfully!")
    else:
        print("No images found.")


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
    if len(product_name.split(",")) < 3:
        print("Product name is None.")
        return
    product_code = item['code']
    product_guid = item['id']
    external_code = item['externalCode']
    product_price = item['salePrices'][0]['value'] / 100.0  # Convert price from kopecks to rubles
    images = item['images']['meta'] if 'images' in item else None
    # Create or get category
    category_name = item.get('pathName', 'Default Category')
    category, _created = Category.objects.get_or_create(name=category_name)

    # Extract name, color, and weight
    name, color, weight_value = extract_name_color_weight(product_name)
    print(f"Extracted Name: {name}, Color: {color}, Weight: {weight_value}")  # Debug output

    # Create or get product weight
    # Create or get product
    product, created = Product.objects.update_or_create(
        title=name,
        defaults={
            'category': category,
            'public': True,
            'description': item.get('description', ''),  # Default to empty string if no description

        }
    )
    product_weight = None
    if weight_value:
        product_weight, _ = ProductWeight.objects.get_or_create(mass=weight_value)

    product_color = None
    if color:
        product_color, _ = ProductColor.objects.get_or_create(name=color)

    Product.objects.filter(title=product_name).delete()

    if product_weight and product_color:
        product_price_obj, _ = ProductPrice.objects.update_or_create(
            guid=product_guid,
            defaults={
                'weight': product_weight,
                'color': product_color,
                'amount': product_price,
                'stock': 0,
                'artikul': product_code,
                'external_code': external_code,
            }
        )
        # Associate the ProductPrice object with the product
        product.price.add(product_price_obj)

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
    product_name = data['name']
    stock = data.get('stock', 0)  # Get stock value, default to 0 if not found
    parsed_url = urlparse(product_url)
    product_id = parsed_url.path.split('/')[-1]

    # Find the product by guid
    product_weight_obj = ProductPrice.objects.filter(guid=product_id).first()

    if product_weight_obj:
        product_weight_obj.stock = int(stock)
        product_weight_obj.save()

        print(f"Stock for product {product_name} updated to {stock} for each ProductPrice.")
