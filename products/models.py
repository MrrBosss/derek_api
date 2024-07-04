import random
from django.conf import settings 
from django.db import models
from django.db.models import Q



User = settings.AUTH_USER_MODEL #auth.user


TAGS_MODELS_VALUES = ['electronics', 'cars','boats','movies','cameras']


class ProductQuerySet(models.QuerySet):
    def is_public(self):
        return self.filter(public=True)
    
    def search(self, query, user=None):
        lookup = Q(title__icontains=query) | Q(content__icontains=query)
        qs = self.is_public().filter(lookup)
        if user is not None:
            qs2 = self.filter(user=user).filter(lookup)
            qs = (qs | qs2).distinct()
        return qs
    


class ProductManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return ProductQuerySet(self.model, using=self._db)
    
    def search(self, query, user=None):
        return self.get_queryset().search(query, user=user)



class ProductWeight(models.Model):
    value = models.IntegerField()

    def __str__(self):
        return str(self.value)



class ProductColor(models.Model):
    name = models.CharField(max_length=150)
    color = models.CharField(max_length=60)



class FAQ(models.Model):
    question = models.CharField(max_length=500, null=True)
    answer = models.CharField(max_length=500, null=True)

    def __str__(self):
        return str(self.question)



class Banner(models.Model):
    user = models.ForeignKey(User, default=1, null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=500, null=True)
    subtitle = models.TextField(blank=True, null=True)
    link = models.CharField(max_length=250, null=True)



class Brand(models.Model):
    brands = models.ImageField(upload_to="products", null=True)
    name = models.CharField(max_length=500, null=True)

    def __str__(self):
        return str(self.brands)
    


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name



class Catalog(models.Model):
    catalog = models.FileField(upload_to='products')



class Product(models.Model):
    user = models.ForeignKey(User, default=1, null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=120, null=True)
    content = models.TextField(blank=True, null=True)
    price = models.FloatField(default=10.000) 
    public = models.BooleanField(default=True)
    image = models.ImageField(upload_to="products", null=True, blank=True)
    objects = ProductManager()
    weight = models.ManyToManyField(ProductWeight)
    color = models.ManyToManyField(ProductColor)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null= True)

    def get_absolute_url(self):
        return f"/api/products/{self.pk}/"
    
    def __str__(self) -> str:
        return str(self.title)
    
    @property
    def endpoint(self):
        return self.get_absolute_url()
    
    @property
    def path(self):
        return f"/products/{self.pk}/"
  
    @property
    def body(self):
        return self.content
   
    def is_public(self): # returns bool
        return self.public #True or False   
    
    def get_tags_list(self):
        return [random.choice(TAGS_MODELS_VALUES)]

    @property
    def sale_price(self):
        return "%.2f" %(float(self.price) * 0.8)

    def get_discount(self):
        return '123'

    

class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    color = models.CharField(max_length=20, null=True)
    weight = models.IntegerField(null=True)
    quantity = models.IntegerField(default=0)

    @property
    def total_price(self):
        # Calculate product's price sum
        if self.product:
            return self.quantity * self.product.price
        return 0
