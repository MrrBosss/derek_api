# Register your models here.
from django.contrib import admin
from .models import Product, ProductWeight, FAQ, Banner , Brand, Category, Order
from .models import  ProductColor, Catalog 



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["product", "quantity", "color", "weight", "total_price"]

    def total_price(self, obj):
        return obj.total_price

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'category']

admin.site.register(Catalog)

admin.site.register(ProductWeight)    

admin.site.register(ProductColor)

admin.site.register(Category)

admin.site.register(FAQ)

admin.site.register(Banner)

admin.site.register(Brand)

