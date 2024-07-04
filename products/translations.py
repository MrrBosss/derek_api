from modeltranslation.translator import TranslationOptions
from modeltranslation.decorators import register
from .models import Product, FAQ, Banner , Brand
from . models import Category



@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('title', 'content')



@register(Banner)
class BannerTranslationOptions(TranslationOptions):
    fields = ('title','subtitle')



@register(FAQ)
class FAQTranslationOptions(TranslationOptions):
    fields = ('question', 'answer')



@register(Brand)
class BrandTranslationOptions(TranslationOptions):
    fields = ('name',)



@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)