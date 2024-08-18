import django_filters
from django import forms
from django.db import models
from .models import Product, ProductColor, ProductWeight, Category



class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(method='filter_by_weight', lookup_expr='gte')
    max_price = django_filters.NumberFilter(method='filter_by_weight', lookup_expr='lte')
    
    available = django_filters.BooleanFilter(method='filter_by_availability')

    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')

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

    weight = django_filters.ModelChoiceFilter(
        queryset=ProductWeight.objects.all(),
        method='filter_by_weight',
        widget=forms.Select(attrs={'onchange': 'this.form.submit();'}),
        label='Select Weight'
    )

    def filter_by_weight(self, queryset, name, value):
        if value:
            # Assuming `ProductWeight` model has a `price` field for specific weight prices
            return queryset.annotate(price_adjusted=models.F('price') * value.price)
        return queryset


    def filter_by_availability(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)  # Available products
        else:
            return queryset.filter(stock__lte=0)  # Non-available products

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'available','title', 'weight', 'color', 'category']

