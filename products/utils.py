from products.models import Category, ProductWeight, Product


def create_product(item):
    product_name = item['name']  # noqa
    product_code = item['code']
    product_guid = item['id']
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
            'guid': product_guid,
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


def update_product(item):
    product_name = item['name']  # noqa
    product_code = item['code']
    product_guid = item['id']
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
