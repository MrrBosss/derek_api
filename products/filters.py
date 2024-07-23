import django_filters
from .models import Product, ProductColor, ProductWeight, Category
from django_filters import rest_framework as filters


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    available = django_filters.BooleanFilter(method='filter_by_availability')

    weight = django_filters.ModelMultipleChoiceFilter(
        field_name='weight',
        queryset=ProductWeight.objects.all(),
        label='Weight'
    )

    color = django_filters.ModelMultipleChoiceFilter(
        field_name='color', 
        queryset=ProductColor.objects.all(),
        label='Color'
    )
    category = django_filters.ModelChoiceFilter(
        field_name='category',
        queryset=Category.objects.all(),
        label='Category'
    )
    
    def filter_by_availability(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)  # Available products
        else:
            return queryset.filter(stock__lte=0)  # Non-available products


    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'available', 'weight', 'color', 'category']

