from modeltranslation.translator import TranslationOptions
from modeltranslation.decorators import register
from .models import Product, FAQ, Banner
from . models import Category


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


@register(Banner)
class BannerTranslationOptions(TranslationOptions):
    fields = ('title','subtitle')


@register(FAQ)
class FAQTranslationOptions(TranslationOptions):
    fields = ('question', 'answer')


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)