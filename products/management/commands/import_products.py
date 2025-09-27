import sys
import time
import requests
from requests.auth import HTTPBasicAuth

from django.core.management.base import BaseCommand
from django.conf import settings

from products.utils import create_or_update_product

API_URL = "https://api.moysklad.ru/api/remap/1.2/entity/product"


def get_data(page: int, limit: int):
    """
    Возвращает JSON с товарами.
    """
    resp = requests.get(
        url=f"{API_URL}?limit={limit}&offset={page * limit}",
        auth=HTTPBasicAuth(settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD),
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


class Command(BaseCommand):
    help = "Import products with resume support via --start-page and --start-index"

    def add_arguments(self, parser):
        parser.add_argument(
            "--start-page",
            type=int,
            default=0,
            help="С какой страницы (offset/limit) начать. По умолчанию 0.",
        )
        parser.add_argument(
            "--start-index",
            type=int,
            default=0,
            help="С какого индекса внутри страницы начать (0..limit-1). По умолчанию 0.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=1000,
            help="Сколько записей запрашивать за страницу. По умолчанию 1000.",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=0.0,
            help="Пауза (сек) между элементами для снижения нагрузки/ограничений API.",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        page = options["start_page"]
        index = options["start_index"]
        sleep_between = options["sleep"]

        total_ok = 0
        total_err = 0

        self.stdout.write(self.style.NOTICE(
            f"Старт импорта: page={page} index={index} limit={limit}"
        ))

        while True:
            # Загрузка страницы
            try:
                data = get_data(page, limit)
            except Exception as e:
                self.stderr.write(self.style.ERROR(
                    f"Ошибка загрузки данных со страницы {page}: {e}"
                ))
                self.stderr.write("Подсказка для продолжения:\n"
                                  f"python manage.py import_products --start-page {page} --start-index {index} --limit {limit}")
                # Прерываем — чтобы можно было продолжить с тех же параметров
                sys.exit(2)

            rows = data.get("rows", []) or []
            if not rows:
                # Данные закончились
                break

            # Перебор элементов внутри страницы (с учётом возможного резюма)
            for i in range(index, len(rows)):
                item = rows[i]
                try:
                    ok = create_or_update_product(item)  # True/False
                    if ok:
                        total_ok += 1
                    else:
                        total_err += 1
                except Exception as e:
                    total_err += 1
                    self.stderr.write(self.style.ERROR(
                        f"[page={page} idx={i}] Ошибка обработки товара: {e}"
                    ))

                # Прогресс + точная подсказка, как продолжить
                # (если оборвётся — возобновите со следующим индексом)
                self.stdout.write(
                    f"[page={page} idx={i}] ok={total_ok} err={total_err} | "
                    f"RESUME: python manage.py import_products --start-page {page} --start-index {i+1} --limit {limit}"
                )

                if sleep_between > 0:
                    time.sleep(sleep_between)

            # Следующая страница; внутри страницы начинаем с 0
            page += 1
            index = 0

            # Если вернулась неполная страница — вероятно, дальше данных нет
            if len(rows) < limit:
                break

        self.stdout.write(self.style.SUCCESS(
            f"Импорт завершён. Итог: ok={total_ok}, err={total_err}"
        ))
