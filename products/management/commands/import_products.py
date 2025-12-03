import sys
import time
from django.core.management.base import BaseCommand, CommandError

from products.moysklad_client import moysklad_client, MoyskladClientError

from products.utils import create_or_update_product

API_URL = "https://api.moysklad.ru/api/remap/1.2/entity/product"


def get_data(page: int, limit: int):
    """
    Возвращает JSON с товарами.
    """
    params = {
        "limit": limit,
        "offset": page * limit,
    }
    return moysklad_client.get_json(API_URL, params=params)


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
        parser.add_argument(
            "--name",
            type=str,
            default=None,
            help="Начало названия товара для импорта (если указано, импортируются все товары, названия которых начинаются с этой строки).",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        if limit > 1000:
            raise CommandError("Moysklad API does not allow limit > 1000.")
        page = options["start_page"]
        index = options["start_index"]
        sleep_between = options["sleep"]
        target_name = options["name"]

        total_ok = 0
        total_err = 0
        found_target = False

        import_mode = "specific product" if target_name else "all products"
        self.stdout.write(self.style.NOTICE(
            f"Старт импорта ({import_mode}): page={page} index={index} limit={limit}"
        ))

        while True:
            # Загрузка страницы
            try:
                data = get_data(page, limit)
            except MoyskladClientError as e:
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
                item_name = item.get('name', '')

                # Если указано конкретное название, проверяем частичное совпадение (начинается с)
                if target_name and not item_name.startswith(target_name):
                    continue

                try:
                    ok = create_or_update_product(item)  # True/False
                    if ok:
                        total_ok += 1
                        if target_name:
                            found_target = True
                            self.stdout.write(self.style.SUCCESS(
                                f"Найден и импортирован товар: {item_name}"
                            ))
                    else:
                        total_err += 1
                except Exception as e:
                    total_err += 1
                    self.stderr.write(self.style.ERROR(
                        f"[page={page} idx={i}] Ошибка обработки товара: {e}"
                    ))

                # Прогресс + точная подсказка, как продолжить
                # (если оборвётся — возобновите со следующим индексом)
                resume_cmd = f"RESUME: python manage.py import_products --start-page {page} --start-index {i+1} --limit {limit}"
                if target_name:
                    resume_cmd += f" --name '{target_name}'"

                self.stdout.write(
                    f"[page={page} idx={i}] ok={total_ok} err={total_err} | {resume_cmd}"
                )

                if sleep_between > 0:
                    time.sleep(sleep_between)

            # Продолжаем поиск всех подходящих товаров

            # Следующая страница; внутри страницы начинаем с 0
            page += 1
            index = 0

            # Если вернулась неполная страница — вероятно, дальше данных нет
            if len(rows) < limit:
                break

        # Финальное сообщение
        if target_name:
            if found_target:
                self.stdout.write(self.style.SUCCESS(
                    f"Найдено и импортировано товаров серии '{target_name}': {total_ok}"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"Товары серии '{target_name}' не найдены среди {total_ok + total_err} просмотренных товаров."
                ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Импорт завершён. Итог: ok={total_ok}, err={total_err}"
            ))
