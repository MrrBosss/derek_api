from django.core.management.base import BaseCommand
from products.utils import update_stock
from products.moysklad_client import moysklad_client, MoyskladClientError

API_URL = "https://api.moysklad.ru/api/remap/1.2/report/stock/all"


def get_data(page):
    params = {
        "limit": 1000,
        "offset": page * 1000,
    }
    return moysklad_client.get_json(API_URL, params=params)


def parse_and_save_products(json_response):
    for item in json_response['rows']:
        update_stock(item)


class Command(BaseCommand):
    help = 'Import product stocks'

    def handle(self, *args, **options):
        for i in range(2):
            try:
                data = get_data(i)
            except MoyskladClientError as exc:
                self.stderr.write(self.style.ERROR(f"Не удалось загрузить остатки (страница {i}): {exc}"))
                break
            parse_and_save_products(data)
