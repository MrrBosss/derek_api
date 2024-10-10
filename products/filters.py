import django_filters
from django import forms
from django.db import models
from .models import Product, ProductColor, ProductWeight, Category, ProductPrice


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price__amount', lookup_expr='gte', label='Min Price')
    max_price = django_filters.NumberFilter(field_name='price__amount', lookup_expr='lte', label='Max Price')
    
    available = django_filters.BooleanFilter(method='filter_by_availability')

    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains', label='Title')

    color = django_filters.ModelMultipleChoiceFilter(
        field_name='price__color',  # Now filtering based on ProductPrice's color
        queryset=ProductColor.objects.all(),
        label='Color'
    )

    category = django_filters.ModelChoiceFilter(
        field_name='category',
        queryset=Category.objects.all(),
        label='Category'
    )

    weight = django_filters.ModelMultipleChoiceFilter(
        field_name='price__weight',  # Now filtering based on ProductPrice's weight
        queryset=ProductWeight.objects.all(),
        widget=forms.Select(attrs={'onchange': 'this.form.submit();'}),
        label='Select Weight'
    )

    def filter_by_availability(self, queryset, name, value):
        if value:
            # Filter products whose related ProductPrice has stock > 0
            return queryset.filter(price__stock__gt=0).distinct()
        else:
            return queryset.filter(price__stock__lte=0).distinct()

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'available', 'title', 'weight', 'color', 'category']


