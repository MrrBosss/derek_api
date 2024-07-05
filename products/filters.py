import django_filters
from .models import Product, ProductColor, ProductWeight, Category



class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
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


    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'weight', 'color', 'category']

