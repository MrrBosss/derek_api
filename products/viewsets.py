from rest_framework import mixins,viewsets

from .models import Product 
from .serializers import ProductSerializer



class ProductGenericViewSet(
        mixins.ListModelMixin,
        mixins.RetrieveModelMixin,
        viewsets.GenericViewSet):
    """ 
    get = list = Queryset
    get = retrieve = Product instance detail view
    
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'pk' #default    



    
