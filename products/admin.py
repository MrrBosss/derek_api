# Register your models here.
from django.contrib import admin
from .models import Product, ProductWeight, FAQ, Banner , Brand, Category, Order
from .models import  ProductColor, Catalog, OrderItem, Team



class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_date', 'get_total_quantity', 'get_total_price']
    inlines = [OrderItemInline]

    def get_total_quantity(self, obj):
        return sum(item.quantity for item in obj.items.all())
    get_total_quantity.short_description = 'Total Quantity'

    def get_total_price(self, obj):
        return sum(item.subtotal for item in obj.items.all())
    get_total_price.short_description = 'Total Price'


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

admin.site.register(Team)