from rest_framework.routers import DefaultRouter
from django.urls import path
from products.views import FAQViewSet, BrandViewSet, BannerViewSet, ProductWeightViewSet, Orderview, CatalogList
from products.views import ProductDetailView, ProductColorViewset, ProductListView, CategoryView  



router = DefaultRouter()
router.register('products-color', ProductColorViewset, basename='products-color')
router.register('products-weight', ProductWeightViewSet, basename='products-weight')
router.register('categories', CategoryView, basename='categories')
router.register('faqs', FAQViewSet, basename='faqs')
router.register('banners', BannerViewSet, basename='banners')
router.register('brands', BrandViewSet, basename='brands')
urlpatterns = router.urls
urlpatterns += [
    path('catalog-list/', CatalogList.as_view(), name='catalog-list'),
    path('orders/', Orderview.as_view(), name='orders'),
    path('products-list/', ProductListView.as_view(), name='products-list'),
    path("products-detail/<int:pk>/", ProductDetailView.as_view(), name='product-detail'),
]
