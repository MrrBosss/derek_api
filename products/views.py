import traceback
from urllib.parse import urlparse

import requests
from requests.auth import HTTPBasicAuth
from dataclasses import dataclass

from django.conf import settings
from rest_framework import generics, mixins, viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView, Response

from .models import Product, FAQ, Banner, Brand, ProductWeight, ProductColor, Category, Order, Catalog, Team
from .serializers import ProductSerializer, FAQSerializer, BannerSerializer, BrandSerializer, ProductWeightSerializer
from .serializers import ProductColorSerializer, CategorySerializer, OrderSerializer, CatalogSerializer
from .serializers import TeamSerializer, ProductDetailSerializer
from .filters import ProductFilter
from .utils import create_product, update_product, delete_product


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


class CategoryView(viewsets.ModelViewSet):
    queryset = Category.objects.all()
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


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(public=True)
    serializer_class = ProductSerializer
    http_method_names = ['get']
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer


class Orderview(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    http_method_names = ['post']


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


class MoyskladProductAPIView(APIView):
    def post(self, request):
        request_data = request.data
        try:
            meta = request_data['events'][0]['meta']  # product
            event = meta['type']
            action = request_data['events'][0]['action']  # product
            if event == EventMapper.PRODUCT:
                if action == ActionMapper.CREATE:
                    url = meta['href']
                    response = requests.get(url,
                                            auth=HTTPBasicAuth(settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD))
                    if response.status_code == 200:
                        create_product(response.json())
                elif action == ActionMapper.UPDATE:
                    url = meta['href']
                    response = requests.get(url,
                                            auth=HTTPBasicAuth(settings.MOYSKLAD_LOGIN, settings.MOYSKLAD_PASSWORD))
                    if response.status_code == 200:
                        update_product(response.json())
                elif action == ActionMapper.DELETE:
                    url = meta['href']
                    parsed_url = urlparse(url)
                    product_id = parsed_url.path.split('/')[-1]
                    delete_product(product_id)
            elif event == EventMapper.COUNTERPARTY:
                ...
            elif event == EventMapper.RETAILDEMAND:
                ...

            data = {"success": True, "message": "Success"}
            return Response(data)
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
            meta = request_data['events'][0]['meta']  # product
            event = meta['type']
            action = request_data['events'][0]['action']  # product

            data = {"success": True, "message": "Success"}
            return Response(data)
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"Error str: {str(e)}\n"
                               f"Error repr: {repr(e)}\n"
                               f"Traceback: {traceback.format_exc()}"
                }, status=400)
