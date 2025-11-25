import csv
import io
import sys
from datetime import datetime

from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from products.moysklad_client import moysklad_client, MoyskladClientError

API_URL = "https://api.moysklad.ru/api/remap/1.2/entity/product"


def fetch_page(page: int, limit: int):
    params = {
        "limit": limit,
        "offset": page * limit,
    }
    return moysklad_client.get_json(API_URL, params=params)


def classify_issue(item):
    """
    Возвращает (is_problem, reason, parsed_fields_dict)
    Логика синхронизирована с create_or_update_product:
      - имя должно иметь формат 'Name, Color, Weight'
      - должны быть salePrices[0].value
      - должен быть id (guid)
      - нужны и color, и weight для цены
    """
    name = (item.get("name") or "").strip()
    path_name = item.get("pathName")
    code = item.get("code")
    external_code = item.get("externalCode")
    guid = item.get("id")

    # sale price
    sale_prices = item.get("salePrices") or []
    price_value = None
    if sale_prices:
        price_value = sale_prices[0].get("value")

    # parse name
    parts = name.split(",")
    parts = [p.strip() for p in parts if p is not None]

    parsed_name = parts[0] if len(parts) > 0 else ""
    parsed_color = parts[1] if len(parts) > 1 else None
    parsed_weight = parts[2] if len(parts) > 2 else None

    # выявление проблем
    if len(parts) < 3:
        return True, "Некорректный формат имени: ожидается 'Name, Color, Weight'", {
            "name_raw": name,
            "name": parsed_name,
            "color": parsed_color,
            "weight": parsed_weight,
            "guid": guid,
            "code": code,
            "external_code": external_code,
            "path_name": path_name,
            "price_value": price_value,
        }

    if not price_value:
        return True, "Отсутствует цена (salePrices[0].value)", {
            "name_raw": name,
            "name": parsed_name,
            "color": parsed_color,
            "weight": parsed_weight,
            "guid": guid,
            "code": code,
            "external_code": external_code,
            "path_name": path_name,
            "price_value": price_value,
        }

    if not guid:
        return True, "Отсутствует id (guid)", {
            "name_raw": name,
            "name": parsed_name,
            "color": parsed_color,
            "weight": parsed_weight,
            "guid": guid,
            "code": code,
            "external_code": external_code,
            "path_name": path_name,
            "price_value": price_value,
        }

    # Для создания цены в текущей логике нужны оба поля
    if not parsed_color or not parsed_weight:
        return True, "Нет color и/или weight в имени", {
            "name_raw": name,
            "name": parsed_name,
            "color": parsed_color,
            "weight": parsed_weight,
            "guid": guid,
            "code": code,
            "external_code": external_code,
            "path_name": path_name,
            "price_value": price_value,
        }

    # Всё ок — проблем нет
    return False, "", {
        "name_raw": name,
        "name": parsed_name,
        "color": parsed_color,
        "weight": parsed_weight,
        "guid": guid,
        "code": code,
        "external_code": external_code,
        "path_name": path_name,
        "price_value": price_value,
    }


class Command(BaseCommand):
    help = (
        "Собирает полный список проблемных товаров из МоЙСклад и сохраняет в CSV. "
        "Опционально отправляет CSV на e-mail."
    )

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=1000, help="Размер страницы (default: 1000)")
        parser.add_argument("--start-page", type=int, default=0, help="Стартовая страница (default: 0)")
        parser.add_argument(
            "--max-pages",
            type=int,
            default=None,
            help="Максимум страниц для обхода. По умолчанию идём до конца данных.",
        )
        parser.add_argument(
            "--outfile",
            type=str,
            default=None,
            help="Путь к CSV-файлу для сохранения. По умолчанию создаёт имя с датой во временной папке.",
        )
        parser.add_argument(
            "--email-to",
            type=str,
            default=None,
            help="Адрес e-mail получателя. Если указан — CSV ушлём на почту.",
        )
        parser.add_argument(
            "--email-subject",
            type=str,
            default="Проблемные товары (отчёт МоЙСклад)",
            help="Тема письма (если отправляем e-mail).",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        if limit > 1000:
            raise CommandError("Moysklad API does not allow limit > 1000.")
        page = options["start_page"]
        max_pages = options["max_pages"]
        email_to = options["email_to"]
        email_subject = options["email_subject"]

        # Имя файла по умолчанию
        if options["outfile"]:
            outfile = options["outfile"]
        else:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            outfile = f"/tmp/invalid_products_{stamp}.csv"

        self.stdout.write(self.style.NOTICE(
            f"Формируем отчёт: start_page={page}, limit={limit}, outfile={outfile}"
        ))

        problems = []
        pages_processed = 0
        total_seen = 0

        while True:
            if max_pages is not None and pages_processed >= max_pages:
                break

            try:
                data = fetch_page(page, limit)
            except MoyskladClientError as e:
                self.stderr.write(self.style.ERROR(f"Ошибка загрузки страницы {page}: {e}"))
                break

            rows = data.get("rows") or []
            if not rows:
                break

            for idx, item in enumerate(rows):
                total_seen += 1
                is_problem, reason, fields = classify_issue(item)
                if is_problem:
                    problems.append({
                        "page": page,
                        "index": idx,
                        "reason": reason,
                        **fields,
                    })

            # Если последняя страница неполная — дальше данных нет
            page += 1
            pages_processed += 1
            if len(rows) < limit:
                break

        # Пишем CSV
        if problems:
            fieldnames = [
                "page", "index", "reason",
                "name_raw", "name", "color", "weight",
                "guid", "code", "external_code",
                "path_name", "price_value",
            ]
            with open(outfile, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in problems:
                    writer.writerow(row)

            self.stdout.write(self.style.SUCCESS(
                f"Готово. Нашли проблемных товаров: {len(problems)} из {total_seen} просмотренных. "
                f"CSV сохранён: {outfile}"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Проблем не найдено среди {total_seen} товаров. CSV не создавался."
            ))

        # Отправка e-mail (опционально)
        if email_to and problems:
            try:
                # Формируем CSV в памяти для вложения
                mem = io.StringIO()
                fieldnames = [
                    "page", "index", "reason",
                    "name_raw", "name", "color", "weight",
                    "guid", "code", "external_code",
                    "path_name", "price_value",
                ]
                writer = csv.DictWriter(mem, fieldnames=fieldnames)
                writer.writeheader()
                for row in problems:
                    writer.writerow(row)
                mem.seek(0)

                msg = EmailMessage(
                    subject=email_subject,
                    body=(
                        "Добрый день!\n\n"
                        "Во вложении список товаров, требующих правок на стороне МоЙСклад.\n"
                        "Столбец 'reason' поясняет проблему по каждому товару.\n\n"
                        "С уважением,\nВаш автоматический отчёт"
                    ),
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                    to=[email_to],
                )
                msg.attach(filename="invalid_products.csv", content=mem.getvalue(), mimetype="text/csv")
                msg.send(fail_silently=False)

                self.stdout.write(self.style.SUCCESS(f"E-mail отправлен на {email_to}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Не удалось отправить e-mail: {e}"))
