import time
from urllib.parse import urlparse
import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth
from django.core.files.base import ContentFile
from products.models import Category, ProductWeight, Product, ProductColor, ProductPrice

# Function to get image data
def get_images_data(url):
    try:
        response = requests.get(url, auth=HTTPBasicAuth(settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD))
        response.raise_for_status()  # Raise an exception for unsuccessful requests
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching images data: {e}")
        return None

# Function to save images for a product
def save_images(product, images_request_url):
    images_data = get_images_data(images_request_url)
    if images_data and images_data.get('rows'):
        for i, image_meta in enumerate(images_data['rows']):
            download_href = image_meta['meta']['downloadHref']
            try:
                # Attempt to download the image
                image_response = requests.get(download_href, auth=HTTPBasicAuth(
                    settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD))
                image_response.raise_for_status()  # Raise an exception if the request is unsuccessfull

                # Prepare image content
                image_content = ContentFile(image_response.content)

                # Save the image to the ProductShots model
                product.product_shots.create(image=image_content)
                print(f"Image {i + 1} saved successfully to ProductShots for product {product.title}!")

                print("Image Content:", image_content)

            except requests.RequestException as e:
                print(f"Error downloading image {i + 1}: {e}")
                continue  # Skip to the next image if an error occurs
    else:
        print("No images found.")


# Function to extract name, color, and weight from product name
def extract_name_color_weight(product_name):
    parts = product_name.split(', ')
    name = parts[0] if len(parts) > 0 else ''
    color = parts[1] if len(parts) > 1 else None
    weight = parts[2] if len(parts) > 2 else None
    return name, color, weight

def create_or_update_product(item):
    product_name = item['name']  # e.g. "Product Name, Color, Weight"
    if len(product_name.split(",")) < 3:
        print(f"Product: {product_name} is invalid or incomplete.")
        return

    product_code = item['code']
    product_guid = item['id']
    external_code = item['externalCode']
    product_price = item['salePrices'][0]['value'] / 100.0  # Convert price from kopecks to rubles
    product_description = item.get('description', '')

    images = item['images']['meta'] if 'images' in item else None

    # Create or get hierarchical category
    category_name_path = item.get('pathName', 'Default Category')
    category = create_or_get_category_hierarchy(category_name_path)

    # Extract name, color, and weight
    name, color, weight_value = extract_name_color_weight(product_name)
    print(f"Extracted Name: {name}, Color: {color}, Weight: {weight_value}")

    # Create or get product
    product, _ = Product.objects.update_or_create(
        title=name.strip(),
        defaults={
            'category': category,
            'public': True,
        }
    )

    # Create or get product weight
    product_weight = None
    if weight_value:
        product_weight, _ = ProductWeight.objects.get_or_create(mass=weight_value.strip())

    # Create or get product color
    product_color = None
    if color:
        product_color, _ = ProductColor.objects.get_or_create(name=color.strip())

    # Create or update product price with description
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
                'description': product_description,
            }
        )

        # Associate the ProductPrice object with the product
        product.price.add(product_price_obj)

    # Save the first image if available
    if images and images.get('size', 0) > 0:
        time.sleep(2)
        save_images(product, images['href'])

    print(f"Product '{name}' created or updated successfully!")

def create_or_get_category_hierarchy(category_path):
    category_names = category_path.split('/')
    parent = None

    for name in category_names:
        name = name.strip()
        if not name:
            continue

        category, _ = Category.objects.get_or_create(name=name, parent=parent)
        parent = category  # Update parent for the next iteration

    return parent  # Return the last child category

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

    # Find the product price by guid
    product_price_obj = ProductPrice.objects.filter(guid=product_id).first()

    if product_price_obj:
        product_price_obj.stock = int(stock)
        product_price_obj.save()
        print(f"Stock for product {product_name} updated to {stock} for each ProductPrice.")
    else:
        print(f"No product price found for guid {product_id}.")


