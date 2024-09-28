from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from rest_framework.reverse import reverse

from .models import Product, FAQ, Banner, Brand, ProductWeight, ProductColor, Category, Catalog# ProductList,
from . import validators
from api.serializers import UserPublicSerializer
from .models import Order, OrderItem, Team, BestSeller


class ProductInlineSerializer(serializers.Serializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='product-detail',
        lookup_field='pk',
        read_only=True,
    )
    title = serializers.CharField(read_only=True)   


class ProductSerializer(serializers.ModelSerializer):
    owner = UserPublicSerializer(source="user",read_only=True)
    title = serializers.CharField(validators=[validators.validate_title_no_hello,
                                              validators.unique_product_title])
    
    body = serializers.CharField(source='content')
    class Meta:
        model = Product
        fields = [
            'owner',                         
            'pk',
            'title',
            'body',
            'price',
            'sale_price',
            'public',
            'path',
            'endpoint',
        ]
   
    def get_my_user_data(self, obj):
        return {
            "username": obj.user.username
        }

    def get_edit_url(self, obj):
        request = self.context.get('request')  #self.request
        if request is None: 
            return None
        return reverse("product-edit", kwargs={"pk": obj.pk}, request=request)


class ProductColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductColor
        fields = ['id', 'name']


class ProductWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductWeight
        fields = ['id', 'mass']


class ProductDetailSerializer(serializers.ModelSerializer):
    weight = ProductWeightSerializer(many=True, read_only=True)
    color = ProductColorSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    weights = ProductWeightSerializer(many=True, source='weight')

    class Meta:
        model = Product
        fields = ['id', 'title_ru','title_en', 'price','color','weights', 'artikul', 'category',\
                   'stock','description_ru','description_en']



class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'subcategories']
    

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = "__all__"


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = "__all__"


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = "__all__"
        

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'color', 'weight', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'order_date', 'name', 'phone_number', 'items']

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Items list cannot be empty")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order


class CatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Catalog
        fields = "__all__"


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = '__all__'


class BestProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['title', 'image','description']


class BestSellerSerializer(serializers.ModelSerializer):
    product_details = BestProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = BestSeller
        fields = ['id', 'product', 'product_details'] 