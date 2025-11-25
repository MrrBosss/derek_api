import traceback
from urllib.parse import urlparse

import requests
from requests.auth import HTTPBasicAuth
from dataclasses import dataclass

from django.conf import settings
from django.db import models
from rest_framework import generics, mixins, viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView, Response
from rest_framework.generics import ListAPIView

from .models import Product, FAQ, Banner, Brand, ProductWeight, ProductColor, Category, Order, Catalog, Team, \
    BestSeller, ProductPrice,ProductShots
from .serializers import ProductSerializer, FAQSerializer, BannerSerializer, BrandSerializer, ProductWeightSerializer, \
    ProductColorSerializer, CategorySerializer, OrderSerializer, CatalogSerializer, TeamSerializer, \
    ProductDetailSerializer, BestSellerSerializer, ProductDetailPriceSerializer, ProductShotsSerializer
from .filters import ProductFilter
from .utils import create_or_update_product, delete_product


class ProductShotsViewSet(viewsets.ModelViewSet):
    queryset = ProductShots.objects.all()
    serializer_class = ProductShotsSerializer
    http_method_names = ['get']
    pagination_class = None


class ProductWeightViewSet(viewsets.ModelViewSet):
    queryset = ProductWeight.objects.all()
    serializer_class = ProductWeightSerializer
    http_method_names = ['get']
    pagination_class = None


class ProductColorViewset(viewsets.ModelViewSet):
    queryset = ProductColor.objects.all()
    serializer_class = ProductColorSerializer
    http_method_names = ['get']
    pagination_class = None


class CategoryListView(ListAPIView):
    queryset = Category.objects.filter(parent=None)  # Only top-level categories
    serializer_class = CategorySerializer
    http_method_names = ['get']
    pagination_class = None


class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    http_method_names = ['get']
    pagination_class = None


class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    http_method_names = ['get']
    pagination_class = None


class BrandViewSet(mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet
                   ):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    pagination_class = None


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 500
    page_size_query_param = 'page_size'
    max_page_size = 1000


class BannerView(generics.ListAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    pagination_class = LargeResultsSetPagination


class CatalogList(generics.ListAPIView):
    queryset = Catalog.objects.all()
    serializer_class = CatalogSerializer
    http_method_names = ['get']
    pagination_class = None


class ProductPriceViewSet(viewsets.ModelViewSet):
    queryset = ProductPrice.objects.all()
    serializer_class = ProductDetailPriceSerializer
    http_method_names = ['get']
    pagination_class = None


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(public=True).prefetch_related("price")
    serializer_class = ProductSerializer
    http_method_names = ['get']
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all().prefetch_related("price")
    serializer_class = ProductDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


class OrderView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    http_method_names = ['post']


class BestSellerListView(generics.ListAPIView):
    queryset = BestSeller.objects.all()
    serializer_class = BestSellerSerializer
    http_method_names = ['get']
    pagination_class = None


class TeamListView(generics.ListAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    http_method_names = ['get']
    pagination_class = None


json_example = {
    "auditContext": {
        "meta": {
            "type": "audit",
            "href": "https://api.moysklad.ru/api/remap/1.2/audit/23817f8d-3cfa-11ef-0a80-13aa00358154"
        },
        "uid": "admin@derektrade",
        "moment": "2024-07-08 10:17:30"
    },
    "events": [
        {
            "meta": {
                "type": "product",
                "href": "https://api.moysklad.ru/api/remap/1.2/entity/product/7c440000-3cf9-11ef-0a80-0bf80032dd58"
            },
            "action": "UPDATE",
            "accountId": "ef436254-ce21-11ee-0a80-16db00012ca5"
        }
    ]
}


@dataclass
class EventMapper:
    PRODUCT = "product"
    RETAILDEMAND = "retaildemand"
    COUNTERPARTY = "counterparty"


@dataclass
class ActionMapper:
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


def _extract_guid_from_href(url: str) -> str:
    parsed_url = urlparse(url)
    return parsed_url.path.rstrip('/').split('/')[-1]


class MoyskladProductAPIView(APIView):
    def post(self, request):
        request_data = request.data
        try:
            events = request_data.get("events")
            if not isinstance(events, list):
                raise ValueError("Payload must contain 'events' list.")

            processed = 0
            errors = []

            for event_payload in events:
                meta = (event_payload or {}).get("meta") or {}
                action = event_payload.get("action")
                event_type = meta.get("type")
                href = meta.get("href")

                if event_type != EventMapper.PRODUCT or not href or not action:
                    continue

                try:
                    if action in (ActionMapper.CREATE, ActionMapper.UPDATE):
                        response = requests.get(
                            href,
                            auth=HTTPBasicAuth(settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD),
                            timeout=60,
                        )
                        response.raise_for_status()
                        create_or_update_product(response.json())
                    elif action == ActionMapper.DELETE:
                        product_id = _extract_guid_from_href(href)
                        delete_product(product_id)
                    processed += 1
                except Exception as inner_exc:
                    errors.append(
                        f"Failed to process product event for href '{href}': {inner_exc}"
                    )

            response_payload = {
                "success": not errors,
                "message": "Completed with errors" if errors else "Success",
                "processed_events": processed,
                "errors": errors,
            }
            status_code = 200 if not errors else 207
            return Response(response_payload, status=status_code)
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"Error str: {str(e)}\n"
                               f"Error repr: {repr(e)}\n"
                               f"Traceback: {traceback.format_exc()}"
                }, status=400)


class MoyskladProductStockAPIView(APIView):
    def post(self, request):
        request_data = request.data
        try:
            stock_rows = []
            if isinstance(request_data, list):
                stock_rows = request_data
            elif isinstance(request_data, dict):
                stock_rows = request_data.get("rows", [])
            else:
                raise ValueError("Unsupported payload format for stocks.")

            updated = 0
            missing = []

            for stock in stock_rows:
                product_id = stock.get("assortmentId")
                if not product_id:
                    assortment_meta = (stock.get("assortment") or {}).get("meta") or {}
                    href = assortment_meta.get("href")
                    if href:
                        product_id = _extract_guid_from_href(href)

                if not product_id:
                    continue

                action = stock.get("action", ActionMapper.UPDATE)
                stock_count = stock.get("stock", 0)
                if action == ActionMapper.DELETE:
                    stock_count = 0

                try:
                    normalized_stock = int(float(stock_count))
                except (TypeError, ValueError):
                    missing.append(f"{product_id}: invalid stock value '{stock_count}'")
                    continue

                try:
                    product_price = ProductPrice.objects.filter(guid=product_id).first()
                    if not product_price:
                        missing.append(product_id)
                        continue

                    product_price.stock = normalized_stock
                    product_price.save(update_fields=["stock"])
                    updated += 1
                except Exception as inner_exc:
                    missing.append(f"{product_id}: {inner_exc}")

            data = {
                "success": True,
                "message": "Success" if not missing else "Completed with missing records",
                "updated": updated,
                "missing": missing,
            }
            status_code = 200 if not missing else 207
            return Response(data, status=status_code)
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"Error str: {str(e)}\n"
                               f"Error repr: {repr(e)}\n"
                               f"Traceback: {traceback.format_exc()}"
                }, status=400)
