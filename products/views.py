from rest_framework import generics,mixins, viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from .models import Product, FAQ, Banner, Brand, ProductWeight, ProductColor, Category, Order, Catalog, Team
from .serializers import ProductSerializer, FAQSerializer, BannerSerializer, BrandSerializer, ProductWeightSerializer
from .serializers import ProductColorSerializer,CategorySerializer, OrderSerializer, CatalogSerializer
from .serializers import TeamSerializer, ProductDetailSerializer
from .filters import ProductFilter




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
    queryset = Product.objects.all()
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