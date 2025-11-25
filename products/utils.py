import time
from urllib.parse import urlparse
from django.core.files.base import ContentFile
from products.models import Category, ProductWeight, Product, ProductColor, ProductPrice
from .moysklad_client import moysklad_client, MoyskladClientError

def get_images_data(url):
    try:
        return moysklad_client.get_json(url)
    except MoyskladClientError as e:
        print(f"Error fetching images data: {e}")
        return None

def save_images(product, images_request_url):
    images_data = get_images_data(images_request_url)
    if images_data and images_data.get('rows'):
        for i, image_meta in enumerate(images_data['rows']):
            download_href = image_meta['meta'].get('downloadHref')
            if not download_href:
                print(f"Image meta without downloadHref at index {i}")
                continue
            try:
                image_bytes = moysklad_client.get_binary(download_href, timeout=120)
                image_content = ContentFile(image_bytes)
                # Желательно дать имя файлу (если ваша модель ожидает):
                # product.product_shots.create(image=ImageFile(image_content, name=f"{product.pk}_{i}.jpg"))
                product.product_shots.create(image=image_content)
                print(f"Image {i + 1} saved successfully for product {product.title}!")
            except MoyskladClientError as e:
                print(f"Error downloading image {i + 1}: {e}")
                continue
    else:
        print("No images found.")

def extract_name_color_weight(product_name):
    parts = product_name.split(', ')
    name = parts[0] if len(parts) > 0 else ''
    color = parts[1] if len(parts) > 1 else None
    weight = parts[2] if len(parts) > 2 else None
    return name, color, weight

def create_or_update_product(item) -> bool:
    """
    Возвращает True, если товар/цена успешно обработаны (создана/обновлена ProductPrice),
    False — если некорректные данные/пропуски и т.п.
    Исключения наружу не бросаем — команда их перехватит и посчитает как ошибки.
    """
    try:
        product_name = item.get('name') or ''
        if len(product_name.split(",")) < 3:
            print(f"Product: {product_name} is invalid or incomplete.")
            return False

        product_code = item.get('code')
        product_guid = item.get('id')
        external_code = item.get('externalCode')
        sale_prices = item.get('salePrices') or []
        if not sale_prices or not sale_prices[0].get('value'):
            print(f"Product: {product_name} has no salePrices.")
            return False

        product_price = sale_prices[0]['value'] / 100.0
        product_description = item.get('description', '')

        images = item.get('images', {}).get('meta')

        # Category
        category_name_path = item.get('pathName', 'Default Category')
        category = create_or_get_category_hierarchy(category_name_path)

        # Parse name/color/weight
        name, color, weight_value = extract_name_color_weight(product_name)
        # print(f"Extracted Name: {name}, Color: {color}, Weight: {weight_value}")

        # Product
        product, _ = Product.objects.update_or_create(
            title=name.strip(),
            defaults={
                'category': category,
                'public': True,
            }
        )

        # Weight
        product_weight = None
        if weight_value:
            product_weight, _ = ProductWeight.objects.get_or_create(mass=weight_value.strip())

        # Color
        product_color = None
        if color:
            product_color, _ = ProductColor.objects.get_or_create(name=color.strip())

        # Price
        created_or_updated_price = False
        if product_weight and product_color and product_guid:
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
            product.price.add(product_price_obj)
            created_or_updated_price = True
        else:
            print(f"Skip price: guid/weight/color missing for product '{name}'")

        # Images (не критично — ошибки не должны валить импорт)
        if images and images.get('size', 0) > 0:
            time.sleep(2)
            save_images(product, images['href'])

        print(f"Product '{name}' processed.")
        return bool(created_or_updated_price)

    except Exception as e:
        # Не пробрасываем — пусть команда решит, как считать
        print(f"Unexpected error in create_or_update_product: {e}")
        return False

def create_or_get_category_hierarchy(category_path):
    category_names = category_path.split('/')
    parent = None
    for name in category_names:
        name = name.strip()
        if not name:
            continue
        category, _ = Category.objects.get_or_create(name=name, parent=parent)
        parent = category
    return parent

def delete_product(product_id):
    """
    Deletes single product variation (ProductPrice) and hides parent Product when
    it no longer has any attached prices.
    """
    from products.models import ProductPrice  # локальный импорт на всякий

    product_price = ProductPrice.objects.filter(guid=product_id).first()
    if not product_price:
        print(f"No product price found for guid {product_id}. Nothing to delete.")
        return

    related_products = list(product_price.product_set.all())
    product_price.delete()

    for product in related_products:
        if not product.price.exists() and product.public:
            product.public = False
            product.save(update_fields=["public"])
            print(f"Product '{product.title}' marked as deleted (no active prices).")

def update_stock(data):
    from products.models import ProductPrice  # локальный импорт на всякий
    product_url = data['meta']['href']
    product_name = data['name']
    stock = data.get('stock', 0)
    parsed_url = urlparse(product_url)
    product_id = parsed_url.path.split('/')[-1]
    product_price_obj = ProductPrice.objects.filter(guid=product_id).first()
    if product_price_obj:
        product_price_obj.stock = int(stock)
        product_price_obj.save()
        print(f"Stock for product {product_name} updated to {stock}.")
    else:
        print(f"No product price found for guid {product_id}.")

