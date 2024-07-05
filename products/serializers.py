from rest_framework import serializers
from .models import Product, FAQ, Banner, Brand, ProductWeight, ProductColor, Category, Catalog# ProductList,
from rest_framework.reverse import reverse
from . import validators
from api.serializers import UserPublicSerializer
from .models import Order, OrderItem




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
        fields = ['id', 'name', 'color']



class ProductWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductWeight
        fields = "__all__"



class ProductDetailSerializer(serializers.ModelSerializer):
    weight = ProductWeightSerializer(many=True, read_only=True)
    color = ProductColorSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = "__all__"



class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
    


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