import requests
from requests.auth import HTTPBasicAuth

from django.core.management.base import BaseCommand
from django.conf import settings
from products.utils import create_product, update_stock

API_URL = "https://api.moysklad.ru/api/remap/1.2/report/stock/all"


def get_data(page):
    response = requests.get(
        url=API_URL + f"?limit=1000&offset={page * 1000}",
        auth=HTTPBasicAuth(settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD)
    )
    return response.json()


def parse_and_save_products(json_response):
    for item in json_response['rows']:
        update_stock(item)


class Command(BaseCommand):
    help = 'Import product stocks'

    def handle(self, *args, **options):
        for i in range(2):
            data = get_data(i)
            parse_and_save_products(data)
