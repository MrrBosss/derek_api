from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from rest_framework.reverse import reverse

from .models import Product, FAQ, Banner, Brand, ProductWeight, ProductColor, Category, Catalog, \
    Order, OrderItem, Team, BestSeller, ProductPrice, ProductShots
from . import validators
from api.serializers import UserPublicSerializer


class ProductInlineSerializer(serializers.Serializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='product-detail',
        lookup_field='pk',
        read_only=True,
    )
    title = serializers.CharField(read_only=True)


class ProductShotsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductShots
        fields = "__all__"


class ProductColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductColor
        fields = ['id', 'name']


class ProductWeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductWeight
        fields = ['id', 'mass']


class ProductListPriceSerializer(serializers.ModelSerializer):
    color = ProductColorSerializer(many=False, read_only=True)
    weight = ProductWeightSerializer(many=False, read_only=True)

    class Meta:
        model = ProductPrice
        fields = ['id', 'weight', 'color', 'amount', 'stock', 'guid', 'external_code', 'artikul',\
                   'description_ru', 'description_en']


class ProductDetailPriceSerializer(serializers.ModelSerializer):
    color = ProductColorSerializer(many=False, read_only=True)
    weight = ProductWeightSerializer(many=False, read_only=True)

    class Meta:
        model = ProductPrice
        fields = ['id', 'weight', 'color', 'amount', 'stock', 'guid', 'external_code', 'artikul',\
                   'description_ru', 'description_en']


class ProductDetailSerializer(serializers.ModelSerializer):
    product_shots = ProductShotsSerializer(many=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_price(self, obj) -> ProductDetailPriceSerializer(read_only=True, many=True):
        prices = obj.price.all().order_by('-stock', 'amount')
        return ProductDetailPriceSerializer(prices, many=True).data


class ProductSerializer(serializers.ModelSerializer):
    product_shots = ProductShotsSerializer(many=True)
    price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'title_ru', 'title_en', 'price','product_shots','category']

    def get_price(self, obj) -> ProductListPriceSerializer(read_only=True, many=True):
        prices = obj.price.all().select_related("weight", "color").order_by('-stock', 'amount')
        return ProductListPriceSerializer(prices, many=True).data


# class SubcategorySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Category
#         fields = ['id', 'name']


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'subcategories']

    def get_subcategories(self, obj):
        # Use prefetching to optimize queries
        subcategories = obj.subcategories.all()
        return CategorySerializer(subcategories, many=True).data



class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = "__all__"


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = "__all__"


class BrandSerializer(serializers.ModelSerializer):
    category = CategorySerializer(many=False,read_only=True)
    
    class Meta:
        model = Brand
        fields = ['category','brands']


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


class BestProductDetailSerializer(serializers.ModelSerializer):
    product_shots = ProductShotsSerializer(many=True)
    class Meta:
        model = Product
        fields = ['id', 'title_ru', 'title_en','product_shots']  # Include all desired fields from Product


class ProductPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPrice
        fields = ['description_ru', 'description_en','id']  # Include relevant fields from ProductPrice


class BestSellerSerializer(serializers.ModelSerializer):
    product = BestProductDetailSerializer(read_only=True)  # Serialize the Product properties
    product_price = ProductPriceSerializer(source='product.price', many=True, read_only=True)  # Assuming you want all related prices

    class Meta:
        model = BestSeller
        fields = ['id', 'product', 'product_price']  # Include Product and ProductPrice details
